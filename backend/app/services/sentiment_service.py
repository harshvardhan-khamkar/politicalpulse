"""
Sentiment Analysis Service
Multilingual sentiment analysis for social media posts
Supports English and Hindi text
"""
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Sentiment analysis service for political social media content
    Uses language detection, translation (for Hindi), and VADER sentiment.
    """
    
    def __init__(self):
        self.analyzer = None
        self.translator = None
        self.initialized = False
        
    def _init_models(self):
        """Lazy load VADER and translation models"""
        if self.initialized:
            return
            
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            from deep_translator import GoogleTranslator
            
            self.analyzer = SentimentIntensityAnalyzer()
            self.translator = GoogleTranslator(source='auto', target='en')
            self.initialized = True
            logger.info("VADER Sentiment and Translator initialized successfully")
        except ImportError:
            logger.error("Required NLP packages missing. Install: pip install vaderSentiment deep-translator")
            self.initialized = False
    
    def detect_language(self, text: str) -> str:
        """
        Simple heuristic language detection.
        Returns: 'hi' if Devanagari detected, else 'en'
        """
        if not text:
            return "en"
        # Check for Devanagari characters
        if any('\u0900' <= c <= '\u097F' for c in text):
            return "hi"
        return "en"
    
    def analyze_sentiment(self, text: str, language: Optional[str] = None) -> Dict[str, any]:
        """
        Analyze sentiment using VADER.
        Translates Hindi text to English first for highly accurate VADER scoring.
        """
        if not text or not text.strip():
            return {
                'label': 'neutral',
                'score': 0.0,
                'language': 'unknown',
                'confidence': 1.0
            }
        
        self._init_models()
        
        if not language:
            language = self.detect_language(text)
            
        analysis_text = text
        
        # Translate to English if text contains Hindi
        if self.initialized and language == 'hi':
            try:
                analysis_text = self.translator.translate(text[:4500]) # Limit to 4500 chars for API
            except Exception as e:
                logger.warning(f"Translation failed, falling back to original: {e}")
                
        # Get VADER scores
        if self.initialized and self.analyzer:
            scores = self.analyzer.polarity_scores(analysis_text)
            compound = scores['compound']
        else:
            # Absolute worst-case fallback (if packages fail to load)
            compound = 0.0
            
        # Classify based on compound score
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
            
        return {
            'label': label,
            'score': round(compound, 4),
            'language': language,
            'confidence': round(abs(compound), 4) if label != 'neutral' else 0.5
        }
    
    def batch_analyze(self, texts: list, languages: Optional[list] = None) -> list:
        results = []
        for i, text in enumerate(texts):
            lang = languages[i] if languages and i < len(languages) else None
            results.append(self.analyze_sentiment(text, lang))
        return results

# Global instance
sentiment_analyzer = SentimentAnalyzer()
