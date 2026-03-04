from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "polipulse"
    DB_USER: str = "polipulse_admin"
    DB_PASSWORD: str = "polipulse_admin"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Admin credentials (for protected write endpoints)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # GNews API
    NEWS_API_KEY: str = ""  # legacy/unused
    GNEWS_API_KEY: str = ""
    NEWS_REFRESH_INTERVAL_HOURS: int = 6

    # Reddit API (PRAW)
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "PoliPulse/1.0"

    # Twitter Scraper
    TWITTER_COOKIES_PATH: str = "cookies.json"
    SCRAPER_ENABLED: bool = True

    # Background Jobs
    PREDICTION_CRON_HOUR: int = 0
    PREDICTION_CRON_MINUTE: int = 0

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Environment
    ENVIRONMENT: str = "development"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
