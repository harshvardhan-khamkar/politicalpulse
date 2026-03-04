from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List
from app.database import get_db
from app.models.elections import ElectionResult
from app.schemas.elections import (
    ElectionResultResponse,
    StatesList,
    ConstituenciesList,
    YearsList,
    ElectionStats
)

router = APIRouter(prefix="/elections", tags=["Elections"])


@router.get("/states", response_model=StatesList)
def get_states(db: Session = Depends(get_db)):
    """Get list of all states"""
    states = db.query(distinct(ElectionResult.state_name))\
        .order_by(ElectionResult.state_name)\
        .all()
    return {"states": [s[0] for s in states]}


@router.get("/constituencies", response_model=ConstituenciesList)
def get_constituencies(
    state: str = Query(..., description="State name"),
    db: Session = Depends(get_db)
):
    """Get list of constituencies for a state"""
    constituencies = db.query(distinct(ElectionResult.constituency_name))\
        .filter(ElectionResult.state_name == state)\
        .order_by(ElectionResult.constituency_name)\
        .all()

    return {"constituencies": [c[0] for c in constituencies]}


@router.get("/years", response_model=YearsList)
def get_years(db: Session = Depends(get_db)):
    """Get list of all election years"""
    years = db.query(distinct(ElectionResult.year))\
        .order_by(ElectionResult.year.desc())\
        .all()
    return {"years": [y[0] for y in years]}


@router.get("/results", response_model=List[ElectionResultResponse])
def get_results(
    state: str = Query(..., description="State name"),
    constituency: str = Query(..., description="Constituency name"),
    year: int = Query(..., description="Election year"),
    db: Session = Depends(get_db)
):
    """
    Get election results for specific state, constituency, and year.
    Results are ordered by position (winner first).
    """
    results = db.query(ElectionResult).filter(
        ElectionResult.state_name == state,
        ElectionResult.constituency_name == constituency,
        ElectionResult.year == year
    ).order_by(ElectionResult.position).all()

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for {constituency}, {state} in {year}"
        )

    return results


@router.get("/stats", response_model=ElectionStats)
def get_stats(db: Session = Depends(get_db)):
    """Get overall election statistics"""
    total_constituencies = db.query(
        func.count(distinct(ElectionResult.constituency_name))
    ).scalar()

    total_candidates = db.query(func.count(ElectionResult.id)).scalar()

    total_votes = db.query(func.sum(ElectionResult.votes_secured)).scalar()

    avg_turnout = db.query(func.avg(ElectionResult.turnout)).scalar()

    return {
        "total_constituencies": total_constituencies,
        "total_candidates": total_candidates,
        "total_votes": int(total_votes) if total_votes else 0,
        "average_turnout": float(avg_turnout) if avg_turnout else 0.0
    }