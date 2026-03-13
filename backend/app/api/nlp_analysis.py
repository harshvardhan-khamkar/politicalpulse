from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.social_media import TwitterPost, RedditPost
from app.models.events_topics import TopicData
from app.services.topic_modeling_service import topic_modeling_service
from app.services.alignment_model_service import alignment_model_service

router = APIRouter(prefix="/nlp", tags=["NLP Analysis"])

@router.get("/topics")
def get_current_topics(
    days: int = Query(7, ge=1, le=30),
    platform: Optional[str] = Query("all", pattern="^(twitter|reddit|all)$"),
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Extract current topics from recent social media posts using NMF.
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    texts = []
    
    # Gather texts
    if platform in ("all", "twitter"):
        tw_posts = db.query(TwitterPost.content).filter(TwitterPost.posted_at >= cutoff_date).limit(2000).all()
        texts.extend([p[0] for p in tw_posts if p[0]])
        
    if platform in ("all", "reddit"):
        rd_posts = db.query(RedditPost.content).filter(RedditPost.posted_at >= cutoff_date).limit(2000).all()
        texts.extend([p[0] for p in rd_posts if p[0]])
        
    if not texts:
        raise HTTPException(status_code=404, detail="Not enough recent posts to extract topics.")
        
    # Run extraction
    topics = topic_modeling_service.extract_topics(texts, num_topics=limit)
    
    # Store extraction results
    stored_topics = []
    for t in topics:
        db_topic = TopicData(
            topic_name=t["topic_name"],
            keywords=",".join(t["keywords"]),
            start_date=cutoff_date,
            end_date=datetime.now(),
            salience_score=t["salience_score"],
            document_count=len(texts)
        )
        db.add(db_topic)
        stored_topics.append(db_topic)
        
    db.commit()
    
    return {
        "timeframe_days": days,
        "platform": platform,
        "document_count": len(texts),
        "topics": topics
    }

@router.post("/alignment/train")
def train_alignment_model(db: Session = Depends(get_db)):
    """
    Manually trigger retraining of the political alignment classifier 
    using official handler posts.
    """
    result = alignment_model_service.train_model(db)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/alignment/predict")
def predict_alignment(text: str = Query(..., min_length=10)):
    """
    Predict alignment for a given text payload.
    """
    if not alignment_model_service.initialized:
        raise HTTPException(status_code=500, detail="Model is not trained/initialized yet. Call /alignment/train first.")
        
    result = alignment_model_service.predict_alignment(text)
    return result
