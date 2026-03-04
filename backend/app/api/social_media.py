from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.social_media import RedditPost, SentimentData, TwitterPost
from app.schemas.social_media import (
    SentimentDataCreate,
    SentimentDataResponse,
    SocialPostCreate,
    SocialPostResponse,
)

router = APIRouter(prefix="/social", tags=["Social Media"])


def _get_post_model(platform: str):
    if platform == "twitter":
        return TwitterPost
    if platform == "reddit":
        return RedditPost
    raise HTTPException(status_code=400, detail="platform must be 'twitter' or 'reddit'")


def _serialize_post(post: Any, platform: str) -> Dict[str, Any]:
    return {
        "id": post.id,
        "platform": platform,
        "post_id": post.post_id,
        "content": post.content,
        "leader_name": post.leader_name,
        "party": post.party,
        "username": post.username,
        "source_type": post.source_type,
        "url": post.url,
        "subreddit": getattr(post, "subreddit", None),
        "language": post.language,
        "sentiment_label": post.sentiment_label,
        "sentiment_score": float(post.sentiment_score) if post.sentiment_score is not None else None,
        "likes": post.likes or 0,
        "retweets": post.retweets or 0,
        "replies": post.replies or 0,
        "score": post.score or 0,
        "posted_at": post.posted_at,
        "created_at": post.created_at,
    }


def _build_platform_query(
    db: Session,
    model: Any,
    cutoff_date: datetime,
    party: Optional[str] = None,
    leader_name: Optional[str] = None,
    language: Optional[str] = None,
    sentiment_label: Optional[str] = None,
    source_type: Optional[str] = None,
):
    query = db.query(model).filter(model.posted_at >= cutoff_date)
    if party:
        query = query.filter(model.party == party)
    if leader_name:
        query = query.filter(model.leader_name == leader_name)
    if language:
        query = query.filter(model.language == language)
    if sentiment_label:
        query = query.filter(model.sentiment_label == sentiment_label)
    if source_type:
        query = query.filter(model.source_type == source_type)
    return query


# ========== Social Posts Endpoints ==========


@router.post("/posts", response_model=SocialPostResponse, status_code=status.HTTP_201_CREATED)
def create_social_post(post: SocialPostCreate, db: Session = Depends(get_db)):
    """Create a new social media post (for scrapers/background jobs)."""
    model = _get_post_model(post.platform)

    existing = db.query(model).filter(model.post_id == post.post_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post with ID '{post.post_id}' already exists in {post.platform}",
        )

    payload = post.dict()
    payload.pop("platform")

    if post.platform == "twitter":
        payload.pop("subreddit", None)
    if post.platform == "reddit":
        payload["likes"] = payload.get("likes") or 0
        payload["retweets"] = payload.get("retweets") or 0

    db_post = model(**payload)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return _serialize_post(db_post, post.platform)


@router.get("/posts", response_model=List[SocialPostResponse])
def get_social_posts(
    platform: Optional[str] = Query(None, pattern="^(twitter|reddit)$"),
    source_type: Optional[str] = Query(None, pattern="^(political|public)$"),
    party: Optional[str] = None,
    leader_name: Optional[str] = None,
    language: Optional[str] = None,
    sentiment_label: Optional[str] = None,
    days: int = Query(7, ge=1, le=365, description="Days of history"),
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Get social media posts with platform/source filters."""
    cutoff_date = datetime.now() - timedelta(days=days)

    if platform:
        model = _get_post_model(platform)
        posts = (
            _build_platform_query(
                db,
                model,
                cutoff_date,
                party=party,
                leader_name=leader_name,
                language=language,
                sentiment_label=sentiment_label,
                source_type=source_type,
            )
            .order_by(desc(model.posted_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_serialize_post(post, platform) for post in posts]

    fetch_limit = skip + limit
    twitter_posts = (
        _build_platform_query(
            db,
            TwitterPost,
            cutoff_date,
            party=party,
            leader_name=leader_name,
            language=language,
            sentiment_label=sentiment_label,
            source_type=source_type,
        )
        .order_by(desc(TwitterPost.posted_at))
        .limit(fetch_limit)
        .all()
    )
    reddit_posts = (
        _build_platform_query(
            db,
            RedditPost,
            cutoff_date,
            party=party,
            leader_name=leader_name,
            language=language,
            sentiment_label=sentiment_label,
            source_type=source_type,
        )
        .order_by(desc(RedditPost.posted_at))
        .limit(fetch_limit)
        .all()
    )

    merged = [_serialize_post(post, "twitter") for post in twitter_posts] + [
        _serialize_post(post, "reddit") for post in reddit_posts
    ]
    merged.sort(key=lambda post: post["posted_at"], reverse=True)
    return merged[skip : skip + limit]


@router.get("/posts/{post_id}", response_model=SocialPostResponse)
def get_social_post(
    post_id: int,
    platform: Optional[str] = Query(None, pattern="^(twitter|reddit)$"),
    db: Session = Depends(get_db),
):
    """Get a specific social post by DB ID. Use platform to avoid cross-table ID ambiguity."""
    if platform:
        model = _get_post_model(platform)
        post = db.query(model).filter(model.id == post_id).first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post with ID {post_id} not found in {platform}",
            )
        return _serialize_post(post, platform)

    twitter_post = db.query(TwitterPost).filter(TwitterPost.id == post_id).first()
    reddit_post = db.query(RedditPost).filter(RedditPost.id == post_id).first()

    if twitter_post and reddit_post:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Post ID exists in both twitter and reddit tables. Pass ?platform=twitter|reddit.",
        )
    if twitter_post:
        return _serialize_post(twitter_post, "twitter")
    if reddit_post:
        return _serialize_post(reddit_post, "reddit")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Post with ID {post_id} not found",
    )


# ========== Sentiment Data Endpoints ==========


@router.post("/sentiment", response_model=SentimentDataResponse, status_code=status.HTTP_201_CREATED)
def create_sentiment_data(sentiment: SentimentDataCreate, db: Session = Depends(get_db)):
    """Create sentiment data entry (for background jobs)."""
    db_sentiment = SentimentData(**sentiment.dict())
    db.add(db_sentiment)
    db.commit()
    db.refresh(db_sentiment)
    return db_sentiment


@router.get("/sentiment", response_model=List[SentimentDataResponse])
def get_sentiment_data(
    entity_name: str = Query(..., description="Name of leader or party"),
    entity_type: str = Query("party", pattern="^(leader|party)$"),
    language: Optional[str] = None,
    source: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get sentiment data for time-series analysis."""
    cutoff_date = datetime.now() - timedelta(days=days)

    query = db.query(SentimentData).filter(
        and_(
            SentimentData.entity_name == entity_name,
            SentimentData.entity_type == entity_type,
            SentimentData.date >= cutoff_date,
        )
    )

    if language:
        query = query.filter(SentimentData.language == language)
    if source:
        query = query.filter(SentimentData.source == source)

    sentiments = query.order_by(SentimentData.date.desc()).all()

    if not sentiments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sentiment data found for {entity_type} '{entity_name}'",
        )

    return sentiments


@router.get("/sentiment/latest")
def get_latest_sentiment(
    entity_name: str = Query(..., description="Name of leader or party"),
    entity_type: str = Query("party", pattern="^(leader|party)$"),
    language: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get the most recent sentiment score for an entity."""
    query = db.query(SentimentData).filter(
        and_(
            SentimentData.entity_name == entity_name,
            SentimentData.entity_type == entity_type,
        )
    )

    if language:
        query = query.filter(SentimentData.language == language)

    sentiment = query.order_by(desc(SentimentData.date)).first()

    if not sentiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No sentiment data found for {entity_type} '{entity_name}'",
        )

    return {
        "entity_name": sentiment.entity_name,
        "entity_type": sentiment.entity_type,
        "sentiment_score": float(sentiment.sentiment_score),
        "language": sentiment.language,
        "date": sentiment.date,
        "source": sentiment.source,
        "sample_size": sentiment.sample_size,
    }


@router.get("/trending/{platform}")
def get_trending_topics(
    platform: str = Path(..., pattern="^(twitter|reddit)$"),
    source_type: Optional[str] = Query(None, pattern="^(political|public)$"),
    days: int = Query(1, ge=1, le=7),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    """Get trending topics/leaders based on engagement."""
    model = _get_post_model(platform)
    cutoff_date = datetime.now() - timedelta(days=days)

    query = db.query(model).filter(model.posted_at >= cutoff_date)
    if source_type:
        query = query.filter(model.source_type == source_type)

    posts = query.order_by(
        desc(model.likes + model.retweets + model.replies + model.score)
    ).limit(limit).all()

    return {
        "platform": platform,
        "source_type": source_type or "all",
        "period_days": days,
        "trending_posts": [
            {
                "id": post.id,
                "leader_name": post.leader_name,
                "party": post.party,
                "source_type": post.source_type,
                "content": post.content[:200],
                "engagement": (post.likes or 0) + (post.retweets or 0) + (post.replies or 0) + (post.score or 0),
                "posted_at": post.posted_at,
                "url": post.url,
            }
            for post in posts
        ],
    }
