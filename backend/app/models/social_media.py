from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric
from sqlalchemy.sql import func
from app.database import Base


class _SocialPostColumns:
    """Shared columns for per-platform social post tables."""

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(100), unique=True, nullable=False, index=True)

    # Attribution
    leader_name = Column(String(100), index=True)
    party = Column(String(50), index=True)
    username = Column(String(100), index=True)
    source_type = Column(String(20), nullable=False, default="public", index=True)  # political/public

    # Content
    content = Column(Text, nullable=False)
    language = Column(String(10), index=True)  # ISO code: en, hi, ta, etc.

    # Sentiment
    sentiment_label = Column(String(20))  # positive/negative/neutral
    sentiment_score = Column(Numeric(5, 4))

    # Engagement metrics
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    score = Column(Integer, default=0)  # Used mostly for Reddit

    # URLs and metadata
    url = Column(String(500))
    posted_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())


class TwitterPost(Base, _SocialPostColumns):
    """Twitter posts only."""

    __tablename__ = "twitter_posts"

    @property
    def platform(self) -> str:
        return "twitter"

    def __repr__(self):
        return f"<TwitterPost(id={self.id}, party={self.party}, source_type={self.source_type})>"


class RedditPost(Base, _SocialPostColumns):
    """Reddit posts only."""

    __tablename__ = "reddit_posts"
    subreddit = Column(String(100), index=True)

    @property
    def platform(self) -> str:
        return "reddit"

    def __repr__(self):
        return f"<RedditPost(id={self.id}, subreddit={self.subreddit}, source_type={self.source_type})>"


class SentimentData(Base):
    """Aggregated sentiment data for leaders and parties"""
    __tablename__ = "sentiment_data"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), nullable=False)  # 'leader', 'party'
    entity_name = Column(String(100), nullable=False, index=True)
    
    sentiment_score = Column(Numeric(5, 4), nullable=False)
    language = Column(String(10), index=True)
    date = Column(DateTime, nullable=False, index=True)
    source = Column(String(20))  # 'twitter', 'reddit', 'news'
    sample_size = Column(Integer, default=0)  # Number of posts analyzed
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<SentimentData(entity={self.entity_name}, score={self.sentiment_score})>"
