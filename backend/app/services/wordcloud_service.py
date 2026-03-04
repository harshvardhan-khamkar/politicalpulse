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
        """Initialize NLTK components"""
        if self.initialized:
            return
            
        try:
            import nltk
            from nltk.corpus import stopwords
            from nltk.stem import WordNetLemmatizer
            
            # Download required NLTK data
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords', quiet=True)
            
            try:
                nltk.data.find('corpora/wordnet')
            except LookupError:
                nltk.download('wordnet', quiet=True)
            
            try:
                nltk.data.find('taggers/averaged_perceptron_tagger')
            except LookupError:
                nltk.download('averaged_perceptron_tagger', quiet=True)
            
            self.stopwords = set(stopwords.words('english'))
            
            # Add custom political stopwords
            custom_stopwords = {
                'bjp', 'inc', 'aap', 'congress', 'party', 'year',
                'india', 'indian', 'government', 'people', 'time',
                'make', 'get', 'one', 'two', 'three', 'new', 'good'
            }
            self.stopwords.update(custom_stopwords)
            
            self.lemmatizer = WordNetLemmatizer()
            self.initialized = True
            logger.info("NLTK initialized successfully")
            
        except ImportError:
            logger.warning("NLTK not available. Basic word cloud generation only")
            self.initialized = False
        except Exception as e:
            logger.error(f"Error initializing NLTK: {e}")
            self.initialized = False
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        self._init_nltk()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove @mentions and#hashtags
        text = re.sub(r'[@#]\w+', '', text)
        
        # Remove punctuation and numbers
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Lemmatize and remove stopwords if available
        if self.initialized and self.lemmatizer:
            words = text.split()
            words = [self.lemmatizer.lemmatize(word) for word in words 
                    if word not in self.stopwords and len(word) > 2]
            text = ' '.join(words)
        
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
        """
        Generate word cloud image from social posts
        
        Args:
            db: Database Session
            party: Filter by party
            leader_name: Filter by leader
            platform: Filter by platform (twitter/reddit)
            source_type: Filter by source category (political/public)
            days: Days of history to include
            language: Language for font selection
            
        Returns:
            PNG image bytes
        """
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
            # Return empty image
            img = Image.new('RGB', (800, 400), color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return buf.getvalue()
        
        # Combine all text
        combined_text = ' '.join([post.content for post in posts])
        
        # Clean text
        cleaned_text = self.clean_text(combined_text)
        
        if not cleaned_text.strip():
            logger.warning("No text remaining after cleaning")
            img = Image.new('RGB', (800, 400), color='white')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return buf.getvalue()
        
        # Select font based on language
        font_path = None
        if language == 'hi':
            # For Hindi, try to use Devanagari font
            possible_fonts = [
                'C:/Windows/Fonts/NotoSansDevanagari-Regular.ttf',
                '/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf',
                None  # Fallback to default
            ]
            for font in possible_fonts:
                if font and os.path.exists(font):
                    font_path = font
                    break
        
        # Generate word cloud
        wc = WordCloud(
            width=1600,
            height=1000,
            background_color='white',
            colormap='viridis',
            max_words=100,
            font_path=font_path,
            relative_scaling=0.5,
            min_font_size=10
        ).generate(cleaned_text)
        
        # Convert to image bytes
        image = wc.to_image()
        buf = io.BytesIO()
        image.save(buf, format='PNG', dpi=(300, 300))
        buf.seek(0)
        
        logger.info(f"Word cloud generated successfully ({len(posts)} posts)")
        return buf.getvalue()


# Global instance
wordcloud_service = WordCloudService()
