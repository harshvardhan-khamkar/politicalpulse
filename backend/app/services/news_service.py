"""
News Service
Fetch political news from GNews API with in-memory caching.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import logging

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class NewsService:
    """News aggregation service using GNews API and in-memory cache."""

    GNEWS_SEARCH_URL = "https://gnews.io/api/v4/search"

    CATEGORY_QUERIES = {
        "india_politics": "India politics OR BJP OR Congress OR Parliament OR elections",
        "geopolitics": "geopolitics OR international relations OR global politics OR diplomacy",
    }

    def __init__(self):
        self.news_cache = {
            "india_politics": {
                "articles": [],
                "last_updated": None,
            },
            "geopolitics": {
                "articles": [],
                "last_updated": None,
            },
        }

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)

    def _is_cache_expired(self, category: str) -> bool:
        cache_entry = self.news_cache[category]
        last_updated = cache_entry["last_updated"]
        articles = cache_entry["articles"]

        if not articles or last_updated is None:
            return True

        refresh_delta = timedelta(hours=settings.NEWS_REFRESH_INTERVAL_HOURS)
        return datetime.now(timezone.utc) - last_updated >= refresh_delta

    def _fetch_from_gnews(self, category: str) -> List[Dict[str, Any]]:
        if category not in self.CATEGORY_QUERIES:
            raise ValueError(f"Unsupported category: {category}")

        if not settings.GNEWS_API_KEY:
            raise ValueError("GNEWS_API_KEY is not configured")

        params = {
            "q": self.CATEGORY_QUERIES[category],
            "token": settings.GNEWS_API_KEY,
            "lang": "en",
            "max": 20,
            "sortby": "publishedAt",
        }

        response = requests.get(self.GNEWS_SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()

        raw_articles = payload.get("articles", [])
        articles: List[Dict[str, Any]] = []

        for item in raw_articles:
            source_payload = item.get("source") or {}
            articles.append(
                {
                    "title": item.get("title") or "",
                    "description": item.get("description") or "",
                    "url": item.get("url") or "",
                    "image_url": item.get("image") or "",
                    "source": source_payload.get("name") or "",
                    "published_at": self._parse_datetime(item.get("publishedAt", "")),
                }
            )

        return articles

    def _build_response(self, category: str) -> Dict[str, Any]:
        cache_entry = self.news_cache[category]
        return {
            "category": category,
            "last_updated": cache_entry["last_updated"],
            "count": len(cache_entry["articles"]),
            "articles": cache_entry["articles"],
        }

    def refresh_category(self, category: str) -> Dict[str, Any]:
        articles = self._fetch_from_gnews(category)
        self.news_cache[category]["articles"] = articles
        self.news_cache[category]["last_updated"] = datetime.now(timezone.utc)
        return self._build_response(category)

    def refresh_all_categories(self) -> Dict[str, Dict[str, Any]]:
        return {
            "india_politics": self.refresh_category("india_politics"),
            "geopolitics": self.refresh_category("geopolitics"),
        }

    def get_category_news(self, category: str) -> Dict[str, Any]:
        if category not in self.news_cache:
            raise ValueError(f"Unsupported category: {category}")

        if self._is_cache_expired(category):
            try:
                return self.refresh_category(category)
            except Exception:
                logger.exception("GNews fetch failed for category %s", category)
                if self.news_cache[category]["articles"]:
                    return self._build_response(category)
                raise

        return self._build_response(category)


news_service = NewsService()
