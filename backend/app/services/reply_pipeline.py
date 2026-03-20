"""
Reply Pipeline
Async job that fetches replies for pending tweets,
runs MiniLM sentiment on batches, and writes aggregated
public sentiment back to the parent twitter_posts row.

Designed to run every 30 minutes via APScheduler.
Processes tweets ordered by reply count (highest signal first).
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


async def run_reply_pipeline(db: Session, batch_size: int = 20) -> dict:
    """
    Main pipeline entry point — called by APScheduler every 30 minutes.

    Steps for each pending tweet:
      1. Fetch replies via twikit
      2. Batch-analyze with MiniLM cosine similarity
      3. Persist TweetReply rows
      4. Aggregate → update parent TwitterPost.public_sentiment_*
      5. Mark replies_fetched = True

    Returns a summary dict with processed/skipped/failed counts.
    """
    from app.models.social_media import TweetReply, TwitterPost
    from app.services.reply_analysis_service import ReplyAnalysisService
    from app.services.twitter_service import twitter_service

    stats = {"processed": 0, "skipped_no_replies": 0, "failed": 0, "batch_size": batch_size}

    # ── Fetch pending tweets ordered by reply count (highest signal first) ────
    pending = (
        db.query(TwitterPost)
        .filter(TwitterPost.replies_fetched.is_(False))
        .filter(TwitterPost.replies > 2)       # skip tweets with almost no replies
        .order_by(TwitterPost.replies.desc())  # process highest-engagement first
        .limit(batch_size)
        .all()
    )

    if not pending:
        logger.info("run_reply_pipeline: no pending tweets found.")
        return stats

    logger.info(f"run_reply_pipeline: processing {len(pending)} tweets.")

    # Instantiate service here so the model is loaded once for the whole batch
    analysis_svc = ReplyAnalysisService()
    # Eagerly initialise (loads model from disk if not already cached in memory)
    analysis_svc._ensure_initialized()

    for post in pending:
        try:
        # ── 1. Fetch raw replies from Twitter/X ───────────────────────────
            import os
            from datetime import datetime as _dt
            USE_MOCK = os.environ.get("USE_MOCK_REPLIES", "0") == "1"

            if USE_MOCK:
                logger.info(f"[MOCK] Generating synthetic replies for tweet {post.post_id}")
                raw_replies = [
                    {
                        "reply_id": f"mock_{post.post_id}_1",
                        "reply_username": "supporter_user",
                        "reply_content": "bahut accha kaam kiya sarkar ne, hum samarthan karte hain",
                        "reply_likes": 8,
                        "reply_posted_at": _dt.utcnow(),
                    },
                    {
                        "reply_id": f"mock_{post.post_id}_2",
                        "reply_username": "critic_user",
                        "reply_content": "This policy is terrible, prices are rising daily for common people",
                        "reply_likes": 15,
                        "reply_posted_at": _dt.utcnow(),
                    },
                    {
                        "reply_id": f"mock_{post.post_id}_3",
                        "reply_username": "neutral_observer",
                        "reply_content": "Let us wait and watch the implementation before forming opinions",
                        "reply_likes": 3,
                        "reply_posted_at": _dt.utcnow(),
                    },
                    {
                        "reply_id": f"mock_{post.post_id}_4",
                        "reply_username": "positive_user",
                        "reply_content": "Great initiative by the government, very happy with this decision",
                        "reply_likes": 22,
                        "reply_posted_at": _dt.utcnow(),
                    },
                ]
            else:
                raw_replies = await twitter_service.fetch_tweet_replies(
                    post.post_id, max_replies=80
                )

            if not raw_replies:
                post.replies_fetched = True
                db.commit()
                stats["skipped_no_replies"] += 1
                logger.info(f"No usable replies for tweet {post.post_id}.")
                continue

            # ── 2. Batch-analyse reply texts ──────────────────────────────────
            texts = [r["reply_content"] for r in raw_replies]
            sentiments = analysis_svc.analyze_batch(texts)

            # ── 3. Merge sentiment back and persist TweetReply rows ───────────
            enriched: list[dict] = []
            for reply_dict, sentiment in zip(raw_replies, sentiments):
                merged = {
                    **reply_dict,
                    "reply_sentiment_label": sentiment["sentiment_label"],
                    "reply_sentiment_score": sentiment["sentiment_score"],
                }
                enriched.append(merged)

                # Upsert-safe: skip if reply_id already exists
                if not db.query(TweetReply).filter(TweetReply.reply_id == merged["reply_id"]).first():
                    db.add(
                        TweetReply(
                            parent_post_id=post.post_id,
                            reply_id=merged["reply_id"],
                            reply_username=merged.get("reply_username"),
                            reply_content=merged["reply_content"],
                            reply_sentiment_label=merged["reply_sentiment_label"],
                            reply_sentiment_score=merged["reply_sentiment_score"],
                            reply_likes=merged.get("reply_likes", 0),
                            reply_posted_at=merged.get("reply_posted_at"),
                        )
                    )

            # ── 4. Aggregate and write back to parent post ────────────────────
            agg = analysis_svc.aggregate(enriched)
            post.public_sentiment_label = agg["public_sentiment_label"]
            post.public_sentiment_score = agg["public_sentiment_score"]
            post.public_reaction_summary = agg["public_reaction_summary"]
            post.replies_fetched = True

            db.commit()
            stats["processed"] += 1
            logger.info(
                f"tweet {post.post_id}: {len(enriched)} replies → "
                f"public_sentiment={agg['public_sentiment_label']} "
                f"(score={agg['public_sentiment_score']})"
            )

        except Exception as exc:
            logger.exception(f"Pipeline failed for tweet {post.post_id}: {exc}")
            db.rollback()
            stats["failed"] += 1

        # ── Rate limit buffer between tweets ──────────────────────────────────
        await asyncio.sleep(2.0)

    logger.info(f"run_reply_pipeline complete: {stats}")
    return stats
