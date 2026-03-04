"""
Twitter Service
Integrates Twikit for Twitter scraping
Adapted from ref/collect.py with database integration
"""
import asyncio
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Known political/official handles used to classify source type.
POLITICAL_HANDLES_BY_PARTY = {
    "BJP": {"BJP4India", "narendramodi", "AmitShah", "JPNadda", "myogiadityanath"},
    "INC": {"INCIndia", "RahulGandhi", "kharge", "ShashiTharoor", "priyankagandhi"},
    "AAP": {"AamAadmiParty", "ArvindKejriwal", "raghav_chadha", "AtishiAAP"},
}

# Terms used to capture broader public conversation for each party.
PUBLIC_TERMS_BY_PARTY = {
    "BJP": ["narendramodi", "AmitShah", "BJP", "#BJP", "#ModiHaiToMumkinHai"],
    "INC": ["RahulGandhi", "#RahulGandhi", "#Congress", "#BharatJodoYatra", "INCIndia"],
    "AAP": ["ArvindKejriwal", "#Kejriwal", "#AAP", "#DelhiModel", "AamAadmiParty"],
}

ALL_POLITICAL_HANDLES = {
    handle.lower() for handles in POLITICAL_HANDLES_BY_PARTY.values() for handle in handles
}
HANDLE_TO_PARTY = {
    handle.lower(): party
    for party, handles in POLITICAL_HANDLES_BY_PARTY.items()
    for handle in handles
}


class TwitterService:
    """Twitter scraping service using Twikit"""
    
    def __init__(self, cookies_path: str = "cookies.json"):
        self.cookies_path = cookies_path
        self.client = None
        self.initialized = False
        
    async def _init_client(self):
        """Initialize Twikit client with cookies"""
        if self.initialized:
            return
            
        try:
            from twikit import Client
            
            if not os.path.exists(self.cookies_path):
                logger.error(f"Cookies file not found: {self.cookies_path}")
                raise FileNotFoundError(f"Twitter cookies not found at {self.cookies_path}")
            
            self.client = Client(language='en-US')
            self.client.load_cookies(self.cookies_path)
            self.initialized = True
            logger.info("Twitter client initialized successfully")
            
        except ImportError:
            logger.error("Twikit not installed. Install with: pip install twikit")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            raise

    @staticmethod
    def _normalize_handle(handle: str) -> str:
        return handle.strip().lstrip("@")

    @staticmethod
    def _normalize_language(language: str) -> str:
        lang = (language or "en").strip().lower()
        if lang not in {"en", "hi", "all"}:
            raise ValueError("language must be one of: en, hi, all")
        return lang

    @staticmethod
    def _build_since_fragment(since_days: int) -> str:
        since_date = (datetime.now() - timedelta(days=since_days)).date().isoformat()
        return f" since:{since_date}"

    @staticmethod
    def _resolve_party_from_username(username: str) -> Optional[str]:
        if not username:
            return None
        return HANDLE_TO_PARTY.get(username.lower())

    def _build_handles_query(self, handles: List[str], language: str, since_days: int) -> str:
        handle_clause = " OR ".join(f"from:{handle}" for handle in handles)
        lang_fragment = "" if language == "all" else f" lang:{language}"
        return f"({handle_clause}){lang_fragment}{self._build_since_fragment(since_days)}"

    def _build_public_query(self, terms: List[str], language: str, since_days: int) -> str:
        terms_clause = " OR ".join(terms)
        lang_fragment = "" if language == "all" else f" lang:{language}"
        return f"({terms_clause}){lang_fragment}{self._build_since_fragment(since_days)}"

    async def _scrape_queries(
        self,
        db: Session,
        queries: List[str],
        party: Optional[str] = None,
        target_handles: Optional[List[str]] = None,
        language: str = "en",
        target_count: int = 200,
        cooldown_seconds: tuple = (3, 8),
        product: str = "Latest",
    ) -> Dict[str, int]:
        from app.models.social_media import TwitterPost
        from app.services.sentiment_service import sentiment_analyzer
        from twikit import TooManyRequests

        target_handle_set = {
            self._normalize_handle(handle).lower()
            for handle in (target_handles or [])
            if str(handle).strip()
        }

        stats = {"total_fetched": 0, "new_inserted": 0, "duplicates": 0, "queries": len(queries)}

        for query_idx, query in enumerate(queries):
            logger.info(f"Twitter scrape query {query_idx + 1}/{len(queries)}: {query}")
            collected = 0
            tweets = None

            while collected < target_count:
                try:
                    if tweets is None:
                        tweets = await self.client.search_tweet(query, product)
                    else:
                        tweets = await tweets.next()

                    if not tweets:
                        break

                    for tweet in tweets:
                        stats["total_fetched"] += 1

                        tweet_id = str(tweet.id)
                        existing = db.query(TwitterPost).filter(TwitterPost.post_id == tweet_id).first()
                        if existing:
                            stats["duplicates"] += 1
                            continue

                        content = getattr(tweet, "text", "") or getattr(tweet, "full_text", "")
                        if not content:
                            continue

                        user_obj = getattr(tweet, "user", None)
                        screen_name = (getattr(user_obj, "screen_name", "") or "").strip()
                        screen_name_key = screen_name.lower()

                        # Political if known party/leader handle, or explicitly targeted handle.
                        source_type = (
                            "political"
                            if screen_name_key in ALL_POLITICAL_HANDLES or screen_name_key in target_handle_set
                            else "public"
                        )

                        inferred_party = party or self._resolve_party_from_username(screen_name)
                        forced_lang = language if language in {"en", "hi"} else None
                        sentiment = sentiment_analyzer.analyze_sentiment(content, forced_lang)

                        url = getattr(tweet, "url", None)
                        if not url and screen_name:
                            url = f"https://twitter.com/{screen_name}/status/{tweet_id}"

                        post = TwitterPost(
                            post_id=tweet_id,
                            party=inferred_party,
                            username=screen_name,
                            source_type=source_type,
                            leader_name=None,
                            content=content,
                            language=sentiment["language"],
                            sentiment_label=sentiment["label"],
                            sentiment_score=sentiment["score"],
                            likes=getattr(tweet, "favorite_count", 0) or 0,
                            retweets=getattr(tweet, "retweet_count", 0) or 0,
                            replies=getattr(tweet, "reply_count", 0) or 0,
                            url=url,
                            posted_at=getattr(tweet, "created_at", datetime.now()),
                        )

                        db.add(post)
                        stats["new_inserted"] += 1
                        collected += 1

                        if collected >= target_count:
                            break

                    db.commit()
                    await asyncio.sleep(random.uniform(*cooldown_seconds))

                except TooManyRequests as e:
                    rate_limit_reset = e.rate_limit_reset
                    wait_time = (rate_limit_reset - datetime.now()).total_seconds()
                    wait_time = max(10, wait_time + 5)
                    logger.warning(f"Twitter rate limited. Waiting {wait_time:.0f}s...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Twitter query failed: {e}")
                    db.rollback()
                    break

            logger.info(f"Completed query {query_idx + 1}: inserted {collected} posts")
            if query_idx < len(queries) - 1:
                wait_time = random.uniform(45, 90)
                logger.info(f"Query cooldown: {wait_time:.0f}s")
                await asyncio.sleep(wait_time)

        return stats

    async def scrape_party_tweets(
        self,
        db: Session,
        party: str,
        language: str = "en",
        since_days: int = 180,
        include_public: bool = True,
        target_count: int = 200,
        cooldown_seconds: tuple = (3, 8),
        product: str = "Latest",
    ) -> Dict[str, int]:
        """
        Scrape tweets for a political party
        
        Args:
            db: Database session
            party: Party name (BJP, INC, AAP)
            language: en, hi, or all
            since_days: how many days back to scrape
            include_public: include non-handle public conversation query for party
            target_count: Target number of tweets per query
            cooldown_seconds: Min/max seconds to wait between requests
            product: Twikit search product (Latest/Top)
            
        Returns:
            Statistics dict with counts
        """
        await self._init_client()

        party_key = (party or "").strip().upper()
        language = self._normalize_language(language)
        handles = [self._normalize_handle(h) for h in POLITICAL_HANDLES_BY_PARTY.get(party_key, set())]
        handles = [h for h in handles if h]

        if not handles:
            logger.warning(f"No handles configured for party: {party_key}")
            return {"total_fetched": 0, "new_inserted": 0, "duplicates": 0, "queries": 0}

        queries = [self._build_handles_query(handles, language=language, since_days=since_days)]
        if include_public:
            public_terms = PUBLIC_TERMS_BY_PARTY.get(party_key, [party_key])
            queries.append(self._build_public_query(public_terms, language=language, since_days=since_days))

        stats = await self._scrape_queries(
            db,
            queries=queries,
            party=party_key,
            target_handles=handles,
            language=language,
            target_count=target_count,
            cooldown_seconds=cooldown_seconds,
            product=product,
        )
        logger.info(f"Twitter scraping complete for {party_key}: {stats}")
        return stats

    async def scrape_handles(
        self,
        db: Session,
        handles: List[str],
        party: Optional[str] = None,
        language: str = "en",
        since_days: int = 180,
        target_count: int = 200,
        cooldown_seconds: tuple = (3, 8),
        product: str = "Latest",
    ) -> Dict[str, int]:
        """Scrape tweets from explicitly provided handles."""
        await self._init_client()

        normalized_handles = []
        for handle in handles:
            clean = self._normalize_handle(handle)
            if clean:
                normalized_handles.append(clean)
        normalized_handles = list(dict.fromkeys(normalized_handles))

        if not normalized_handles:
            raise ValueError("handles must contain at least one valid handle")

        language = self._normalize_language(language)
        party_key = (party or "").strip().upper() or None
        queries = [self._build_handles_query(normalized_handles, language=language, since_days=since_days)]

        stats = await self._scrape_queries(
            db,
            queries=queries,
            party=party_key,
            target_handles=normalized_handles,
            language=language,
            target_count=target_count,
            cooldown_seconds=cooldown_seconds,
            product=product,
        )
        logger.info(f"Twitter custom handle scrape complete for {normalized_handles}: {stats}")
        return stats

    async def scrape_all_parties(
        self,
        db: Session,
        language: str = "en",
        since_days: int = 180,
        include_public: bool = True,
        target_count: int = 200,
        cooldown_seconds: tuple = (3, 8),
        product: str = "Latest",
    ) -> Dict[str, Dict]:
        """Scrape all configured parties"""
        results = {}

        for party in POLITICAL_HANDLES_BY_PARTY.keys():
            logger.info(f"Starting scrape for {party}")
            try:
                stats = await self.scrape_party_tweets(
                    db,
                    party=party,
                    language=language,
                    since_days=since_days,
                    include_public=include_public,
                    target_count=target_count,
                    cooldown_seconds=cooldown_seconds,
                    product=product,
                )
                results[party] = stats
            except Exception as e:
                logger.error(f"Failed to scrape {party}: {e}")
                results[party] = {'error': str(e)}
        
        return results


# Global instance
twitter_service = TwitterService()
