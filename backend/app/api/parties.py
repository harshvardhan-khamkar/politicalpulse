from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app.models.parties import Party, PartyLeader
from app.models.social_media import RedditPost, TwitterPost
from app.models.users import AppUser
from app.schemas.parties import (
    PartyCreate,
    PartyUpdate,
    PartyResponse,
    PartyListResponse,
    PartyWikiResponse,
    PartyWikiUpsertRequest,
    PartyAssetsUploadResponse,
    PartyLeaderCreate,
    PartyLeaderUpdate,
    PartyLeaderResponse,
)
from app.security import get_current_admin
from app.services.wordcloud_service import wordcloud_service
from app.services.wiki_service import wiki_service

router = APIRouter(prefix="/parties", tags=["Parties"])


def _resolve_party_wordcloud_key(
    db: Session,
    party: Party,
    platform: str = "twitter",
    source_type: Optional[str] = "political",
    days: int = 365,
) -> str:
    """Pick the most data-rich key between party.name and party.short_name."""
    cutoff = datetime.now() - timedelta(days=days)

    candidates = []
    if party.short_name:
        candidates.append(party.short_name)
    if party.name and party.name not in candidates:
        candidates.append(party.name)

    if not candidates:
        return party.name

    best_key = candidates[0]
    best_count = -1

    for key in candidates:
        if platform == "twitter":
            query = db.query(TwitterPost).filter(
                TwitterPost.party == key,
                TwitterPost.posted_at >= cutoff,
            )
            if source_type:
                query = query.filter(TwitterPost.source_type == source_type)
            count = query.count()
        elif platform == "reddit":
            query = db.query(RedditPost).filter(
                RedditPost.party == key,
                RedditPost.posted_at >= cutoff,
            )
            if source_type:
                query = query.filter(RedditPost.source_type == source_type)
            count = query.count()
        else:
            twitter_query = db.query(TwitterPost).filter(
                TwitterPost.party == key,
                TwitterPost.posted_at >= cutoff,
            )
            reddit_query = db.query(RedditPost).filter(
                RedditPost.party == key,
                RedditPost.posted_at >= cutoff,
            )
            if source_type:
                twitter_query = twitter_query.filter(TwitterPost.source_type == source_type)
                reddit_query = reddit_query.filter(RedditPost.source_type == source_type)
            count = twitter_query.count() + reddit_query.count()

        if count > best_count:
            best_count = count
            best_key = key

    return best_key


def _get_party_logo_url(party: Party) -> Optional[str]:
    """Return backend image URL only when DB image exists."""
    if party.logo_image_data:
        return f"/parties/{party.id}/logo"
    return None


def _get_party_eci_chart_url(party: Party) -> Optional[str]:
    """Return backend image URL only when DB image exists."""
    if party.eci_chart_image_data:
        return f"/parties/{party.id}/eci-chart"
    return None


def _get_party_wordcloud_version(
    db: Session,
    party: Party,
    platform: str = "twitter",
    source_type: Optional[str] = "political",
    days: int = 365,
) -> str:
    """Return a stable cache token that changes when the backing post set changes."""
    cutoff = datetime.now() - timedelta(days=days)
    party_key = _resolve_party_wordcloud_key(
        db,
        party,
        platform=platform,
        source_type=source_type,
        days=days,
    )

    if platform == "twitter":
        query = db.query(func.max(TwitterPost.posted_at)).filter(
            TwitterPost.party == party_key,
            TwitterPost.posted_at >= cutoff,
        )
        if source_type:
            query = query.filter(TwitterPost.source_type == source_type)
        latest_posted_at = query.scalar()
    elif platform == "reddit":
        query = db.query(func.max(RedditPost.posted_at)).filter(
            RedditPost.party == party_key,
            RedditPost.posted_at >= cutoff,
        )
        if source_type:
            query = query.filter(RedditPost.source_type == source_type)
        latest_posted_at = query.scalar()
    else:
        latest_posted_at = None

    version_source = latest_posted_at or party.updated_at or party.created_at
    if not version_source:
        return "0"

    return str(int(version_source.timestamp()))


# ========== Party Endpoints ==========

@router.post("/", response_model=PartyResponse, status_code=status.HTTP_201_CREATED)
def create_party(
    party: PartyCreate,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """Create a new party (admin only)."""
    # Check if party with same name exists
    existing = db.query(Party).filter(Party.name == party.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Party with name '{party.name}' already exists",
        )

    party_data = party.dict(exclude={"logo_url", "eci_chart_image_url"})
    db_party = Party(**party_data)
    db.add(db_party)
    db.commit()
    db.refresh(db_party)
    return db_party


@router.post("/wiki/upsert", response_model=PartyResponse)
def upsert_party_wiki(
    payload: PartyWikiUpsertRequest,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """
    Create or update party wiki/profile content in one request (admin only).

    Behavior:
    - Uses `id` when provided, else resolves by `name`.
    - Writes party profile/stats fields.
    - Replaces leaders when `replace_leaders=true` (default).
    """
    db_party = None
    if payload.id is not None:
        db_party = db.query(Party).filter(Party.id == payload.id).first()

    if db_party is None:
        db_party = db.query(Party).filter(Party.name == payload.name).first()

    party_data = payload.dict(
        exclude={"id", "leaders", "replace_leaders", "logo_url", "eci_chart_image_url"},
        exclude_unset=True,
    )

    if db_party is None:
        db_party = Party(**party_data)
        db.add(db_party)
        db.flush()
    else:
        for key, value in party_data.items():
            setattr(db_party, key, value)

    if payload.replace_leaders:
        db.query(PartyLeader).filter(PartyLeader.party_id == db_party.id).delete(
            synchronize_session=False
        )

    for leader in payload.leaders:
        leader_data = leader.dict(exclude_unset=True)
        db.add(PartyLeader(party_id=db_party.id, **leader_data))

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Party upsert failed. Ensure party name is unique.",
        )

    party_with_leaders = (
        db.query(Party)
        .options(joinedload(Party.leaders))
        .filter(Party.id == db_party.id)
        .first()
    )
    if party_with_leaders is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found after upsert",
        )

    party_with_leaders.leaders = sorted(
        party_with_leaders.leaders,
        key=lambda leader: (leader.display_order or 0, leader.id),
    )
    return party_with_leaders


@router.get("/", response_model=List[PartyListResponse])
def get_parties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all parties (list view without leaders)."""
    parties = db.query(Party).order_by(Party.total_mps.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": party.id,
            "name": party.name,
            "short_name": party.short_name,
            "ideology": party.ideology,
            "logo_url": _get_party_logo_url(party),
            "color_hex": party.color_hex,
            "total_mps": party.total_mps,
            "vote_share_percentage": party.vote_share_percentage,
        }
        for party in parties
    ]


@router.get("/name/{party_name}", response_model=PartyResponse)
def get_party_by_name(party_name: str, db: Session = Depends(get_db)):
    """Get a party by name."""
    party = db.query(Party).options(joinedload(Party.leaders)).filter(Party.name == party_name).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party '{party_name}' not found",
        )
    return party


@router.get("/{party_id}", response_model=PartyResponse)
def get_party(party_id: int, db: Session = Depends(get_db)):
    """Get a specific party with its leaders."""
    party = db.query(Party).options(joinedload(Party.leaders)).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )
    return party


@router.get("/{party_id}/wiki", response_model=PartyWikiResponse)
def get_party_wiki(party_id: int, db: Session = Depends(get_db)):
    """
    Get page-ready party payload for wiki/information view.
    Includes profile, leaders, stats, and wordcloud URL.
    """
    party = db.query(Party).options(joinedload(Party.leaders)).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    wordcloud_version = _get_party_wordcloud_version(
        db,
        party,
        platform="twitter",
        source_type="political",
        days=365,
    )

    return {
        "id": party.id,
        "name": party.name,
        "short_name": party.short_name,
        "logo_url": _get_party_logo_url(party),
        "color_hex": party.color_hex,
        "founded_year": party.founded_year,
        "ideology": party.ideology,
        "overview": party.overview,
        "history": party.history,
        "policies": party.policies,
        "website": party.website,
        "eci_chart_image_url": _get_party_eci_chart_url(party),
        "states_won": party.states_won,
        "total_mps": party.total_mps,
        "total_mlas": party.total_mlas,
        "vote_share_percentage": party.vote_share_percentage,
        "leaders": party.leaders,
        "has_logo_image": bool(party.logo_image_data),
        "has_eci_chart_image": bool(party.eci_chart_image_data),
        "wordcloud_image_url_en": (
            f"/parties/{party.id}/wordcloud?platform=twitter&source_type=political&days=365&language=en&v={wordcloud_version}"
        ),
        "wordcloud_image_url_hi": (
            f"/parties/{party.id}/wordcloud?platform=twitter&source_type=political&days=365&language=hi&v={wordcloud_version}"
        ),
    }


@router.post("/{party_id}/wiki/sync", response_model=PartyResponse)
def sync_party_wiki(
    party_id: int,
    db: Session = Depends(get_db),
    current_admin: AppUser = Depends(get_current_admin),
):
    """
    Fetch information from Wikipedia and update the party details.
    Admin only.
    """
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    # Fetch from Wiki
    wiki_data = wiki_service.get_party_info(party.name)
    if not wiki_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not find Wikipedia information for {party.name}",
        )

    # Update fields if found
    if wiki_data.get("overview"):
        party.overview = wiki_data["overview"]
    if wiki_data.get("history"):
        party.history = wiki_data["history"]
    if wiki_data.get("ideology"):
        party.ideology = wiki_data["ideology"]
    if wiki_data.get("founded_year"):
        party.founded_year = wiki_data["founded_year"]

    try:
        db.commit()
        db.refresh(party)
        return party
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating party info: {str(e)}",
        )


@router.post("/{party_id}/assets", response_model=PartyAssetsUploadResponse)
async def upload_party_assets(
    party_id: int,
    logo: Optional[UploadFile] = File(default=None),
    eci_chart: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """Upload party logo / ECI chart images and store them in DB (admin only)."""
    if logo is None and eci_chart is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one file: logo or eci_chart",
        )

    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    max_size_bytes = 10 * 1024 * 1024  # 10 MB per image

    if logo is not None:
        if not logo.content_type or not logo.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="logo must be an image file",
            )
        logo_bytes = await logo.read()
        if not logo_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="logo file is empty",
            )
        if len(logo_bytes) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="logo file exceeds 10MB",
            )
        party.logo_image_data = logo_bytes
        party.logo_image_content_type = logo.content_type
        party.logo_url = None

    if eci_chart is not None:
        if not eci_chart.content_type or not eci_chart.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eci_chart must be an image file",
            )
        eci_chart_bytes = await eci_chart.read()
        if not eci_chart_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eci_chart file is empty",
            )
        if len(eci_chart_bytes) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eci_chart file exceeds 10MB",
            )
        party.eci_chart_image_data = eci_chart_bytes
        party.eci_chart_image_content_type = eci_chart.content_type
        party.eci_chart_image_url = None

    db.commit()
    db.refresh(party)

    return {
        "party_id": party.id,
        "logo_image_url": _get_party_logo_url(party),
        "eci_chart_image_url": _get_party_eci_chart_url(party),
    }


@router.get("/{party_id}/logo")
def get_party_logo(party_id: int, db: Session = Depends(get_db)):
    """Return party logo image stored in DB."""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )
    if not party.logo_image_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Logo image not found for party ID {party_id}",
        )
    return Response(
        content=party.logo_image_data,
        media_type=party.logo_image_content_type or "image/png",
    )


@router.get("/{party_id}/eci-chart")
def get_party_eci_chart_image(party_id: int, db: Session = Depends(get_db)):
    """Return ECI chart image stored in DB."""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )
    if not party.eci_chart_image_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ECI chart image not found for party ID {party_id}",
        )
    return Response(
        content=party.eci_chart_image_data,
        media_type=party.eci_chart_image_content_type or "image/png",
    )


@router.get("/{party_id}/wordcloud")
def get_party_wordcloud(
    request: Request,
    party_id: int,
    platform: str = Query("twitter", pattern="^(twitter|reddit)$"),
    source_type: str = Query("political", pattern="^(political|public|all)$"),
    days: int = Query(365, ge=1, le=3650),
    language: str = Query("all", pattern="^(all|en|hi)$"),
    v: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Generate and return a party wordcloud image (PNG)."""
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    source_filter = None if source_type == "all" else source_type
    party_key = _resolve_party_wordcloud_key(
        db,
        party,
        platform=platform,
        source_type=source_filter,
        days=days,
    )
    cache_entry = wordcloud_service.get_or_generate_wordcloud(
        db,
        party=party_key,
        platform=platform,
        source_type=source_filter,
        days=days,
        language=language,
        cache_version=v,
    )
    etag = f"\"{cache_entry.etag}\""
    cache_control = "public, max-age=86400, immutable" if v else "public, max-age=3600"
    headers = {
        "Cache-Control": cache_control,
        "ETag": etag,
    }

    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)

    return Response(content=cache_entry.image_bytes, media_type="image/png", headers=headers)


@router.put("/{party_id}", response_model=PartyResponse)
def update_party(
    party_id: int,
    party_update: PartyUpdate,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """Update a party (admin only)."""
    db_party = db.query(Party).filter(Party.id == party_id).first()
    if not db_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    update_data = party_update.dict(
        exclude_unset=True,
        exclude={"logo_url", "eci_chart_image_url"},
    )
    for key, value in update_data.items():
        setattr(db_party, key, value)

    db.commit()
    db.refresh(db_party)
    return db_party


@router.delete("/{party_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_party(
    party_id: int,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """Delete a party (admin only)."""
    db_party = db.query(Party).filter(Party.id == party_id).first()
    if not db_party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    db.delete(db_party)
    db.commit()
    return None


# ========== Party Leader Endpoints ==========

@router.post("/{party_id}/leaders", response_model=PartyLeaderResponse, status_code=status.HTTP_201_CREATED)
def create_party_leader(
    party_id: int,
    leader: PartyLeaderCreate,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """Add a leader to a party (admin only)."""
    # Verify party exists
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    # Override party_id from URL
    leader_data = leader.dict()
    leader_data["party_id"] = party_id

    db_leader = PartyLeader(**leader_data)
    db.add(db_leader)
    db.commit()
    db.refresh(db_leader)
    return db_leader


@router.get("/{party_id}/leaders", response_model=List[PartyLeaderResponse])
def get_party_leaders(party_id: int, db: Session = Depends(get_db)):
    """Get all leaders of a party."""
    # Verify party exists
    party = db.query(Party).filter(Party.id == party_id).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Party with ID {party_id} not found",
        )

    leaders = db.query(PartyLeader).filter(PartyLeader.party_id == party_id).order_by(PartyLeader.display_order).all()

    return leaders


@router.put("/leaders/{leader_id}", response_model=PartyLeaderResponse)
def update_party_leader(
    leader_id: int,
    leader_update: PartyLeaderUpdate,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """Update a party leader (admin only)."""
    db_leader = db.query(PartyLeader).filter(PartyLeader.id == leader_id).first()
    if not db_leader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leader with ID {leader_id} not found",
        )

    update_data = leader_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_leader, key, value)

    db.commit()
    db.refresh(db_leader)
    return db_leader


@router.delete("/leaders/{leader_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_party_leader(
    leader_id: int,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin),
):
    """Delete a party leader (admin only)."""
    db_leader = db.query(PartyLeader).filter(PartyLeader.id == leader_id).first()
    if not db_leader:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Leader with ID {leader_id} not found",
        )

    db.delete(db_leader)
    db.commit()
    return None
