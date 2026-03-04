from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PredictionCreate(BaseModel):
    """Schema for creating a prediction"""
    prediction_type: str = Field(..., pattern=r'^(pm_candidate|party_seats|constituency)$')
    candidate_name: Optional[str] = Field(None, max_length=100)
    party: Optional[str] = Field(None, max_length=50)
    predicted_win_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    predicted_seats: Optional[int] = Field(None, ge=0, le=543)
    seat_range_min: Optional[int] = Field(None, ge=0)
    seat_range_max: Optional[int] = Field(None, le=543)
    state_name: Optional[str] = Field(None, max_length=120)
    constituency_name: Optional[str] = Field(None, max_length=150)
    predicted_winner: Optional[str] = Field(None, max_length=100)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = Field(None, max_length=20)
    prediction_date: datetime
    valid_until: Optional[datetime] = None


class PredictionResponse(BaseModel):
    """Schema for prediction response"""
    id: int
    prediction_type: str
    candidate_name: Optional[str]
    party: Optional[str]
    predicted_win_rate: Optional[float]
    predicted_seats: Optional[int]
    seat_range_min: Optional[int]
    seat_range_max: Optional[int]
    state_name: Optional[str]
    constituency_name: Optional[str]
    predicted_winner: Optional[str]
    confidence_score: Optional[float]
    model_version: Optional[str]
    prediction_date: datetime
    valid_until: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class NewsArticleCreate(BaseModel):
    """Schema for creating a news article"""
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    content: Optional[str] = None
    url: str = Field(..., max_length=1000)
    image_url: Optional[str] = Field(None, max_length=1000)
    category: str = Field(..., pattern=r'^(india_politics|geopolitics)$')
    source: Optional[str] = Field(None, max_length=100)
    author: Optional[str] = Field(None, max_length=200)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    published_at: datetime


class NewsArticleResponse(BaseModel):
    """Schema for news article response"""
    id: int
    title: str
    description: Optional[str]
    content: Optional[str]
    url: str
    image_url: Optional[str]
    category: str
    source: Optional[str]
    author: Optional[str]
    relevance_score: Optional[float]
    published_at: datetime
    fetched_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class NewsQuery(BaseModel):
    """Schema for querying news"""
    category: Optional[str] = Field(None, pattern=r'^(india_politics|geopolitics)$')
    limit: Optional[int] = Field(20, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)


class CachedNewsArticle(BaseModel):
    """Schema for cached GNews article."""
    title: str
    description: str
    url: str
    image_url: str
    source: str
    published_at: datetime


class CachedNewsResponse(BaseModel):
    """Schema for cached category response."""
    category: str
    last_updated: datetime | None
    count: int
    articles: list[CachedNewsArticle]
