from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric
from sqlalchemy.sql import func
from app.database import Base


class Prediction(Base):
    """ML-generated predictions for elections"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What is being predicted
    prediction_type = Column(String(50), nullable=False, index=True)  # 'pm_candidate', 'party_seats', 'constituency'
    
    # PM Candidate predictions
    candidate_name = Column(String(100), index=True)
    party = Column(String(50), index=True)
    predicted_win_rate = Column(Numeric(5, 4))  # 0.0 to 1.0
    
    # Party seat projections
    predicted_seats = Column(Integer)
    seat_range_min = Column(Integer)
    seat_range_max = Column(Integer)
    
    # Constituency predictions
    state_name = Column(String(120))
    constituency_name = Column(String(150))
    predicted_winner = Column(String(100))
    confidence_score = Column(Numeric(5, 4))
    
    # Metadata
    model_version = Column(String(20))
    prediction_date = Column(DateTime, nullable=False, index=True)
    valid_until = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Prediction(type={self.prediction_type}, candidate={self.candidate_name})>"


class NewsArticle(Base):
    """Aggregated news articles"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Content
    title = Column(String(500), nullable=False)
    description = Column(Text)
    content = Column(Text)
    url = Column(String(1000), unique=True, nullable=False)
    image_url = Column(String(1000))
    
    # Classification
    category = Column(String(50), nullable=False, index=True)  # 'india_politics', 'geopolitics'
    source = Column(String(100))  # News source name
    author = Column(String(200))
    
    # Relevance
    relevance_score = Column(Numeric(5, 4))  # How relevant to Indian politics
    
    # Timestamps
    published_at = Column(DateTime, nullable=False, index=True)
    fetched_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title={self.title[:50]})>"
