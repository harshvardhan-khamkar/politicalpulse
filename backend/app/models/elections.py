from sqlalchemy import Column, BigInteger, String, Integer, Numeric, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ElectionResult(Base):
    """
    Model for existing election_results table
    Table already exists in database with 100,570 rows
    """
    __tablename__ = "election_results"
    
    id = Column(BigInteger, primary_key=True, index=True)
    state_name = Column(String(120), index=True, nullable=False)
    constituency_name = Column(String(150), index=True, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    position = Column(Integer, nullable=False)
    candidate_name = Column(String(150), nullable=False)
    gender = Column(String(20), nullable=True)
    party = Column(String(100), nullable=True, index=True)
    votes_secured = Column(BigInteger, nullable=False)
    vote_share_percentage = Column(Numeric(5, 2), nullable=False)
    turnout = Column(BigInteger, nullable=False)  # Note: integer representing percentage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ElectionResult {self.year} - {self.constituency_name} - {self.candidate_name}>"
