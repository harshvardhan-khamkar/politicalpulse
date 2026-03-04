"""
Reddit Service
Integrates PRAW for Reddit scraping
Scrapes Indian political subreddits
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Default subreddits to monitor
DEFAULT_SUBREDDITS = [
    'india',
    'IndiaSpeaks',
    'unitedstatesofindia',
    'librandu'
]

# Keywords to search for
POLITICAL_KEYWORDS = [
    'BJP', 'Congress', 'AAP', 'Modi', 'Rahul Gandhi', 'Kejriwal',
    'election', 'politics', 'government', 'minister', 'parliament'
]


class RedditService:
    """Reddit scraping service using PRAW"""
    
    def __init__(self):
        self.reddit = None
        self.initialized = False
        
    def _init_client(self):
        """Initialize PRAW client"""
        if self.initialized:
            return
            
        try:
            import praw
            from app.config import settings
            
            # Check if credentials are in settings
            if not hasattr(settings, 'REDDIT_CLIENT_ID'):
                logger.warning("Reddit credentials not configured")
                raise ValueError("Reddit API credentials not found in settings")
            
            self.reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
            
            self.initialized = True
            logger.info("Reddit client initialized successfully")
            
        except ImportError:
            logger.error("PRAW not installed. Install with: pip install praw")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise
    
    def scrape_subreddit(
        self,
        db: Session,
        subreddit_name: str,
        limit: int = 100,
        time_filter: str = 'week'
    ) -> Dict[str, int]:
        """
        Scrape posts from a subreddit
        
        Args:
            db: Database session
            subreddit_name: Name of subreddit (without r/)
            limit: Maximum posts to fetch
            time_filter: 'day', 'week', 'month', 'year', 'all'
            
        Returns:
            Statistics dict
        """
        from app.models.social_media import RedditPost
        from app.services.sentiment_service import sentiment_analyzer
        
        self._init_client()
        
        stats = {'total_fetched': 0, 'new_inserted': 0, 'duplicates': 0}
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get hot posts
            for submission in subreddit.hot(limit=limit):
                stats['total_fetched'] += 1
                
                # Build post ID (reddit ID is unique)
                post_id = f"reddit_{submission.id}"
                
                # Check if already exists
                existing = db.query(RedditPost).filter(
                    RedditPost.post_id == post_id
                ).first()
                
                if existing:
                    stats['duplicates'] += 1
                    continue
                
                # Combine title and selftext for content
                content = f"{submission.title}\n\n{submission.selftext[:2000]}"
                
                # Analyze sentiment
                sentiment = sentiment_analyzer.analyze_sentiment(content)
                
                # Create post record
                posted_at = datetime.fromtimestamp(submission.created_utc)
                
                post = RedditPost(
                    post_id=post_id,
                    party=None,  # Can enhance with keyword matching
                    username=str(submission.author) if submission.author else '[deleted]',
                    source_type='public',
                    subreddit=subreddit_name,
                    leader_name=None,
                    content=content,
                    language=sentiment['language'],
                    sentiment_label=sentiment['label'],
                    sentiment_score=sentiment['score'],
                    likes=0,  # Reddit doesn't expose exact likes
                    retweets=0,
                    replies=submission.num_comments,
                    score=submission.score,
                    url=f"https://reddit.com{submission.permalink}",
                    posted_at=posted_at
                )
                
                db.add(post)
                stats['new_inserted'] += 1
            
            # Commit all posts
            db.commit()
            logger.info(f"Reddit scraping complete for r/{subreddit_name}: {stats}")
            
        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {e}")
            db.rollback()
            stats['error'] = str(e)
        
        return stats
    
    def scrape_by_keyword(
        self,
        db: Session,
        subreddit_name: str,
        keyword: str,
        limit: int = 50
    ) -> Dict[str, int]:
        """Search subreddit by keyword"""
        from app.models.social_media import RedditPost
        from app.services.sentiment_service import sentiment_analyzer
        
        self._init_client()
        
        stats = {'total_fetched': 0, 'new_inserted': 0, 'duplicates': 0}
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            for submission in subreddit.search(keyword, limit=limit, time_filter='month'):
                stats['total_fetched'] += 1
                
                post_id = f"reddit_{submission.id}"
                
                # Check if exists
                if db.query(RedditPost).filter(RedditPost.post_id == post_id).first():
                    stats['duplicates'] += 1
                    continue
                
                content = f"{submission.title}\n\n{submission.selftext[:2000]}"
                sentiment = sentiment_analyzer.analyze_sentiment(content)
                
                post = RedditPost(
                    post_id=post_id,
                    username=str(submission.author) if submission.author else '[deleted]',
                    source_type='public',
                    subreddit=subreddit_name,
                    content=content,
                    language=sentiment['language'],
                    sentiment_label=sentiment['label'],
                    sentiment_score=sentiment['score'],
                    replies=submission.num_comments,
                    score=submission.score,
                    url=f"https://reddit.com{submission.permalink}",
                    posted_at=datetime.fromtimestamp(submission.created_utc)
                )
                
                db.add(post)
                stats['new_inserted'] += 1
            
            db.commit()
            logger.info(f"Reddit keyword search '{keyword}' in r/{subreddit_name}: {stats}")
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            db.rollback()
            stats['error'] = str(e)
        
        return stats
    
    def scrape_all_subreddits(
        self,
        db: Session,
        subreddits: Optional[List[str]] = None,
        limit_per_sub: int = 100
    ) -> Dict[str, Dict]:
        """Scrape all configured subreddits"""
        if subreddits is None:
            subreddits = DEFAULT_SUBREDDITS
        
        results = {}
        
        for subreddit_name in subreddits:
            logger.info(f"Scraping r/{subreddit_name}")
            try:
                stats = self.scrape_subreddit(db, subreddit_name, limit_per_sub)
                results[subreddit_name] = stats
            except Exception as e:
                logger.error(f"Failed to scrape r/{subreddit_name}: {e}")
                results[subreddit_name] = {'error': str(e)}
        
        return results


# Global instance
reddit_service = RedditService()
