from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.predictions_news import Prediction
from app.schemas.predictions_news import (
    CachedNewsResponse,
    PredictionCreate,
    PredictionResponse,
)
from app.services.news_service import news_service

router_predictions = APIRouter(prefix="/predictions", tags=["Predictions"])
router_news = APIRouter(prefix="/news", tags=["News"])


# ========== Predictions Endpoints ==========


@router_predictions.post("/", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(prediction: PredictionCreate, db: Session = Depends(get_db)):
    """Create a new prediction (for ML background jobs)"""
    db_prediction = Prediction(**prediction.dict())
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction


@router_predictions.get("/", response_model=List[PredictionResponse])
def get_predictions(
    prediction_type: Optional[str] = Query(None, pattern="^(pm_candidate|party_seats|constituency)$"),
    party: Optional[str] = None,
    state_name: Optional[str] = None,
    valid_only: bool = Query(True, description="Only return valid predictions"),
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Get predictions with filters"""
    query = db.query(Prediction)

    if prediction_type:
        query = query.filter(Prediction.prediction_type == prediction_type)
    if party:
        query = query.filter(Prediction.party == party)
    if state_name:
        query = query.filter(Prediction.state_name == state_name)
    if valid_only:
        now = datetime.now()
        query = query.filter((Prediction.valid_until.is_(None)) | (Prediction.valid_until >= now))

    predictions = query.order_by(desc(Prediction.prediction_date)).offset(skip).limit(limit).all()
    return predictions


@router_predictions.get("/pm-race", response_model=List[PredictionResponse])
def get_pm_candidates(db: Session = Depends(get_db)):
    """Get PM candidate predictions"""
    now = datetime.now()
    predictions = (
        db.query(Prediction)
        .filter(
            and_(
                Prediction.prediction_type == "pm_candidate",
                (Prediction.valid_until.is_(None)) | (Prediction.valid_until >= now),
            )
        )
        .order_by(desc(Prediction.predicted_win_rate))
        .all()
    )

    return predictions


@router_predictions.get("/seats-projection", response_model=List[PredictionResponse])
def get_seats_projection(db: Session = Depends(get_db)):
    """Get party seats projection"""
    now = datetime.now()
    predictions = (
        db.query(Prediction)
        .filter(
            and_(
                Prediction.prediction_type == "party_seats",
                (Prediction.valid_until.is_(None)) | (Prediction.valid_until >= now),
            )
        )
        .order_by(desc(Prediction.predicted_seats))
        .all()
    )

    return predictions


# ========== News Endpoints ==========


@router_news.get("/local", response_model=CachedNewsResponse)
def get_local_news():
    try:
        return news_service.get_category_news("india_politics")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router_news.get("/global", response_model=CachedNewsResponse)
def get_global_news():
    try:
        return news_service.get_category_news("geopolitics")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
