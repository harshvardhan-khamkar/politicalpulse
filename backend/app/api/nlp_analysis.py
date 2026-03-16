from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.social_media import TwitterPost, RedditPost
from app.models.events_topics import TopicData
from app.services.advanced_ml_service import advanced_ml_service
from app.services.text_normalization import repair_mojibake
from app.services.topic_modeling_service import topic_modeling_service
from app.services.alignment_model_service import alignment_model_service

router = APIRouter(prefix="/nlp", tags=["NLP Analysis"])


def _fetch_recent_posts(
    db: Session,
    days: int,
    platform: str = "all",
    limit: int = 120,
):
    cutoff_date = datetime.now() - timedelta(days=days)

    def _fetch_platform(model, platform_name: str):
        return [
            {
                "post_id": post.post_id,
                "content": post.content,
                "platform": platform_name,
                "party": post.party,
                "source_type": post.source_type,
                "posted_at": post.posted_at,
            }
            for post in (
                db.query(model)
                .filter(model.posted_at >= cutoff_date)
                .order_by(desc(model.posted_at))
                .limit(limit)
                .all()
            )
        ]

    if platform == "twitter":
        return _fetch_platform(TwitterPost, "twitter")
    if platform == "reddit":
        return _fetch_platform(RedditPost, "reddit")

    twitter_posts = _fetch_platform(TwitterPost, "twitter")
    reddit_posts = _fetch_platform(RedditPost, "reddit")
    merged = twitter_posts + reddit_posts
    merged.sort(key=lambda post: post["posted_at"], reverse=True)
    return merged[:limit]

@router.get("/topics")
def get_current_topics(
    days: int = Query(7, ge=1, le=30),
    platform: Optional[str] = Query("all", pattern="^(twitter|reddit|all)$"),
    limit: int = 5,
    model: str = Query("advanced", pattern="^(basic|advanced)$"),
    document_limit: int = Query(120, ge=20, le=300),
    db: Session = Depends(get_db)
):
    """
    Extract current topics from recent social media posts.
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    if model == "advanced":
        posts = _fetch_recent_posts(db, days=days, platform=platform, limit=document_limit)
        if not posts:
            raise HTTPException(status_code=404, detail="Not enough recent posts to extract advanced topics.")

        result = advanced_ml_service.analyze_posts(
            db,
            posts=posts,
            topic_limit=limit,
            sample_limit=0,
        )
        if not result.get("available"):
            raise HTTPException(
                status_code=503,
                detail=result.get("error") or "Advanced ML pipeline is unavailable",
            )

        return {
            "timeframe_days": days,
            "platform": platform,
            "document_count": result["document_count"],
            "topics": result["topics"],
            "model_used": "advanced",
        }

    texts = []

    if platform in ("all", "twitter"):
        tw_posts = db.query(TwitterPost.content).filter(TwitterPost.posted_at >= cutoff_date).limit(2000).all()
        texts.extend([repair_mojibake(p[0]) for p in tw_posts if p[0]])

    if platform in ("all", "reddit"):
        rd_posts = db.query(RedditPost.content).filter(RedditPost.posted_at >= cutoff_date).limit(2000).all()
        texts.extend([repair_mojibake(p[0]) for p in rd_posts if p[0]])

    if not texts:
        raise HTTPException(status_code=404, detail="Not enough recent posts to extract topics.")

    topics = topic_modeling_service.extract_topics(texts, num_topics=limit)

    for t in topics:
        db.add(
            TopicData(
                topic_name=t["topic_name"],
                keywords=",".join(t["keywords"]),
                start_date=cutoff_date,
                end_date=datetime.now(),
                salience_score=t["salience_score"],
                document_count=len(texts),
            )
        )

    db.commit()

    return {
        "timeframe_days": days,
        "platform": platform,
        "document_count": len(texts),
        "topics": topics,
        "model_used": "basic",
    }


@router.get("/advanced-analysis")
def get_advanced_analysis(
    days: int = Query(7, ge=1, le=30),
    platform: Optional[str] = Query("all", pattern="^(twitter|reddit|all)$"),
    document_limit: int = Query(120, ge=20, le=300),
    topic_limit: int = Query(5, ge=1, le=12),
    sample_limit: int = Query(12, ge=0, le=30),
    db: Session = Depends(get_db),
):
    """
    Run the advanced batch ML pipeline over recent posts.
    """
    posts = _fetch_recent_posts(db, days=days, platform=platform, limit=document_limit)
    if not posts:
        raise HTTPException(status_code=404, detail="Not enough recent posts to analyze.")

    result = advanced_ml_service.analyze_posts(
        db,
        posts=posts,
        topic_limit=topic_limit,
        sample_limit=sample_limit,
    )
    if not result.get("available"):
        raise HTTPException(
            status_code=503,
            detail=result.get("error") or "Advanced ML pipeline is unavailable",
        )

    return {
        "timeframe_days": days,
        "platform": platform,
        "model_used": "advanced",
        **result,
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
