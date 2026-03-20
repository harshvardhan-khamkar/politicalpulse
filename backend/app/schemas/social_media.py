from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SocialPostBase(BaseModel):
    """Base schema for social media post"""
    content: str = Field(..., min_length=1, description="Post content")
    leader_name: Optional[str] = Field(None, max_length=100)
    party: Optional[str] = Field(None, max_length=50)
    username: Optional[str] = Field(None, max_length=100)
    source_type: str = Field("public", pattern=r'^(political|public)$')
    url: Optional[str] = Field(None, max_length=500)


class SocialPostCreate(SocialPostBase):
    """Schema for creating a social post"""
    platform: str = Field(..., pattern=r'^(twitter|reddit)$', description="Platform: twitter or reddit")
    post_id: str = Field(..., max_length=100, description="Unique post ID from platform")
    subreddit: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    sentiment_label: Optional[str] = Field(None, max_length=20)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    likes: Optional[int] = Field(0, ge=0)
    retweets: Optional[int] = Field(0, ge=0)
    replies: Optional[int] = Field(0, ge=0)
    score: Optional[int] = Field(0, description="Reddit score")
    posted_at: datetime


class SocialPostResponse(SocialPostBase):
    """Schema for social post response"""
    id: int
    platform: str
    post_id: str
    subreddit: Optional[str] = None
    language: Optional[str]
    sentiment_label: Optional[str]
    sentiment_score: Optional[float]
    likes: int
    retweets: int
    replies: int
    score: int
    posted_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SentimentDataCreate(BaseModel):
    """Schema for creating sentiment data"""
    entity_type: str = Field(..., pattern=r'^(leader|party)$')
    entity_name: str = Field(..., max_length=100)
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    language: Optional[str] = Field(None, max_length=10)
    date: datetime
    source: Optional[str] = Field(None, max_length=20)
    sample_size: Optional[int] = Field(0, ge=0)


class SentimentDataResponse(BaseModel):
    """Schema for sentiment data response"""
    id: int
    entity_type: str
    entity_name: str
    sentiment_score: float
    language: Optional[str]
    date: datetime
    source: Optional[str]
    sample_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class SentimentQuery(BaseModel):
    """Schema for querying sentiment"""
    entity_name: str = Field(..., description="Name of leader or party")
    entity_type: Optional[str] = Field("party", pattern=r'^(leader|party)$')
    language: Optional[str] = Field(None, description="Filter by language")
    days: Optional[int] = Field(30, ge=1, le=365, description="Days of history to fetch")


# ─── Reply Analysis Schemas ────────────────────────────────────────────────────

class TweetReplyResponse(BaseModel):
    """Schema for a single tweet reply row."""
    id: int
    parent_post_id: str
    reply_id: str
    reply_username: Optional[str] = None
    reply_content: str
    reply_language: Optional[str] = None
    reply_sentiment_label: Optional[str] = None
    reply_sentiment_score: Optional[float] = None
    reply_likes: int = 0
    reply_posted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PublicSentimentResponse(BaseModel):
    """Public reply-based sentiment for a single tweet."""
    post_id: str
    party: Optional[str] = None
    content_sentiment_label: Optional[str] = None
    content_sentiment_score: Optional[float] = None
    public_sentiment_label: Optional[str] = None
    public_sentiment_score: Optional[float] = None
    public_reaction_summary: Optional[dict] = None
    replies_fetched: bool = False


class PublicSentimentComparisonResponse(BaseModel):
    """Party-level side-by-side: VADER content sentiment vs. public reply sentiment."""
    party: str
    days: int
    sample_size: int
    content_sentiment_avg: float
    public_sentiment_avg: float
    content_label_distribution: dict
    public_label_distribution: dict
