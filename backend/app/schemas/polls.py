from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PollTypeEnum(str, Enum):
    opinion = "opinion"
    pre_election = "pre_election"
    policy = "policy"


class PollOption(BaseModel):
    """Single poll option"""
    id: str = Field(..., description="Unique option ID")
    text: str = Field(..., description="Option text")


class PollCreate(BaseModel):
    """Schema for creating a new poll"""
    title: str = Field(..., min_length=5, max_length=200, description="Poll title")
    description: Optional[str] = Field(None, description="Poll description")
    poll_type: PollTypeEnum = Field(..., description="Type of poll")
    options: List[PollOption] = Field(..., min_items=2, description="Poll options (minimum 2)")
    ends_at: Optional[datetime] = Field(None, description="When poll closes")


class PollUpdate(BaseModel):
    """Schema for updating a poll"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = None
    is_active: Optional[int] = Field(None, ge=0, le=1, description="1=active, 0=closed")
    ends_at: Optional[datetime] = None


class PollResponse(BaseModel):
    """Schema for poll response"""
    id: int
    title: str
    description: Optional[str]
    poll_type: PollTypeEnum
    options: List[PollOption]
    is_active: int
    created_at: datetime
    ends_at: Optional[datetime]
    vote_count: Optional[int] = Field(None, description="Total votes received")

    class Config:
        from_attributes = True


class VoteCreate(BaseModel):
    """Schema for casting a vote"""
    option_id: str = Field(..., description="Selected option ID")


class VoteResponse(BaseModel):
    """Schema for vote response"""
    id: int
    poll_id: int
    option_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PollResults(BaseModel):
    """Schema for poll results with vote counts"""
    poll_id: int
    title: str
    total_votes: int
    results: List[dict] = Field(..., description="Option ID with vote count and percentage")
    # Example: [{"option_id": "opt1", "text": "Modi", "votes": 150, "percentage": 60.0}, ...]
