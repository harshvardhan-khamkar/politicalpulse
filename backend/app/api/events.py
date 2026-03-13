from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.events_topics import PoliticalEvent
from app.services.event_correlation_service import event_correlation_service

router = APIRouter(prefix="/events", tags=["Political Events"])

class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    date: date
    keywords: Optional[str] = None
    impact_score: Optional[float] = 0.0

@router.get("/")
def get_events(limit: int = 20, db: Session = Depends(get_db)):
    events = db.query(PoliticalEvent).order_by(desc(PoliticalEvent.date)).limit(limit).all()
    return events

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = PoliticalEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/{event_id}/discourse-shift")
def get_discourse_shift(event_id: int, window_days: int = 7, db: Session = Depends(get_db)):
    """
    Get correlation analytics for sentiment/volume shifts around a specific event.
    """
    result = event_correlation_service.analyze_event_impact(db, event_id, window_days)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result
