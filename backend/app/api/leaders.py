"""
Leaders API
Public and admin endpoints for politician/leader profiles.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from fastapi.responses import Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models.parties import Party, PartyLeader
from app.models.social_media import TwitterPost
from app.models.users import AppUser
from app.schemas.parties import (
    PartyLeaderCreate,
    PartyLeaderUpdate,
    PartyLeaderResponse,
    LeaderListResponse,
    LeaderWikiResponse,
)
from app.security import get_current_admin
from app.services.wordcloud_service import wordcloud_service

router = APIRouter(prefix="/leaders", tags=["Leaders"])


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def _photo_url(leader: PartyLeader) -> Optional[str]:
    """Return the best photo URL for a leader."""
    if leader.photo_image_data:
        return f"/leaders/{leader.id}/photo"
    return leader.photo_url


def _get_leader_wordcloud_version(
    db: Session,
    leader: PartyLeader,
    days: int = 365,
    source_type: Optional[str] = "political",
) -> str:
    """Return a cache token that changes when the leader's backing tweet set changes."""
    cutoff = datetime.now() - timedelta(days=days)
    handle = (leader.twitter_handle or "").replace("@", "").strip().lower()
    leader_name = (leader.name or "").strip().lower()

    filters = []
    if leader_name:
        filters.extend(
            [
                func.lower(TwitterPost.leader_name) == leader_name,
                func.lower(TwitterPost.leader_name) == leader_name.replace(" ", ""),
            ]
        )
    if handle:
        filters.extend(
            [
                func.lower(TwitterPost.username) == handle,
                func.lower(TwitterPost.leader_name) == handle,
            ]
        )

    query = db.query(func.max(TwitterPost.posted_at)).filter(TwitterPost.posted_at >= cutoff)
    if filters:
        query = query.filter(or_(*filters))
    if source_type:
        query = query.filter(TwitterPost.source_type == source_type)

    latest_posted_at = query.scalar()
    version_source = latest_posted_at or leader.updated_at or leader.created_at
    if not version_source:
        return "0"

    return str(int(version_source.timestamp()))


def _to_list_response(leader: PartyLeader) -> dict:
    party = leader.party
    return {
        "id": leader.id,
        "name": leader.name,
        "position": leader.position,
        "party_id": leader.party_id,
        "party_name": party.name if party else None,
        "party_short_name": party.short_name if party else None,
        "party_color_hex": party.color_hex if party else None,
        "photo_url": _photo_url(leader),
        "has_photo_image": leader.photo_image_data is not None,
        "state": leader.state,
        "twitter_handle": leader.twitter_handle,
    }


def _to_wiki_response(leader: PartyLeader, wordcloud_version: str) -> dict:
    party = leader.party
    return {
        "id": leader.id,
        "name": leader.name,
        "position": leader.position,
        "bio": leader.bio,
        "state": leader.state,
        "constituency": leader.constituency,
        "election_history": leader.election_history,
        "twitter_handle": leader.twitter_handle,
        "photo_url": _photo_url(leader),
        "has_photo_image": leader.photo_image_data is not None,
        "party_id": leader.party_id,
        "party_name": party.name if party else None,
        "party_short_name": party.short_name if party else None,
        "party_color_hex": party.color_hex if party else None,
        "wordcloud_url_en": f"/leaders/{leader.id}/wordcloud?language=en&days=365&v={wordcloud_version}",
        "wordcloud_url_hi": f"/leaders/{leader.id}/wordcloud?language=hi&days=365&v={wordcloud_version}",
    }


# ────────────────────────────────────────────────────────────────────────────
# Public endpoints
# ────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[LeaderListResponse])
def list_leaders(
    party_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """List all leaders (optionally filtered by party)."""
    query = db.query(PartyLeader).options(joinedload(PartyLeader.party))
    if party_id is not None:
        query = query.filter(PartyLeader.party_id == party_id)
    query = query.order_by(PartyLeader.display_order, PartyLeader.name)
    leaders = query.all()
    return [_to_list_response(l) for l in leaders]


@router.get("/{leader_id}/wiki")
def get_leader_wiki(leader_id: int, db: Session = Depends(get_db)):
    """Get full leader profile (wiki-style)."""
    leader = (
        db.query(PartyLeader)
        .options(joinedload(PartyLeader.party))
        .filter(PartyLeader.id == leader_id)
        .first()
    )
    if not leader:
        raise HTTPException(status_code=404, detail=f"Leader {leader_id} not found")
    wordcloud_version = _get_leader_wordcloud_version(db, leader, days=365, source_type="political")
    return _to_wiki_response(leader, wordcloud_version)


@router.get("/{leader_id}/photo")
def get_leader_photo(leader_id: int, db: Session = Depends(get_db)):
    """Serve leader photo image."""
    leader = db.query(PartyLeader).filter(PartyLeader.id == leader_id).first()
    if not leader:
        raise HTTPException(status_code=404, detail="Leader not found")
    if not leader.photo_image_data:
        raise HTTPException(status_code=404, detail="No photo uploaded for this leader")
    return Response(
        content=leader.photo_image_data,
        media_type=leader.photo_image_content_type or "image/png",
    )


@router.get("/{leader_id}/wordcloud")
def get_leader_wordcloud(
    request: Request,
    leader_id: int,
    language: str = Query("all", pattern="^(all|en|hi)$"),
    days: int = Query(365, ge=1, le=3650),
    v: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Generate leader word cloud from their tweets (cached)."""
    leader = db.query(PartyLeader).filter(PartyLeader.id == leader_id).first()
    if not leader:
        raise HTTPException(status_code=404, detail="Leader not found")

    handle = (leader.twitter_handle or "").replace("@", "").strip() or None

    cache_entry = wordcloud_service.get_or_generate_wordcloud(
        db,
        leader_name=leader.name,
        username=handle,
        platform="twitter",
        source_type="political",
        days=days,
        language=language,
        cache_version=v,
    )
    etag = f'"{cache_entry.etag}"'
    cache_control = "public, max-age=86400, immutable" if v else "public, max-age=3600"
    headers = {"Cache-Control": cache_control, "ETag": etag}

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    return Response(content=cache_entry.image_bytes, media_type="image/png", headers=headers)


# ────────────────────────────────────────────────────────────────────────────
# Admin endpoints
# ────────────────────────────────────────────────────────────────────────────

@router.post("", response_model=PartyLeaderResponse, status_code=status.HTTP_201_CREATED)
def create_leader(
    leader: PartyLeaderCreate,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(get_current_admin),
):
    """Create a new leader (admin only)."""
    party = db.query(Party).filter(Party.id == leader.party_id).first()
    if not party:
        raise HTTPException(status_code=404, detail=f"Party {leader.party_id} not found")
    db_leader = PartyLeader(**leader.dict())
    db.add(db_leader)
    db.commit()
    db.refresh(db_leader)
    return db_leader


@router.put("/{leader_id}", response_model=PartyLeaderResponse)
def update_leader(
    leader_id: int,
    leader_update: PartyLeaderUpdate,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(get_current_admin),
):
    """Update a leader (admin only)."""
    db_leader = db.query(PartyLeader).filter(PartyLeader.id == leader_id).first()
    if not db_leader:
        raise HTTPException(status_code=404, detail=f"Leader {leader_id} not found")
    for key, value in leader_update.dict(exclude_unset=True).items():
        setattr(db_leader, key, value)
    db.commit()
    db.refresh(db_leader)
    return db_leader


@router.delete("/{leader_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leader(
    leader_id: int,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(get_current_admin),
):
    """Delete a leader (admin only)."""
    db_leader = db.query(PartyLeader).filter(PartyLeader.id == leader_id).first()
    if not db_leader:
        raise HTTPException(status_code=404, detail=f"Leader {leader_id} not found")
    db.delete(db_leader)
    db.commit()
    return None


@router.post("/{leader_id}/photo")
async def upload_leader_photo(
    leader_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(get_current_admin),
):
    """Upload a leader's photo (admin only)."""
    leader = db.query(PartyLeader).filter(PartyLeader.id == leader_id).first()
    if not leader:
        raise HTTPException(status_code=404, detail=f"Leader {leader_id} not found")

    photo_bytes = await photo.read()
    if len(photo_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Photo must be under 5 MB")

    leader.photo_image_data = photo_bytes
    leader.photo_image_content_type = photo.content_type
    leader.photo_url = None  # Clear external URL in favour of stored image
    db.commit()

    return {
        "leader_id": leader.id,
        "photo_url": f"/leaders/{leader.id}/photo",
    }
