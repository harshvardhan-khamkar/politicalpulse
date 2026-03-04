from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PartyBase(BaseModel):
    """Base schema for party"""
    name: str = Field(..., min_length=2, max_length=100)
    short_name: Optional[str] = Field(None, max_length=20)
    ideology: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = Field(None, ge=1800, le=2100)
    overview: Optional[str] = None
    history: Optional[str] = None
    policies: Optional[str] = None
    website: Optional[str] = Field(None, max_length=200)
    logo_url: Optional[str] = Field(None, max_length=500)
    color_hex: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    eci_chart_image_url: Optional[str] = Field(None, max_length=1000)


class PartyCreate(PartyBase):
    """Schema for creating a party"""
    pass


class PartyUpdate(BaseModel):
    """Schema for updating a party"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    short_name: Optional[str] = None
    ideology: Optional[str] = None
    founded_year: Optional[int] = None
    overview: Optional[str] = None
    history: Optional[str] = None
    policies: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    color_hex: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    eci_chart_image_url: Optional[str] = None
    states_won: Optional[int] = Field(None, ge=0)
    total_mps: Optional[int] = Field(None, ge=0)
    total_mlas: Optional[int] = Field(None, ge=0)
    vote_share_percentage: Optional[str] = None


class PartyLeaderBase(BaseModel):
    """Base schema for party leader"""
    name: str = Field(..., min_length=2, max_length=100)
    position: Optional[str] = Field(None, max_length=100, description="President, Secretary, etc.")
    photo_url: Optional[str] = Field(None, max_length=500)
    twitter_handle: Optional[str] = Field(None, max_length=50, pattern=r'^@?[A-Za-z0-9_]+$')
    display_order: Optional[int] = Field(0, ge=0)


class PartyLeaderCreate(PartyLeaderBase):
    """Schema for creating a party leader"""
    party_id: int = Field(..., description="Party ID")


class PartyLeaderUpdate(BaseModel):
    """Schema for updating a party leader"""
    name: Optional[str] = None
    position: Optional[str] = None
    photo_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    display_order: Optional[int] = None


class PartyLeaderResponse(PartyLeaderBase):
    """Schema for party leader response"""
    id: int
    party_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PartyResponse(PartyBase):
    """Schema for party response"""
    id: int
    states_won: int
    total_mps: int
    total_mlas: int
    vote_share_percentage: Optional[str]
    created_at: datetime
    updated_at: datetime
    leaders: List[PartyLeaderResponse] = []

    class Config:
        from_attributes = True


class PartyWikiResponse(BaseModel):
    """Schema for wiki-style party page payload"""
    id: int
    name: str
    short_name: Optional[str]
    logo_url: Optional[str]
    color_hex: Optional[str]
    founded_year: Optional[int]
    ideology: Optional[str]
    overview: Optional[str]
    history: Optional[str]
    policies: Optional[str]
    website: Optional[str]
    eci_chart_image_url: Optional[str]
    states_won: int
    total_mps: int
    total_mlas: int
    vote_share_percentage: Optional[str]
    leaders: List[PartyLeaderResponse] = []
    has_logo_image: bool = False
    has_eci_chart_image: bool = False
    wordcloud_image_url: str


class PartyLeaderBulkUpsert(BaseModel):
    """Leader payload for wiki upsert endpoint."""
    name: str = Field(..., min_length=2, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    photo_url: Optional[str] = Field(None, max_length=500)
    twitter_handle: Optional[str] = Field(None, max_length=50, pattern=r'^@?[A-Za-z0-9_]+$')
    display_order: Optional[int] = Field(0, ge=0)


class PartyWikiUpsertRequest(PartyBase):
    """Single-request admin payload for party wiki page."""
    id: Optional[int] = Field(
        None,
        ge=1,
        description="Existing party ID. If omitted, upsert uses party name.",
    )
    states_won: Optional[int] = Field(0, ge=0)
    total_mps: Optional[int] = Field(0, ge=0)
    total_mlas: Optional[int] = Field(0, ge=0)
    vote_share_percentage: Optional[str] = None
    leaders: List[PartyLeaderBulkUpsert] = []
    replace_leaders: bool = Field(
        True,
        description="When true, existing leaders are replaced by the provided list.",
    )


class PartyListResponse(BaseModel):
    """Schema for list of parties (without leaders)"""
    id: int
    name: str
    short_name: Optional[str]
    ideology: Optional[str]
    logo_url: Optional[str]
    color_hex: Optional[str]
    total_mps: int
    vote_share_percentage: Optional[str]

    class Config:
        from_attributes = True


class PartyAssetsUploadResponse(BaseModel):
    """Response for party image upload endpoint."""
    party_id: int
    logo_image_url: Optional[str] = None
    eci_chart_image_url: Optional[str] = None
