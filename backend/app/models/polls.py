from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class PollType(enum.Enum):
    opinion = "opinion"
    pre_election = "pre_election"
    policy = "policy"


class Poll(Base):
    """Polls created by admins for user participation"""
    __tablename__ = "polls"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    poll_type = Column(Enum(PollType), nullable=False, index=True)
    
    # Options stored as JSON: [{"id": "opt1", "text": "Option 1"}, ...]
    options = Column(JSON, nullable=False)
    
    # Status
    is_active = Column(Integer, default=1)  # 1 = active, 0 = closed
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    ends_at = Column(DateTime, nullable=True)
    
    # Relationship
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Poll(id={self.id}, title={self.title}, type={self.poll_type})>"


class PollVote(Base):
    """Individual votes on polls"""
    __tablename__ = "poll_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False, index=True)
    option_id = Column(String(50), nullable=False)  # References options JSON in Poll
    
    # Voter info (optional - can be anonymous or tracked by session/IP)
    voter_info = Column(String(200))  # session_id or user_id
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    poll = relationship("Poll", back_populates="votes")
    
    def __repr__(self):
        return f"<PollVote(poll_id={self.poll_id}, option={self.option_id})>"
