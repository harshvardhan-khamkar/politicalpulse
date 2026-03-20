"""
Admin API
Endpoints for triggering background jobs manually
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import logging

from app.database import get_db
from app.security import get_current_admin
from app.services.twitter_service import twitter_service
from app.services.reddit_service import reddit_service
from app.services.wordcloud_service import wordcloud_service
from app.services.news_service import news_service
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin)],
)


def _extract_new_inserted_count(payload: Any) -> int:
    """Recursively sum 'new_inserted' counters from scrape result payloads."""
    if isinstance(payload, dict):
        total = int(payload.get("new_inserted", 0)) if str(payload.get("new_inserted", "")).isdigit() else 0
        for value in payload.values():
            total += _extract_new_inserted_count(value)
        return total

    if isinstance(payload, list):
        return sum(_extract_new_inserted_count(item) for item in payload)

    return 0


def _collect_admin_metrics(db: Session) -> Dict[str, Any]:
    """Collect dashboard metrics for admin status visibility."""
    from app.models.users import AppUser
    from app.models.polls import Poll, PollVote
    from app.models.parties import Party, PartyLeader
    from app.models.social_media import TwitterPost, RedditPost
    from app.models.predictions_news import Prediction
    from app.models.elections import ElectionResult

    now = datetime.utcnow()
    recent_window = now - timedelta(days=7)

    users_total = db.query(func.count(AppUser.id)).scalar() or 0
    users_active = db.query(func.count(AppUser.id)).filter(AppUser.is_active == 1).scalar() or 0
    users_admin = db.query(func.count(AppUser.id)).filter(AppUser.role == "admin").scalar() or 0
    users_recent = (
        db.query(func.count(AppUser.id))
        .filter(AppUser.created_at.isnot(None), AppUser.created_at >= recent_window)
        .scalar()
        or 0
    )

    polls_total = db.query(func.count(Poll.id)).scalar() or 0
    polls_active = db.query(func.count(Poll.id)).filter(Poll.is_active == 1).scalar() or 0
    poll_votes_total = db.query(func.count(PollVote.id)).scalar() or 0

    parties_total = db.query(func.count(Party.id)).scalar() or 0
    leaders_total = db.query(func.count(PartyLeader.id)).scalar() or 0
    parties_with_logo = db.query(func.count(Party.id)).filter(Party.logo_image_data.isnot(None)).scalar() or 0
    parties_with_eci_chart = (
        db.query(func.count(Party.id)).filter(Party.eci_chart_image_data.isnot(None)).scalar() or 0
    )

    twitter_posts_total = db.query(func.count(TwitterPost.id)).scalar() or 0
    reddit_posts_total = db.query(func.count(RedditPost.id)).scalar() or 0
    pending_twitter_sentiment = (
        db.query(func.count(TwitterPost.id)).filter(TwitterPost.sentiment_label.is_(None)).scalar() or 0
    )
    pending_reddit_sentiment = (
        db.query(func.count(RedditPost.id)).filter(RedditPost.sentiment_label.is_(None)).scalar() or 0
    )
    latest_twitter_post = db.query(func.max(TwitterPost.posted_at)).scalar()
    latest_reddit_post = db.query(func.max(RedditPost.posted_at)).scalar()

    predictions_total = db.query(func.count(Prediction.id)).scalar() or 0
    valid_predictions = (
        db.query(func.count(Prediction.id))
        .filter((Prediction.valid_until.is_(None)) | (Prediction.valid_until >= now))
        .scalar()
        or 0
    )
    predictions_by_type = {
        row[0]: row[1]
        for row in db.query(Prediction.prediction_type, func.count(Prediction.id))
        .group_by(Prediction.prediction_type)
        .all()
    }

    # Election table can be very large; still useful for admin visibility.
    election_results_total = db.query(func.count(ElectionResult.id)).scalar() or 0
    election_states_total = db.query(func.count(func.distinct(ElectionResult.state_name))).scalar() or 0
    election_years_total = db.query(func.count(func.distinct(ElectionResult.year))).scalar() or 0

    news_cache_metrics: Dict[str, Dict[str, Any]] = {}
    for category in ("india_politics", "geopolitics"):
        cache_entry = news_service.news_cache.get(category, {"articles": [], "last_updated": None})
        try:
            is_expired = news_service._is_cache_expired(category)
        except Exception:
            is_expired = None

        news_cache_metrics[category] = {
            "count": len(cache_entry.get("articles", [])),
            "last_updated": cache_entry.get("last_updated"),
            "is_expired": is_expired,
        }

    return {
        "users": {
            "total": users_total,
            "active": users_active,
            "admins": users_admin,
            "regular_users": max(users_total - users_admin, 0),
            "registered_last_7_days": users_recent,
        },
        "polls": {
            "total": polls_total,
            "active": polls_active,
            "closed": max(polls_total - polls_active, 0),
            "total_votes": poll_votes_total,
        },
        "parties": {
            "total_parties": parties_total,
            "total_leaders": leaders_total,
            "with_logo_image": parties_with_logo,
            "with_eci_chart_image": parties_with_eci_chart,
        },
        "social_media": {
            "twitter_posts": twitter_posts_total,
            "reddit_posts": reddit_posts_total,
            "total_posts": twitter_posts_total + reddit_posts_total,
            "pending_sentiment": {
                "twitter": pending_twitter_sentiment,
                "reddit": pending_reddit_sentiment,
                "total": pending_twitter_sentiment + pending_reddit_sentiment,
            },
            "latest_post_at": {
                "twitter": latest_twitter_post,
                "reddit": latest_reddit_post,
            },
        },
        "predictions": {
            "total": predictions_total,
            "valid_now": valid_predictions,
            "by_type": predictions_by_type,
        },
        "news_cache": news_cache_metrics,
        "elections": {
            "total_results": election_results_total,
            "states": election_states_total,
            "years": election_years_total,
        },
    }


def _analyze_pending_sentiment(db: Session, limit: int = 100) -> Dict[str, Any]:
    """Analyze sentiment for posts still missing sentiment fields."""
    from app.models.social_media import RedditPost, TwitterPost
    from app.services.sentiment_service import sentiment_analyzer

    breakdown = {"twitter": 0, "reddit": 0}
    remaining = limit
    batches: List[Any] = []

    for platform_name, model in (("twitter", TwitterPost), ("reddit", RedditPost)):
        if remaining <= 0:
            break
        posts = db.query(model).filter(model.sentiment_label.is_(None)).limit(remaining).all()
        if posts:
            batches.append(posts)
            breakdown[platform_name] = len(posts)
            remaining -= len(posts)

    if not batches:
        return {
            "status": "success",
            "message": "No posts need sentiment analysis",
            "analyzed": 0,
            "breakdown": breakdown,
        }

    analyzed_count = 0
    for posts in batches:
        for post in posts:
            sentiment = sentiment_analyzer.analyze_sentiment(post.content, post.language)
            post.sentiment_label = sentiment["label"]
            post.sentiment_score = sentiment["score"]
            analyzed_count += 1

    db.commit()

    return {
        "status": "success",
        "message": f"Analyzed sentiment for {analyzed_count} posts",
        "analyzed": analyzed_count,
        "breakdown": breakdown,
    }


def _generate_wordclouds_after_scrape(
    db: Session,
    platform: str,
    party: Optional[str] = None,
    days: int = 30,
) -> Dict[str, Any]:
    """Generate relevant wordclouds right after scraping."""
    from app.models.social_media import TwitterPost

    targets: List[Dict[str, Any]] = []
    cutoff_date = datetime.now() - timedelta(days=days)

    if platform == "twitter":
        if party:
            targets.append(
                {
                    "label": f"party:{party}:political",
                    "params": {
                        "party": party,
                        "platform": "twitter",
                        "source_type": "political",
                        "days": days,
                        "language": "all",
                    },
                }
            )
            targets.append(
                {
                    "label": f"party:{party}:public",
                    "params": {
                        "party": party,
                        "platform": "twitter",
                        "source_type": "public",
                        "days": days,
                        "language": "all",
                    },
                }
            )
        else:
            parties = (
                db.query(TwitterPost.party)
                .filter(
                    TwitterPost.posted_at >= cutoff_date,
                    TwitterPost.party.isnot(None),
                )
                .distinct()
                .all()
            )
            for party_row in parties:
                if party_row[0]:
                    targets.append(
                        {
                            "label": f"party:{party_row[0]}:political",
                            "params": {
                                "party": party_row[0],
                                "platform": "twitter",
                                "source_type": "political",
                                "days": days,
                                "language": "all",
                            },
                        }
                    )

        targets.append(
            {
                "label": "platform:twitter:political",
                "params": {"platform": "twitter", "source_type": "political", "days": days, "language": "all"},
            }
        )
        targets.append(
            {
                "label": "platform:twitter:public",
                "params": {"platform": "twitter", "source_type": "public", "days": days, "language": "all"},
            }
        )

    elif platform == "reddit":
        targets.append(
            {
                "label": "platform:reddit:public",
                "params": {"platform": "reddit", "source_type": "public", "days": days, "language": "all"},
            }
        )

    else:
        targets.append(
            {
                "label": "platform:all",
                "params": {"days": days, "language": "all"},
            }
        )

    generated = []
    failed = []

    for target in targets:
        try:
            image_bytes = wordcloud_service.generate_wordcloud(db, **target["params"])
            generated.append({"target": target["label"], "bytes": len(image_bytes)})
        except Exception as exc:
            logger.error(f"Wordcloud generation failed for {target['label']}: {exc}")
            failed.append({"target": target["label"], "error": str(exc)})

    return {
        "generated": len(generated),
        "failed": len(failed),
        "details": generated,
        "errors": failed,
    }


def _run_auto_post_processing(
    db: Session,
    scrape_stats: Dict[str, Any],
    platform: str,
    party: Optional[str] = None,
) -> Dict[str, Any]:
    """Run scrape follow-up automation: sentiment then wordcloud."""
    new_posts = _extract_new_inserted_count(scrape_stats)
    sentiment_limit = max(100, min(2000, new_posts * 2 if new_posts else 200))

    sentiment_stats = _analyze_pending_sentiment(db, limit=sentiment_limit)
    wordcloud_stats = _generate_wordclouds_after_scrape(
        db,
        platform=platform,
        party=party,
        days=30,
    )

    return {
        "new_posts_detected": new_posts,
        "sentiment": sentiment_stats,
        "wordcloud": wordcloud_stats,
    }


@router.post("/scrape/twitter")
async def trigger_twitter_scrape(
    party: Optional[str] = None,
    handles: Optional[str] = Query(
        None,
        description="Comma-separated Twitter handles to target (e.g. narendramodi,AmitShah)",
    ),
    language: str = Query("en", pattern="^(en|hi|all)$"),
    since_days: int = Query(180, ge=1, le=3650),
    include_public: bool = Query(True, description="When party scrape is used, also scrape public conversation"),
    target_count: int = Query(200, ge=1, le=2000),
    product: str = Query("Latest", pattern="^(Latest|Top)$"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Trigger Twitter scraping + automatic post-processing.

    - If handles specified: scrape those handles (political source)
    - Else if party specified: scrape configured handles for that party (+ optional public conversation)
    - Else: scrape all configured parties
    - language: en, hi, or all
    - since_days: lookback window in days
    - target_count: target tweets per query
    - product: Latest or Top
    - Automatically runs pending sentiment analysis and wordcloud generation
    """
    try:
        if handles:
            parsed_handles = [
                handle.strip().lstrip("@")
                for handle in handles.split(",")
                if handle.strip()
            ]
            if not parsed_handles:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid handles parameter. Provide comma-separated handle names.",
                )

            logger.info(
                f"Starting Twitter custom handle scrape for {parsed_handles} "
                f"(language={language}, since_days={since_days})"
            )
            stats = await twitter_service.scrape_handles(
                db,
                handles=parsed_handles,
                party=party,
                language=language,
                since_days=since_days,
                target_count=target_count,
                product=product,
            )
            automation = _run_auto_post_processing(
                db,
                scrape_stats=stats,
                platform="twitter",
                party=party,
            )
            return {
                "status": "success",
                "message": "Twitter custom handle scrape completed",
                "mode": "custom_handles",
                "handles": parsed_handles,
                "stats": stats,
                "automation": automation,
            }

        if party:
            logger.info(
                f"Starting Twitter scrape for {party} "
                f"(language={language}, since_days={since_days}, include_public={include_public})"
            )
            stats = await twitter_service.scrape_party_tweets(
                db,
                party=party,
                language=language,
                since_days=since_days,
                include_public=include_public,
                target_count=target_count,
                product=product,
            )
            automation = _run_auto_post_processing(
                db,
                scrape_stats=stats,
                platform="twitter",
                party=party,
            )
            return {
                "status": "success",
                "message": f"Twitter scrape completed for {party}",
                "stats": stats,
                "automation": automation,
            }

        logger.info("Starting Twitter scrape for all parties")
        results = await twitter_service.scrape_all_parties(
            db,
            language=language,
            since_days=since_days,
            include_public=include_public,
            target_count=target_count,
            product=product,
        )
        automation = _run_auto_post_processing(
            db,
            scrape_stats=results,
            platform="twitter",
            party=None,
        )
        return {
            "status": "success",
            "message": "Twitter scrape completed for all parties",
            "results": results,
            "automation": automation,
        }
    except Exception as e:
        logger.error(f"Twitter scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/twitter/hashtag")
async def trigger_hashtag_scrape(
    hashtag: str = Query(..., description="Hashtag or keyword to search (e.g. #BJP, #Modi, OperationSindoor)"),
    party: Optional[str] = Query(None, description="Optional: tag captured tweets with this party"),
    language: str = Query("en", pattern="^(en|hi|all)$"),
    since_days: int = Query(7, ge=1, le=365),
    target_count: int = Query(200, ge=10, le=2000),
    product: str = Query("Latest", pattern="^(Latest|Top)$"),
    db: Session = Depends(get_db),
):
    """
    Scrape tweets for a specific hashtag or keyword.

    - hashtag: '#BJP', '#Congress', 'NarendraModi', etc.
    - language: en | hi | all
    - since_days: look-back window (default 7)
    - target_count: max tweets to collect
    - product: Latest or Top results
    """
    try:
        tag = hashtag.strip()
        logger.info(f"Starting Twitter hashtag scrape: {tag} (lang={language}, days={since_days})")
        stats = await twitter_service.scrape_hashtag(
            db,
            hashtag=tag,
            party=party,
            language=language,
            since_days=since_days,
            target_count=target_count,
            product=product,
        )
        automation = _run_auto_post_processing(db, scrape_stats=stats, platform="twitter", party=party)
        return {
            "status": "success",
            "message": f"Hashtag scrape completed for '{tag}'",
            "mode": "hashtag",
            "hashtag": tag,
            "language": language,
            "stats": stats,
            "automation": automation,
        }
    except Exception as e:
        logger.error(f"Hashtag scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/twitter/bilingual")
async def trigger_bilingual_scrape(
    mode: str = Query("party", pattern="^(party|handle|hashtag|all)$",
                      description="Scrape mode: party | handle | hashtag | all"),
    party: Optional[str] = Query(None, description="Party name (BJP, INC, AAP, SP, TMC, BSP, CPIM)"),
    handles: Optional[str] = Query(None, description="Comma-separated handles (for mode=handle)"),
    hashtag: Optional[str] = Query(None, description="Hashtag or keyword (for mode=hashtag)"),
    since_days: int = Query(30, ge=1, le=365),
    target_count: int = Query(100, ge=10, le=1000),
    include_public: bool = Query(True),
    product: str = Query("Latest", pattern="^(Latest|Top)$"),
    db: Session = Depends(get_db),
):
    """
    Run scraping in BOTH English and Hindi in a single call.

    - mode: party | handle | hashtag | all
    - Sets up two consecutive scrapes (lang=en then lang=hi)
    - Runs automatic sentiment + wordcloud post-processing
    """
    try:
        parsed_handles = None
        if handles:
            parsed_handles = [h.strip().lstrip("@") for h in handles.split(",") if h.strip()]

        logger.info(f"Starting bilingual scrape (mode={mode}, party={party}, hashtag={hashtag})")
        results = await twitter_service.scrape_bilingual(
            db,
            mode=mode,
            party=party,
            handles=parsed_handles,
            hashtag=hashtag,
            since_days=since_days,
            target_count=target_count,
            include_public=include_public,
            product=product,
        )
        automation = _run_auto_post_processing(db, scrape_stats=results, platform="twitter", party=party)
        return {
            "status": "success",
            "message": "Bilingual scrape (EN + HI) completed",
            "mode": mode,
            "results": results,
            "automation": automation,
        }
    except Exception as e:
        logger.error(f"Bilingual scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/reddit")
def trigger_reddit_scrape(
    subreddit: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger Reddit scraping + automatic post-processing.

    - If subreddit specified: scrape only that subreddit
    - If no subreddit: scrape all configured subreddits
    - Automatically runs pending sentiment analysis and wordcloud generation
    """
    try:
        if subreddit:
            logger.info(f"Starting Reddit scrape for r/{subreddit}")
            stats = reddit_service.scrape_subreddit(db, subreddit)
            automation = _run_auto_post_processing(
                db,
                scrape_stats=stats,
                platform="reddit",
                party=None,
            )
            return {
                "status": "success",
                "message": f"Reddit scrape completed for r/{subreddit}",
                "stats": stats,
                "automation": automation,
            }

        logger.info("Starting Reddit scrape for all subreddits")
        results = reddit_service.scrape_all_subreddits(db)
        automation = _run_auto_post_processing(
            db,
            scrape_stats=results,
            platform="reddit",
            party=None,
        )
        return {
            "status": "success",
            "message": "Reddit scrape completed for all subreddits",
            "results": results,
            "automation": automation,
        }
    except Exception as e:
        logger.error(f"Reddit scrape failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/news")
def trigger_news_fetch(
    category: Optional[str] = Query(None, pattern="^(india_politics|geopolitics)$")
):
    """
    Fetch latest news articles

    - category: 'india_politics' or 'geopolitics' or None for both
    """
    try:
        if category:
            logger.info(f"Fetching news for {category}")
            stats = news_service.refresh_category(category)
            return {
                "status": "success",
                "message": f"News fetch completed for {category}",
                "stats": stats
            }
        else:
            logger.info("Fetching news for all categories")
            results = news_service.refresh_all_categories()
            return {
                "status": "success",
                "message": "News fetch completed for all categories",
                "results": results
            }
    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/sentiment")
def trigger_sentiment_analysis(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Analyze sentiment for posts without sentiment scores"""
    try:
        sentiment_stats = _analyze_pending_sentiment(db, limit=limit)
        return sentiment_stats

    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wordcloud/{entity_type}/{entity_name}")
def generate_wordcloud(
    entity_type: str,
    entity_name: str,
    days: int = 30,
    source_type: str = Query("all", pattern="^(political|public|all)$"),
    language: str = 'en',
    db: Session = Depends(get_db)
):
    """
    Generate word cloud image

    - entity_type: 'party' or 'leader'
    - entity_name: Name of party or leader
    - days: Days of history
    - source_type: 'political', 'public', or 'all'
    - language: 'en', 'hi', or 'all'
    """
    try:
        source_filter = None if source_type == "all" else source_type
        if entity_type == 'party':
            image_bytes = wordcloud_service.generate_wordcloud(
                db, party=entity_name, source_type=source_filter, days=days, language=language
            )
        elif entity_type == 'leader':
            image_bytes = wordcloud_service.generate_wordcloud(
                db, leader_name=entity_name, source_type=source_filter, days=days, language=language
            )
        else:
            raise HTTPException(status_code=400, detail="entity_type must be 'party' or 'leader'")

        return Response(content=image_bytes, media_type="image/png")

    except Exception as e:
        logger.error(f"Word cloud generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def admin_status(db: Session = Depends(get_db)):
    """Get status of admin services"""
    metrics = _collect_admin_metrics(db)
    return {
        "status": "active",
        "generated_at": datetime.utcnow(),
        "services": {
            "twitter": "available" if twitter_service else "unavailable",
            "reddit": "available" if reddit_service else "unavailable",
            "news": "available" if news_service else "unavailable",
            "wordcloud": "available" if wordcloud_service else "unavailable"
        },
        "metrics": metrics,
        "message": "Admin endpoints are operational"
    }


@router.post("/trigger-reply-pipeline")
async def trigger_reply_pipeline(
    batch_size: int = Query(20, ge=1, le=100, description="Number of tweets to process"),
    db: Session = Depends(get_db),
):
    """
    Manually trigger one batch of the tweet reply analysis pipeline.

    Fetches replies for up to `batch_size` tweets that have not yet been
    processed (replies_fetched=False, replies>2), runs MiniLM sentiment
    on the replies, and writes public_sentiment_* back to the parent tweet.

    Useful for testing without waiting 30 minutes for the APScheduler job.
    """
    from app.services.reply_pipeline import run_reply_pipeline

    try:
        logger.info(f"Manual reply pipeline trigger: batch_size={batch_size}")
        stats = await run_reply_pipeline(db=db, batch_size=batch_size)
        return {
            "status": "success",
            "message": f"Reply pipeline completed. Processed {stats.get('processed', 0)} tweets.",
            "stats": stats,
        }
    except Exception as exc:
        logger.exception("Manual reply pipeline trigger failed")
        raise HTTPException(status_code=500, detail=str(exc))
