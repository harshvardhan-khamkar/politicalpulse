from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.polls import Poll, PollVote
from app.models.users import AppUser
from app.schemas.polls import (
    PollCreate, PollUpdate, PollResponse,
    VoteCreate, VoteResponse, PollResults
)
from app.security import get_current_admin, get_current_user

router = APIRouter(prefix="/polls", tags=["Polls"])


@router.post("/", response_model=PollResponse, status_code=status.HTTP_201_CREATED)
def create_poll(
    poll: PollCreate,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin)
):
    """Create a new poll (admin only)."""
    db_poll = Poll(
        title=poll.title,
        description=poll.description,
        poll_type=poll.poll_type,
        options=[opt.dict() for opt in poll.options],  # Convert to dict for JSON storage
        ends_at=poll.ends_at,
        is_active=1
    )
    db.add(db_poll)
    db.commit()
    db.refresh(db_poll)

    # Add vote_count
    db_poll.vote_count = 0
    return db_poll


@router.get("/", response_model=List[PollResponse])
def get_polls(
    is_active: int = None,
    poll_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all polls with optional filters"""
    query = db.query(Poll)

    if is_active is not None:
        query = query.filter(Poll.is_active == is_active)
    if poll_type:
        query = query.filter(Poll.poll_type == poll_type)

    polls = query.order_by(Poll.created_at.desc()).offset(skip).limit(limit).all()

    # Add vote counts
    for poll in polls:
        vote_count = db.query(func.count(PollVote.id)).filter(PollVote.poll_id == poll.id).scalar()
        poll.vote_count = vote_count

    return polls


@router.get("/{poll_id}", response_model=PollResponse)
def get_poll(poll_id: int, db: Session = Depends(get_db)):
    """Get a specific poll by ID"""
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poll with ID {poll_id} not found"
        )

    # Add vote count
    vote_count = db.query(func.count(PollVote.id)).filter(PollVote.poll_id == poll.id).scalar()
    poll.vote_count = vote_count

    return poll


@router.put("/{poll_id}", response_model=PollResponse)
def update_poll(
    poll_id: int,
    poll_update: PollUpdate,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin)
):
    """Update a poll (admin only)."""
    db_poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not db_poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poll with ID {poll_id} not found"
        )

    update_data = poll_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_poll, key, value)

    db.commit()
    db.refresh(db_poll)

    # Add vote count
    vote_count = db.query(func.count(PollVote.id)).filter(PollVote.poll_id == db_poll.id).scalar()
    db_poll.vote_count = vote_count

    return db_poll


@router.delete("/{poll_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_poll(
    poll_id: int,
    db: Session = Depends(get_db),
    _current_admin: AppUser = Depends(get_current_admin)
):
    """Delete a poll (admin only)."""
    db_poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not db_poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poll with ID {poll_id} not found"
        )

    db.delete(db_poll)
    db.commit()
    return None


@router.post("/{poll_id}/vote", response_model=VoteResponse, status_code=status.HTTP_201_CREATED)
def vote_on_poll(
    poll_id: int,
    vote: VoteCreate,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Cast a vote on a poll (one vote per user per poll)."""
    # Check if poll exists and is active
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poll with ID {poll_id} not found"
        )

    if poll.is_active != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This poll is closed"
        )

    # Validate option_id exists in poll options
    option_ids = [opt['id'] for opt in poll.options]
    if vote.option_id not in option_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid option ID: {vote.option_id}"
        )

    voter_info = f"user:{current_user.id}"

    # Enforce one vote per user per poll.
    existing_vote = db.query(PollVote).filter(
        PollVote.poll_id == poll_id,
        PollVote.voter_info == voter_info,
    ).first()
    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User has already voted on this poll",
        )

    db_vote = PollVote(
        poll_id=poll_id,
        option_id=vote.option_id,
        voter_info=voter_info,
    )
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)

    return db_vote


@router.get("/{poll_id}/results", response_model=PollResults)
def get_poll_results(poll_id: int, db: Session = Depends(get_db)):
    """Get poll results with vote counts and percentages"""
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poll with ID {poll_id} not found"
        )

    # Get total votes
    total_votes = db.query(func.count(PollVote.id)).filter(PollVote.poll_id == poll_id).scalar()

    # Count votes per option
    vote_counts = db.query(
        PollVote.option_id,
        func.count(PollVote.id).label('count')
    ).filter(PollVote.poll_id == poll_id).group_by(PollVote.option_id).all()

    # Create results dict
    vote_dict = {opt_id: count for opt_id, count in vote_counts}

    # Build results
    results = []
    for option in poll.options:
        option_id = option['id']
        votes = vote_dict.get(option_id, 0)
        percentage = (votes / total_votes * 100) if total_votes > 0 else 0.0

        results.append({
            "option_id": option_id,
            "text": option['text'],
            "votes": votes,
            "percentage": round(percentage, 2)
        })

    return {
        "poll_id": poll_id,
        "title": poll.title,
        "total_votes": total_votes,
        "results": results
    }
