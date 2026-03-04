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
    Uses language detection and appropriate models
    """
    
    def __init__(self):
        self.models_loaded = False
        self.english_model = None
        self.hindi_model = None
        self.detector = None
        
    def _load_models(self):
        """Lazy load ML models"""
        if self.models_loaded:
            return
            
        try:
            # Try to import transformers (optional dependency for now)
            from transformers import pipeline
            import langdetect
            
            logger.info("Loading sentiment analysis models...")
            
            # English sentiment model
            self.english_model = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # For multilingual (Hindi included)
            # Using a simpler approach for now
            self.hindi_model = self.english_model  # Fallback
            
            self.detector = langdetect
            self.models_loaded = True
            
            logger.info("Sentiment models loaded successfully")
            
        except ImportError:
            logger.warning("Transformers not installed. Using simple sentiment analysis.")
            self.models_loaded = False
        except Exception as e:
            logger.error(f"Error loading sentiment models: {e}")
            self.models_loaded = False
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        Returns: ISO language code ('en', 'hi', etc.)
        """
        if not text or len(text.strip()) < 10:
            return "en"  # Default to English for short text
            
        try:
            if self.detector:
                return self.detector.detect(text)
            else:
                # Simple heuristic: check for Devanagari characters
                if any('\u0900' <= c <= '\u097F' for c in text):
                    return "hi"
                return "en"
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"
    
    def analyze_sentiment(self, text: str, language: Optional[str] = None) -> Dict[str, any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            language: Optional language code. If None, will be detected
            
        Returns:
            {
                'label': 'positive'|'negative'|'neutral',
                'score': float (-1.0 to 1.0),
                'language': str,
                'confidence': float (0.0 to 1.0)
            }
        """
        if not text or not text.strip():
            return {
                'label': 'neutral',
                'score': 0.0,
                'language': 'unknown',
                'confidence': 0.0
            }
        
        # Detect language if not provided
        if not language:
            language = self.detect_language(text)
        
        # Try to use ML models if available
        self._load_models()
        
        if self.models_loaded and self.english_model:
            return self._ml_sentiment(text, language)
        else:
            return self._simple_sentiment(text, language)
    
    def _ml_sentiment(self, text: str, language: str) -> Dict[str, any]:
        """Use ML models for sentiment analysis"""
        try:
            # Use appropriate model based on language
            model = self.english_model  # For now, use English model for all
            
            # Get prediction
            result = model(text[:512])[0]  # Truncate to model limit
            
            label = result['label'].lower()
            confidence = result['score']
            
            # Normalize label
            if 'pos' in label:
                label = 'positive'
                score = confidence
            elif 'neg' in label:
                label = 'negative'
                score = -confidence
            else:
                label = 'neutral'
                score = 0.0
            
            return {
                'label': label,
                'score': round(score, 4),
                'language': language,
                'confidence': round(confidence, 4)
            }
            
        except Exception as e:
            logger.error(f"ML sentiment analysis failed: {e}")
            return self._simple_sentiment(text, language)
    
    def _simple_sentiment(self, text: str, language: str) -> Dict[str, any]:
        """
        Simple rule-based sentiment analysis as fallback
        Uses keyword matching
        """
        text_lower = text.lower()
        
        # Positive keywords (English + Hindi transliterated)
        positive_words = {
            'good', 'great', 'excellent', 'best', 'love', 'amazing', 
            'wonderful', 'fantastic', 'support', 'victory', 'win',
            'achha', 'badhia', 'shandar', 'jeet', 'vijay'
        }
        
        # Negative keywords (English + Hindi transliterated)
        negative_words = {
            'bad', 'worst', 'hate', 'terrible', 'awful', 'poor',
            'corrupt', 'failure', 'lose', 'defeat', 'against',
            'bura', 'ganda', 'harana', 'bhrasht'
        }
        
        # Count occurrences
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate score
        total = pos_count + neg_count
        if total == 0:
            return {
                'label': 'neutral',
                'score': 0.0,
                'language': language,
                'confidence': 0.5
            }
        
        score = (pos_count - neg_count) / total
        
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        confidence = min(abs(score), 1.0)
        
        return {
            'label': label,
            'score': round(score, 4),
            'language': language,
            'confidence': round(confidence, 4)
        }
    
    def batch_analyze(self, texts: list, languages: Optional[list] = None) -> list:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of texts to analyze
            languages: Optional list of language codes
            
        Returns:
            List of sentiment results
        """
        results = []
        for i, text in enumerate(texts):
            lang = languages[i] if languages and i < len(languages) else None
            result = self.analyze_sentiment(text, lang)
            results.append(result)
        
        return results


# Global instance
sentiment_analyzer = SentimentAnalyzer()
