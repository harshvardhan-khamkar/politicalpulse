import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.api import auth, elections, polls, parties, social_media, predictions_news, admin, nlp_analysis, events
from app.models.users import AppUser  # noqa: F401 - ensures table metadata is registered
from app.security import ensure_admin_user_exists

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PoliPulse API",
    description="Political Intelligence Tool for Indian Elections Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Create tables and seed auth data."""
    try:
        Base.metadata.create_all(bind=engine)

        with engine.begin() as conn:
            # DB-level protection for one vote per poll per voter identity.
            conn.execute(
                text(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_poll_votes_poll_voter
                    ON poll_votes (poll_id, voter_info)
                    WHERE voter_info IS NOT NULL
                    """
                )
            )

            # Backward-compatible column additions for existing parties table.
            conn.execute(text("ALTER TABLE parties ADD COLUMN IF NOT EXISTS overview TEXT"))
            conn.execute(text("ALTER TABLE parties ADD COLUMN IF NOT EXISTS policies TEXT"))
            conn.execute(
                text(
                    "ALTER TABLE parties ADD COLUMN IF NOT EXISTS eci_chart_image_url VARCHAR(1000)"
                )
            )
            conn.execute(text("ALTER TABLE parties ADD COLUMN IF NOT EXISTS logo_image_data BYTEA"))
            conn.execute(
                text("ALTER TABLE parties ADD COLUMN IF NOT EXISTS logo_image_content_type VARCHAR(100)")
            )
            conn.execute(text("ALTER TABLE parties ADD COLUMN IF NOT EXISTS eci_chart_image_data BYTEA"))
            conn.execute(
                text(
                    "ALTER TABLE parties ADD COLUMN IF NOT EXISTS eci_chart_image_content_type VARCHAR(100)"
                )
            )

            # Backward-compatible auth additions for email-based login.
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
            conn.execute(
                text(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_app_users_email_lower
                    ON app_users (lower(email))
                    WHERE email IS NOT NULL
                    """
                )
            )

            # Ensure social source split columns exist on new per-platform tables.
            conn.execute(text("ALTER TABLE IF EXISTS twitter_posts ADD COLUMN IF NOT EXISTS source_type VARCHAR(20)"))
            conn.execute(text("ALTER TABLE IF EXISTS reddit_posts ADD COLUMN IF NOT EXISTS source_type VARCHAR(20)"))
            conn.execute(text("ALTER TABLE IF EXISTS reddit_posts ADD COLUMN IF NOT EXISTS subreddit VARCHAR(100)"))
            conn.execute(text("UPDATE twitter_posts SET source_type = 'public' WHERE source_type IS NULL"))
            conn.execute(text("UPDATE reddit_posts SET source_type = 'public' WHERE source_type IS NULL"))
            conn.execute(text("ALTER TABLE IF EXISTS twitter_posts ALTER COLUMN source_type SET DEFAULT 'public'"))
            conn.execute(text("ALTER TABLE IF EXISTS reddit_posts ALTER COLUMN source_type SET DEFAULT 'public'"))
            conn.execute(text("ALTER TABLE IF EXISTS twitter_posts ALTER COLUMN source_type SET NOT NULL"))
            conn.execute(text("ALTER TABLE IF EXISTS reddit_posts ALTER COLUMN source_type SET NOT NULL"))

            # One-time migration from legacy unified social_posts table into split tables.
            legacy_social_table = conn.execute(
                text("SELECT to_regclass('public.social_posts')")
            ).scalar()

            if legacy_social_table:
                conn.execute(
                    text(
                        """
                        INSERT INTO twitter_posts
                        (
                            post_id, leader_name, party, username, source_type, content, language,
                            sentiment_label, sentiment_score, likes, retweets, replies, score, url, posted_at
                        )
                        SELECT
                            sp.post_id,
                            sp.leader_name,
                            sp.party,
                            sp.username,
                            CASE
                                WHEN lower(coalesce(sp.username, '')) IN (
                                    'bjp4india', 'narendramodi', 'amitshah', 'jpnadda', 'myogiadityanath',
                                    'incindia', 'rahulgandhi', 'kharge', 'shashitharoor', 'priyankagandhi',
                                    'aamaadmiparty', 'arvindkejriwal', 'raghav_chadha', 'atishiaap'
                                ) THEN 'political'
                                ELSE 'public'
                            END AS source_type,
                            sp.content,
                            sp.language,
                            sp.sentiment_label,
                            sp.sentiment_score,
                            coalesce(sp.likes, 0),
                            coalesce(sp.retweets, 0),
                            coalesce(sp.replies, 0),
                            coalesce(sp.score, 0),
                            sp.url,
                            sp.posted_at
                        FROM social_posts sp
                        WHERE sp.platform = 'twitter'
                        ON CONFLICT (post_id) DO NOTHING
                        """
                    )
                )

                conn.execute(
                    text(
                        """
                        INSERT INTO reddit_posts
                        (
                            post_id, leader_name, party, username, source_type, content, language,
                            sentiment_label, sentiment_score, likes, retweets, replies, score, url, posted_at, subreddit
                        )
                        SELECT
                            sp.post_id,
                            sp.leader_name,
                            sp.party,
                            sp.username,
                            'public' AS source_type,
                            sp.content,
                            sp.language,
                            sp.sentiment_label,
                            sp.sentiment_score,
                            coalesce(sp.likes, 0),
                            coalesce(sp.retweets, 0),
                            coalesce(sp.replies, 0),
                            coalesce(sp.score, 0),
                            sp.url,
                            sp.posted_at,
                            NULL::varchar(100) AS subreddit
                        FROM social_posts sp
                        WHERE sp.platform = 'reddit'
                        ON CONFLICT (post_id) DO NOTHING
                        """
                    )
                )

        # Run seeding after backward-compatible column migrations.
        ensure_admin_user_exists()

    except Exception:
        logger.exception("Database initialization failed")


# Include routers
app.include_router(auth.router)
app.include_router(elections.router)
app.include_router(polls.router)
app.include_router(parties.router)
app.include_router(social_media.router)
app.include_router(predictions_news.router_predictions)
app.include_router(predictions_news.router_news)
app.include_router(admin.router)
app.include_router(nlp_analysis.router)
app.include_router(events.router)


@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "Welcome to PoliPulse API",
        "version": "1.0.0",
        "docs": "/docs",
        "database": settings.DB_NAME,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
