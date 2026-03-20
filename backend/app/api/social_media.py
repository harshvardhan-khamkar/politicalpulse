from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.social_media import RedditPost, SentimentData, TwitterPost
from app.services.text_normalization import repair_mojibake
from app.schemas.social_media import (
    SentimentDataCreate,
    SentimentDataResponse,
    SocialPostCreate,
    SocialPostResponse,
)
from pydantic import BaseModel

class PublicReactionSummary(BaseModel):
    positive: int = 0
    negative: int = 0
    neutral:  int = 0
    total:    int = 0

class PartyPublicSentimentResponse(BaseModel):
    party: str
    public_reaction_summary: PublicReactionSummary
    avg_public_score: float
    tweet_count: int

class TweetReplyResponse(BaseModel):
    reply_id:              str
    reply_username:        Optional[str]
    reply_content:         str
    reply_sentiment_label: Optional[str]
    reply_sentiment_score: Optional[float]
    reply_likes:           int
    reply_posted_at:       Optional[datetime]
    party:                 Optional[str]
    leader_name:           Optional[str]

    class Config:
        from_attributes = True

class PublicTimelinePoint(BaseModel):
    date:      str
    positive:  int
    negative:  int
    neutral:   int
    total:     int
    avg_score: float

class PaginatedRepliesResponse(BaseModel):
    items:    List[TweetReplyResponse]
    total:    int
    has_more: bool
    page:     int

router = APIRouter(prefix="/social", tags=["Social Media"])
logger = logging.getLogger(__name__)
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
        "content": repair_mojibake(post.content),
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
    username: Optional[str] = None,
    language: Optional[str] = None,
    sentiment_label: Optional[str] = None,
    source_type: Optional[str] = None,
):
    query = db.query(model).filter(model.posted_at >= cutoff_date)
    if party:
        query = query.filter(model.party == party)
    leader_filters = []
    if leader_name:
        normalized_name = leader_name.strip().lower()
        normalized_handle = leader_name.strip().lstrip("@").lower()
        leader_filters.extend(
            [
                func.lower(model.leader_name) == normalized_name,
                func.lower(model.leader_name) == normalized_handle,
                func.lower(model.username) == normalized_handle,
            ]
        )
    if username:
        normalized_username = username.strip().lstrip("@").lower()
        leader_filters.append(func.lower(model.username) == normalized_username)
    if leader_filters:
        query = query.filter(or_(*leader_filters))
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
    payload["content"] = repair_mojibake(payload.get("content"))

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
    username: Optional[str] = None,
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
                username=username,
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
            username=username,
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
            username=username,
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

@router.get("/posts/replies", response_model=PaginatedRepliesResponse)
def get_paginated_replies(
    party: Optional[str] = Query(None),
    reply_sentiment_label: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    from app.models.social_media import TweetReply

    query = db.query(TweetReply, TwitterPost).outerjoin(
        TwitterPost, TweetReply.parent_post_id == TwitterPost.post_id
    )

    if party:
        query = query.filter(TwitterPost.party == party.upper())
    
    if reply_sentiment_label and reply_sentiment_label.lower() != 'all':
        query = query.filter(TweetReply.reply_sentiment_label == reply_sentiment_label.lower())
    
    total_count = query.count()
    offset = (page - 1) * limit
    results = query.order_by(desc(TweetReply.reply_likes)).offset(offset).limit(limit).all()

    items = []
    for reply, post in results:
        items.append(TweetReplyResponse(
            reply_id=reply.reply_id,
            reply_username=reply.reply_username,
            reply_content=reply.reply_content,
            reply_sentiment_label=reply.reply_sentiment_label,
            reply_sentiment_score=float(reply.reply_sentiment_score) if reply.reply_sentiment_score is not None else None,
            reply_likes=reply.reply_likes or 0,
            reply_posted_at=reply.reply_posted_at,
            party=post.party if post else None,
            leader_name=post.leader_name if post else None
        ))
    
    return PaginatedRepliesResponse(
        items=items,
        total=total_count,
        has_more=(offset + limit) < total_count,
        page=page
    )


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


@router.get("/trending/hashtags")
async def get_trending_hashtags(
    days: int = Query(1, ge=1, le=30, description="Days to look back"),
    limit: int = Query(15, ge=5, le=50, description="Number of hashtags to return"),
    party: Optional[str] = None,
    language: Optional[str] = None,
    source_type: Optional[str] = Query(None, pattern="^(political|public)$"),
    live: bool = Query(False, description="When true, fetch live Twitter/X trends instead of DB-ranked hashtags."),
    country_code: str = Query("IN", min_length=2, max_length=2, description="Country code for live Twitter trends."),
    location_name: Optional[str] = Query(None, description="Optional location name for live Twitter place trends."),
    hashtags_only: bool = Query(True, description="Only return names beginning with # for live Twitter trends."),
    db: Session = Depends(get_db),
):
    """
    Get trending hashtags.

    Modes:
    - live=false: extract from stored tweets in the local DB
    - live=true: fetch live trends directly from Twitter/X and fall back to DB data if needed

    Stored-tweet ranking parses #tag tokens from tweet content and ranks by:
    - frequency (count of tweets containing the tag)
    - engagement (likes + retweets + replies)
    """
    from app.services.twitter_service import twitter_service

    if live:
        try:
            live_payload = await twitter_service.get_live_trending_hashtags(
                country_code=country_code,
                location_name=location_name,
                count=limit,
                hashtags_only=hashtags_only,
            )
            live_payload.update(
                {
                    "period_days": None,
                    "party_filter": None,
                    "language_filter": None,
                    "count": len(live_payload.get("hashtags", [])),
                    "fallback_reason": None,
                }
            )
            return live_payload
        except Exception as exc:
            logger.warning(f"Live Twitter trends unavailable, falling back to stored hashtags: {exc}")
            trending = twitter_service.get_trending_hashtags(
                db,
                days=days,
                limit=limit,
                party=party,
                language=language,
                source_type=source_type,
            )
            return {
                "source": "stored_tweets_fallback",
                "is_live": False,
                "location": None,
                "period_days": days,
                "party_filter": party,
                "language_filter": language,
                "count": len(trending),
                "hashtags": trending,
                "fallback_reason": str(exc),
            }

    trending = twitter_service.get_trending_hashtags(
        db,
        days=days,
        limit=limit,
        party=party,
        language=language,
        source_type=source_type,
    )
    return {
        "source": "stored_tweets",
        "is_live": False,
        "location": None,
        "period_days": days,
        "party_filter": party,
        "language_filter": language,
        "count": len(trending),
        "hashtags": trending,
        "fallback_reason": None,
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
                "content": repair_mojibake(post.content)[:200],
                "engagement": (post.likes or 0) + (post.retweets or 0) + (post.replies or 0) + (post.score or 0),
                "posted_at": post.posted_at,
                "url": post.url,
            }
            for post in posts
        ],
    }



# ─── Reply Analysis Endpoints ─────────────────────────────────────────────────

@router.get("/sentiment/public-comparison", response_model=List[PartyPublicSentimentResponse])
def get_public_sentiment_comparison(
    party: Optional[str] = Query(None, description="Filter by party"),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func, cast, Integer
    from sqlalchemy.dialects.postgresql import JSONB

    cutoff = datetime.now() - timedelta(days=days)
    query = db.query(
        TwitterPost.party,
        func.sum(cast(TwitterPost.public_reaction_summary['positive'].astext, Integer)).label('positive'),
        func.sum(cast(TwitterPost.public_reaction_summary['negative'].astext, Integer)).label('negative'),
        func.sum(cast(TwitterPost.public_reaction_summary['neutral'].astext, Integer)).label('neutral'),
        func.sum(cast(TwitterPost.public_reaction_summary['total'].astext, Integer)).label('total'),
        func.avg(TwitterPost.public_sentiment_score).label('avg_score'),
        func.count().label('tweet_count')
    ).filter(
        TwitterPost.replies_fetched == True,
        TwitterPost.posted_at >= cutoff
    )

    if party:
        query = query.filter(TwitterPost.party == party.upper())

    results = query.group_by(TwitterPost.party).all()

    response = []
    for r in results:
        pos = r.positive or 0
        neg = r.negative or 0
        neu = r.neutral or 0
        tot = r.total or 0
        
        response.append(PartyPublicSentimentResponse(
            party=r.party or "Unknown",
            public_reaction_summary=PublicReactionSummary(
                positive=pos, negative=neg, neutral=neu, total=tot
            ),
            avg_public_score=float(r.avg_score) if r.avg_score is not None else 0.0,
            tweet_count=r.tweet_count or 0
        ))
    
    response.sort(key=lambda x: x.tweet_count, reverse=True)
    return response

@router.get("/sentiment/public-timeline", response_model=List[PublicTimelinePoint])
def get_public_timeline(
    party: str = Query(...),
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func, cast, Integer, Date
    cutoff = datetime.now() - timedelta(days=days)

    query = db.query(
        func.date(TwitterPost.posted_at).label('date'),
        func.sum(cast(TwitterPost.public_reaction_summary['positive'].astext, Integer)).label('positive'),
        func.sum(cast(TwitterPost.public_reaction_summary['negative'].astext, Integer)).label('negative'),
        func.sum(cast(TwitterPost.public_reaction_summary['neutral'].astext, Integer)).label('neutral'),
        func.sum(cast(TwitterPost.public_reaction_summary['total'].astext, Integer)).label('total'),
        func.avg(TwitterPost.public_sentiment_score).label('avg_score')
    ).filter(
        TwitterPost.party == party.upper(),
        TwitterPost.replies_fetched == True,
        TwitterPost.posted_at >= cutoff
    ).group_by(func.date(TwitterPost.posted_at)).order_by(func.date(TwitterPost.posted_at).asc())

    results = query.all()

    points = []
    for r in results:
        points.append(PublicTimelinePoint(
            date=str(r.date),
            positive=r.positive or 0,
            negative=r.negative or 0,
            neutral=r.neutral or 0,
            total=r.total or 0,
            avg_score=float(r.avg_score) if r.avg_score is not None else 0.0
        ))

    return points
