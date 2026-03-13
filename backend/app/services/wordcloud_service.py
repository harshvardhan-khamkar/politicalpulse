"""
Word Cloud Service
Generate word clouds from social media data
Supports multilingual text with appropriate fonts
"""
import io
import os
import re
from typing import Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WordCloudService:
    """Generate word clouds from social media posts"""
    
    def __init__(self):
        self.stopwords = None
        self.lemmatizer = None
        self.initialized = False
        
    def _init_nltk(self):
        """Initialize NLTK components explicitly"""
        if self.initialized:
            return
            
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer
            
            # Explicitly set download dir to ensure we don't have permission errors
            import os
            nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data')
            os.makedirs(nltk_data_dir, exist_ok=True)
            if nltk_data_dir not in nltk.data.path:
                nltk.data.path.append(nltk_data_dir)

            # Download required NLTK data securely
            for pkg in ['stopwords', 'wordnet', 'punkt', 'averaged_perceptron_tagger']:
                try:
                    # Check if already downloaded to avoid redownloading
                    if pkg == 'stopwords': nltk.data.find('corpora/stopwords')
                    elif pkg == 'wordnet': nltk.data.find('corpora/wordnet')
                    elif pkg == 'punkt': nltk.data.find('tokenizers/punkt')
                    elif pkg == 'averaged_perceptron_tagger': nltk.data.find('taggers/averaged_perceptron_tagger')
                except LookupError:
                    logger.info(f"Downloading NLTK package: {pkg}")
                    nltk.download(pkg, download_dir=nltk_data_dir, quiet=True)
            
            self.stopwords = set(stopwords.words('english'))
            
            # Expanded custom political noise words (English)
            custom_en = {
                'today', 'every', 'first', 'last', 'work', 'state', 'year', 'month', 'day', 'shri', 'ji',
                'one', 'two', 'three', 'many', 'done', 'also', 'must', 'make', 'get', 'take', 'like', 'time',
                'people', 'country', 'national', 'prime', 'minister', 'chief', 'ji', 'thank', 'thanks',
                'happy', 'best', 'wish', 'wishes', 'meeting', 'meet', 'great', 'good', 'new', 'all', 'any',
                'bjp', 'inc', 'aap', 'congress', 'party', 'rt', 'http', 'https', 'amp', 'via', 'latest',
                'hon', 'honble', 'sri', 'shree', 'delhi', 'tamil', 'nadu', 'bengal', 'west', 'karnataka',
                'madurai', 'chennai', 'puducherry', 'government', 'india', 'indian'
            }
            self.stopwords.update(custom_en)

            # Basic Hindi stopwords
            custom_hi = {
                'आज', 'कल', 'अब', 'जब', 'तब', 'है', 'हो', 'को', 'का', 'की', 'के', 'में', 'पर', 'से', 'भी',
                'ने', 'ही', 'लिए', 'गया', 'गई', 'गए', 'कर', 'रहा', 'रही', 'रहे', 'था', 'थी', 'थे', 'जो',
                'कि', 'यह', 'वह', 'इस', 'उस', 'वे', 'ये', 'जी', 'श्री', 'सब', 'सबसे', 'बहुत', 'तरफ', 'कहा',
                'गया', 'किया', 'जाना', 'होने', 'होता', 'होती', 'होते', 'साथ', 'अपने', 'अपनी', 'अपने',
                'माननीय', 'जी', 'श्री', 'श्रीमती', 'तथा', 'एवं', 'द्वारा', 'हो चुका'
            }
            self.stopwords.update(custom_hi)
            
            self.lemmatizer = WordNetLemmatizer()
            self.initialized = True
            logger.info("NLTK initialized successfully")
            
        except ImportError:
            logger.warning("NLTK not available. Basic word cloud generation only.")
            self.initialized = False
        except Exception as e:
            logger.error(f"Error initializing NLTK: {e}")
            self.initialized = False

    def clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        self._init_nltk()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove @mentions
        text = re.sub(r'@\w+', '', text)
        
        # Remove punctuation and numbers
        # Preserve: Alphanumeric, Space, Hashtag, Devanagari range, and Zero-Width-Joiners (\u200c, \u200d)
        text = re.sub(r'[^\w\s#\u0900-\u097F\u200C\u200D]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        # Lowercase (Safe for Devanagari)
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Lemmatize and remove stopwords
        if self.initialized:
            def is_hindi(w):
                return any('\u0900' <= c <= '\u097F' for c in w)
                
            clean_words = []
            for word in text.split():
                clean_w = word.replace('#', '')
                # Skip if empty, too short, or in stopwords
                if not clean_w or clean_w in self.stopwords:
                    continue
                
                # Minimum length check (2 for English, 1 for Hindi but usually we want at least 2 chars for cloud)
                if len(clean_w) < 2:
                    continue

                if is_hindi(word):
                    # Preserve Hindi words as is (no lemmatization)
                    clean_words.append(word)
                elif self.lemmatizer:
                    # Lemmatize English words
                    clean_words.append(self.lemmatizer.lemmatize(word))
                else:
                    clean_words.append(word)
                    
            text = ' '.join(clean_words)
        
        return text

    def generate_wordcloud(
        self,
        db: Session,
        party: Optional[str] = None,
        leader_name: Optional[str] = None,
        platform: Optional[str] = None,
        source_type: Optional[str] = None,
        days: int = 30,
        language: str = 'en'
    ) -> bytes:
        from app.models.social_media import TwitterPost, RedditPost
        
        try:
            from wordcloud import WordCloud
            from PIL import Image
        except ImportError:
            logger.error("wordcloud or Pillow not installed")
            raise ImportError("Install with: pip install wordcloud pillow")
        
        # Query posts
        cutoff_date = datetime.now() - timedelta(days=days)

        def _fetch_platform_posts(model):
            query = db.query(model).filter(model.posted_at >= cutoff_date)
            if party:
                query = query.filter(model.party == party)
            if leader_name:
                query = query.filter(model.leader_name == leader_name)
            if source_type:
                query = query.filter(model.source_type == source_type)
            if language != 'all':
                query = query.filter(model.language == language)
            return query.all()

        if platform == "twitter":
            posts = _fetch_platform_posts(TwitterPost)
        elif platform == "reddit":
            posts = _fetch_platform_posts(RedditPost)
        else:
            posts = _fetch_platform_posts(TwitterPost) + _fetch_platform_posts(RedditPost)
        
        if not posts:
            logger.warning("No posts found for word cloud generation")
            img = Image.new('RGB', (800, 400), color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return buf.getvalue()
        
        combined_text = ' '.join([post.content for post in posts if post.content])
        cleaned_text = self.clean_text(combined_text)
        
        if not cleaned_text.strip():
            logger.warning("No text remaining after cleaning")
            img = Image.new('RGB', (800, 400), color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return buf.getvalue()
        
        # Select font based on language
        font_path = None
        if language == 'hi' or language == 'all':
            # For Hindi, try to use Windows Native Devanagari fonts so text doesn't render as boxes
            possible_fonts = [
                'C:/Windows/Fonts/Nirmala.ttc', # Correct Windows TrueType Collection format
                'C:/Windows/Fonts/Nirmala.ttf',
                'C:/Windows/Fonts/mangal.ttf',
                'C:/Windows/Fonts/aparaj.ttf',
                'C:/Windows/Fonts/NotoSansDevanagari-Regular.ttf', # Linux WSL fallback
                None  # Final Fallback to default
            ]
            for font in possible_fonts:
                if font and os.path.exists(font):
                    font_path = font
                    break
        
        # Generate word frequencies ourselves to ensure correct Hindi tokenization
        # Use a regex that keeps Devanagari words (and their matras) together
        regexp = r"[\u0900-\u097F\u200C\u200D\w']+"
        
        # WordCloud's default regexp often breaks Indic matras.
        # We'll use our own logic or pass the regexp to the constructor.
        wc = WordCloud(
            width=1600,
            height=1000,
            background_color='white',
            colormap='viridis',
            max_words=150,
            font_path=font_path,
            relative_scaling=0.5,
            min_font_size=12,
            regexp=regexp,
            collocations=False # Avoid repeating single letters as collocations
        )
        
        # Process frequencies to bypass internal wordcloud tokenization issues
        word_counts = wc.process_text(cleaned_text)
        
        # Final filter: remove single characters from the word cloud (often fragmented letters)
        # unless they are meaningful emoji or specific tokens.
        filtered_counts = {w: freq for w, freq in word_counts.items() if len(w) > 1}
        
        if not filtered_counts:
            logger.warning("No words met frequency/length criteria")
            img = Image.new('RGB', (800, 400), color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return buf.getvalue()

        wc.generate_from_frequencies(filtered_counts)
        
        # Convert to image bytes
        image = wc.to_image()
        buf = io.BytesIO()
        image.save(buf, format='PNG', dpi=(300, 300))
        buf.seek(0)
        
        logger.info(f"Word cloud generated successfully ({len(posts)} posts)")
        return buf.getvalue()


# Global instance
wordcloud_service = WordCloudService()
