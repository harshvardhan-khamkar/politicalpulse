"""
Word Cloud Service
Generate word clouds from social media data
Supports multilingual text with appropriate fonts
"""
import io
import os
import re
from dataclasses import dataclass
from hashlib import sha1
from threading import Event, RLock
from typing import Dict, Optional, Tuple
import logging
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.services.text_normalization import repair_mojibake

logger = logging.getLogger(__name__)


@dataclass
class WordCloudCacheEntry:
    image_bytes: bytes
    etag: str
    cached_at: datetime


class WordCloudService:
    """Generate word clouds from social media posts"""

    CACHE_TTL_SECONDS = 60 * 60 * 12
    CACHE_MAX_ENTRIES = 128
    
    def __init__(self):
        self.stopwords = None
        self.lemmatizer = None
        self.initialized = False
        self._cache: Dict[Tuple[str, str, str, str, str, int, str, str], WordCloudCacheEntry] = {}
        self._inflight: Dict[Tuple[str, str, str, str, str, int, str, str], Event] = {}
        self._cache_lock = RLock()
        
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

    def clean_text(self, text: str, language: str = 'en') -> str:
        """Clean and preprocess text, filtering by language."""
        self._init_nltk()
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove @mentions
        text = re.sub(r'@\w+', '', text)
        
        # Remove punctuation and numbers
        text = re.sub(r'[^\w\s#\u0900-\u097F\u200C\u200D]', ' ', text)
        text = re.sub(r'\d+', '', text)
        
        # Language-specific character filtering:
        # For English: strip ALL non-ASCII characters to prevent garbled rendering
        # For Hindi: keep only Devanagari characters (and spaces)
        if language == 'en':
            text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Strip non-ASCII
        elif language == 'hi':
            text = re.sub(r'[a-zA-Z]+', ' ', text)  # Strip Latin letters
        # language == 'all': keep everything
        
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
                
                # Minimum length check
                if len(clean_w) < 2:
                    continue

                if is_hindi(clean_w):
                    # Preserve Hindi words as is (no lemmatization)
                    clean_words.append(clean_w)
                elif self.lemmatizer:
                    # Lemmatize English words
                    clean_words.append(self.lemmatizer.lemmatize(clean_w))
                else:
                    clean_words.append(clean_w)
                    
            text = ' '.join(clean_words)
        
        return text

    @staticmethod
    def _fix_encoding(text: str) -> str:
        return repair_mojibake(text)

    def _build_cache_key(
        self,
        party: Optional[str] = None,
        leader_name: Optional[str] = None,
        username: Optional[str] = None,
        platform: Optional[str] = None,
        source_type: Optional[str] = None,
        days: int = 30,
        language: str = 'en',
        cache_version: Optional[str] = None,
    ) -> Tuple[str, str, str, str, str, int, str, str]:
        return (
            party or "",
            leader_name or "",
            username or "",
            platform or "all",
            source_type or "all",
            int(days),
            language or "all",
            cache_version or "",
        )

    def _get_cached_entry_locked(
        self,
        cache_key: Tuple[str, str, str, str, str, int, str, str],
    ) -> Optional[WordCloudCacheEntry]:
        entry = self._cache.get(cache_key)
        if not entry:
            return None

        age_seconds = (datetime.utcnow() - entry.cached_at).total_seconds()
        if age_seconds <= self.CACHE_TTL_SECONDS:
            return entry

        self._cache.pop(cache_key, None)
        return None

    def _store_cache_entry_locked(
        self,
        cache_key: Tuple[str, str, str, str, str, int, str, str],
        image_bytes: bytes,
    ) -> WordCloudCacheEntry:
        entry = WordCloudCacheEntry(
            image_bytes=image_bytes,
            etag=sha1(image_bytes).hexdigest(),
            cached_at=datetime.utcnow(),
        )
        self._cache[cache_key] = entry

        if len(self._cache) > self.CACHE_MAX_ENTRIES:
            oldest_key = min(self._cache, key=lambda key: self._cache[key].cached_at)
            self._cache.pop(oldest_key, None)

        return entry

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    def get_or_generate_wordcloud(
        self,
        db: Session,
        party: Optional[str] = None,
        leader_name: Optional[str] = None,
        username: Optional[str] = None,
        platform: Optional[str] = None,
        source_type: Optional[str] = None,
        days: int = 30,
        language: str = 'en',
        cache_version: Optional[str] = None,
        force_refresh: bool = False,
    ) -> WordCloudCacheEntry:
        cache_key = self._build_cache_key(
            party=party,
            leader_name=leader_name,
            username=username,
            platform=platform,
            source_type=source_type,
            days=days,
            language=language,
            cache_version=cache_version,
        )

        if not force_refresh:
            with self._cache_lock:
                cached = self._get_cached_entry_locked(cache_key)
            if cached:
                return cached

        with self._cache_lock:
            if not force_refresh:
                cached = self._get_cached_entry_locked(cache_key)
                if cached:
                    return cached

            inflight_event = self._inflight.get(cache_key)
            should_generate = inflight_event is None
            if should_generate:
                inflight_event = Event()
                self._inflight[cache_key] = inflight_event

        if not should_generate:
            inflight_event.wait()
            with self._cache_lock:
                cached = self._get_cached_entry_locked(cache_key)
            if cached:
                return cached

        try:
            image_bytes = self.generate_wordcloud(
                db,
                party=party,
                leader_name=leader_name,
                username=username,
                platform=platform,
                source_type=source_type,
                days=days,
                language=language,
            )
            with self._cache_lock:
                return self._store_cache_entry_locked(cache_key, image_bytes)
        finally:
            with self._cache_lock:
                event = self._inflight.pop(cache_key, None)
                if event:
                    event.set()

    def generate_wordcloud(
        self,
        db: Session,
        party: Optional[str] = None,
        leader_name: Optional[str] = None,
        username: Optional[str] = None,
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
            leader_filters = []
            if leader_name:
                normalized_name = leader_name.strip().lower()
                normalized_handle = leader_name.strip().lstrip("@").lower()
                leader_filters.extend(
                    [
                        func.lower(model.leader_name) == normalized_name,
                        func.lower(model.leader_name) == normalized_handle,
                        func.lower(model.username) == normalized_handle,
                    ]
                )
            if username:
                normalized_username = username.strip().lstrip("@").lower()
                leader_filters.append(func.lower(model.username) == normalized_username)
            if leader_filters:
                query = query.filter(or_(*leader_filters))
            if source_type:
                query = query.filter(model.source_type == source_type)
            if language != 'all':
                if language == 'en':
                    query = query.filter(
                        or_(model.language == language, model.language.is_(None), model.language == "")
                    )
                else:
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
        
        combined_text = ' '.join([repair_mojibake(post.content) for post in posts if post.content])
        cleaned_text = self.clean_text(combined_text, language=language)
        
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
                'C:/Windows/Fonts/Nirmala.ttf',  # Most common on Windows
                'C:/Windows/Fonts/Nirmala.ttc',
                'C:/Windows/Fonts/mangal.ttf',
                'C:/Windows/Fonts/aparaj.ttf',
                'C:/Windows/Fonts/NotoSansDevanagari-Regular.ttf', # Linux WSL fallback
                None  # Final Fallback to default
            ]
            for font in possible_fonts:
                if font and os.path.exists(font):
                    font_path = font
                    logger.info(f"Using Devanagari font: {font_path}")
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
