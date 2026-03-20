from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Numeric
from sqlalchemy.dialects.postgresql import JSONB
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

    # ML Alignment (from alignment_model_service)
    predicted_alignment = Column(String(50), nullable=True)
    alignment_confidence = Column(Numeric(5, 4), nullable=True)

    # Public reply sentiment (populated by async reply pipeline)
    public_sentiment_label = Column(String(20), nullable=True)
    public_sentiment_score = Column(Numeric(5, 4), nullable=True)
    public_reaction_summary = Column(JSONB, nullable=True)  # {positive, negative, neutral, total}
    replies_fetched = Column(Boolean, default=False, nullable=False)

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


class TweetReply(Base):
    """Reply tweets for a parent TwitterPost, analyzed by the async reply pipeline."""

    __tablename__ = "tweet_replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_post_id = Column(
        String(100),
        ForeignKey("twitter_posts.post_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reply_id = Column(String(100), unique=True, nullable=False, index=True)
    reply_username = Column(String(100), nullable=True)
    reply_content = Column(Text, nullable=False)
    reply_language = Column(String(10), nullable=True)
    reply_sentiment_label = Column(String(20), nullable=True)  # positive/negative/neutral
    reply_sentiment_score = Column(Numeric(5, 4), nullable=True)
    reply_likes = Column(Integer, default=0)
    reply_posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<TweetReply(reply_id={self.reply_id}, parent={self.parent_post_id}, label={self.reply_sentiment_label})>"


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
