from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric
from sqlalchemy.sql import func
from app.database import Base


class PoliticalEvent(Base):
    """Political events that may impact discourse and sentiment."""
    __tablename__ = "political_events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    date = Column(Date, nullable=False, index=True)
    keywords = Column(Text)
    impact_score = Column(Numeric(5, 4))
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<PoliticalEvent(id={self.id}, name={self.name})>"


class TopicData(Base):
    """Extracted topics from social media posts via NMF topic modeling."""
    __tablename__ = "topic_data"

    id = Column(Integer, primary_key=True, index=True)
    topic_name = Column(String(100), nullable=False)
    keywords = Column(Text, nullable=False)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    salience_score = Column(Numeric(5, 4))
    average_sentiment = Column(Numeric(5, 4))
    document_count = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<TopicData(id={self.id}, topic={self.topic_name})>"
