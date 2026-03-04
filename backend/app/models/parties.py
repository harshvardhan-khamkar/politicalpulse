from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Party(Base):
    """Political parties information"""
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    short_name = Column(String(20))  # BJP, INC, AAP, etc.

    # Information
    ideology = Column(String(100))
    founded_year = Column(Integer)
    overview = Column(Text)  # short wiki-style summary
    history = Column(Text)
    policies = Column(Text)  # policy summary / manifesto highlights
    website = Column(String(200))

    # Visual
    logo_url = Column(String(500))
    logo_image_data = Column(LargeBinary)  # stored binary image bytes
    logo_image_content_type = Column(String(100))  # image/png, image/jpeg, etc.
    color_hex = Column(String(7))  # #FF9933 for BJP, etc.
    eci_chart_image_url = Column(String(1000))  # static chart image URL
    eci_chart_image_data = Column(LargeBinary)  # stored binary image bytes
    eci_chart_image_content_type = Column(String(100))  # image/png, image/jpeg, etc.

    # Electoral statistics (updated periodically)
    states_won = Column(Integer, default=0)
    total_mps = Column(Integer, default=0)
    total_mlas = Column(Integer, default=0)
    vote_share_percentage = Column(String(10))

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    leaders = relationship("PartyLeader", back_populates="party", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Party(id={self.id}, name={self.name})>"


class PartyLeader(Base):
    """Key leaders of political parties"""
    __tablename__ = "party_leaders"

    id = Column(Integer, primary_key=True, index=True)
    party_id = Column(Integer, ForeignKey("parties.id"), nullable=False, index=True)

    name = Column(String(100), nullable=False, index=True)
    position = Column(String(100))  # President, General Secretary, etc.
    photo_url = Column(String(500))
    twitter_handle = Column(String(50))

    # Order for display
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())

    # Relationship
    party = relationship("Party", back_populates="leaders")

    def __repr__(self):
        return f"<PartyLeader(name={self.name}, position={self.position})>"
