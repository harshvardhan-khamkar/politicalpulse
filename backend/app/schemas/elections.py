from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class ElectionResultBase(BaseModel):
    """Base schema for election results"""
    state_name: str
    constituency_name: str
    year: int
    position: int
    candidate_name: str
    gender: Optional[str] = None
    party: Optional[str] = None
    votes_secured: int
    vote_share_percentage: Decimal
    turnout: int  # Integer representing percentage


class ElectionResultResponse(ElectionResultBase):
    """Response schema for election results"""
    id: int

    class Config:
        from_attributes = True


class ElectionResultQuery(BaseModel):
    """Query parameters for searching election results"""
    state: str = Field(..., description="State name")
    constituency: str = Field(..., description="Constituency name")
    year: int = Field(..., description="Election year")


class StatesList(BaseModel):
    """List of states"""
    states: list[str]


class ConstituenciesList(BaseModel):
    """List of constituencies"""
    constituencies: list[str]


class YearsList(BaseModel):
    """List of election years"""
    years: list[int]


class ElectionStats(BaseModel):
    """Aggregated election statistics"""
    total_constituencies: int
    total_candidates: int
    total_votes: int
    average_turnout: float