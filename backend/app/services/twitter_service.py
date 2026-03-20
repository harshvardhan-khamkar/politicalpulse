"""
Twitter Service
Integrates Twikit for Twitter scraping
Supports: party, handle, hashtag, bilingual, trending hashtag extraction
"""
import asyncio
import os
import re
import random
from dataclasses import dataclass
from collections import Counter
from datetime import datetime, timedelta
from threading import RLock
from typing import Any, Dict, List, Optional, Tuple
import logging
from sqlalchemy.orm import Session

from app.services.text_normalization import repair_mojibake

logger = logging.getLogger(__name__)

# ─── Political handle / term configuration ────────────────────────────────────

POLITICAL_HANDLES_BY_PARTY = {
    "BJP":  {"BJP4India", "narendramodi", "AmitShah", "JPNadda", "myogiadityanath", "PMOIndia", "rajnathsingh"},
    "INC":  {"INCIndia", "RahulGandhi", "kharge", "ShashiTharoor", "priyankagandhi", "JairamRamesh"},
    "AAP":  {"AamAadmiParty", "ArvindKejriwal", "raghav_chadha", "AtishiAAP", "BhagwantMann"},
    "SP":   {"samajwadiparty", "yadavakhilesh", "dimpleyadav"},
    "TMC":  {"AITCofficial", "MamataOfficial", "abhishekaitc"},
    "BSP":  {"BSP4India", "MayawatiSCBSP"},
    "CPIM": {"cpimspeak", "sitaramyechury"},
}

PUBLIC_TERMS_BY_PARTY = {
    "BJP":  ["narendramodi", "AmitShah", "BJP", "#BJP", "#ModiHaiToMumkinHai", "#NarendraModi", "Modi government"],
    "INC":  ["RahulGandhi", "#RahulGandhi", "#Congress", "#BharatJodoYatra", "INCIndia", "#Rahul"],
    "AAP":  ["ArvindKejriwal", "#Kejriwal", "#AAP", "#DelhiModel", "AamAadmiParty", "#ArvindKejriwal"],
    "SP":   ["akhilesh yadav", "#AkhileshYadav", "#SP", "samajwadi party"],
    "TMC":  ["mamata banerjee", "#MamataBanerjee", "#TMC", "#AllIndia TrinaMool"],
    "BSP":  ["mayawati", "#Mayawati", "#BSP", "#DalitPolitics"],
    "CPIM": ["sitaram yechury", "#CPIM", "#LeftFront"],
}

ALL_POLITICAL_HANDLES = {
    handle.lower() for handles in POLITICAL_HANDLES_BY_PARTY.values() for handle in handles
}
HANDLE_TO_PARTY = {
    handle.lower(): party
    for party, handles in POLITICAL_HANDLES_BY_PARTY.items()
    for handle in handles
}

# Hashtag regex for trending extraction
_HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)


@dataclass
class LiveTrendCacheEntry:
    payload: Dict[str, Any]
    cached_at: datetime


class TwitterService:
    """Twitter scraping service using Twikit"""

    LIVE_TRENDS_CACHE_TTL_SECONDS = 60 * 5

    def __init__(self, cookies_path: str = "cookies.json"):
        self.cookies_path = cookies_path
        self.client = None
        self.initialized = False
        self._live_trends_cache: Dict[Tuple[str, str, int, bool], LiveTrendCacheEntry] = {}
        self._live_trends_lock = RLock()

    async def _init_client(self, force_relogin: bool = False):
        """Initialize Twikit client with cookies or fallback to .env credentials"""
        if self.initialized and not force_relogin:
            return
        self.initialized = False
        try:
            from twikit import Client
            self.client = Client(language="en-US")
            if force_relogin or not os.path.exists(self.cookies_path):
                import os
                logger.warning("Attempting Twikit login via .env credentials...")
                username = os.environ.get("TWITTER_USERNAME", "syman763255")
                email = os.environ.get("TWITTER_EMAIL", "spymanxavier@gmail.com")
                password = os.environ.get("TWITTER_PASSWORD", "9421150039")
                await self.client.login(auth_info_1=username, auth_info_2=email, password=password)
                self.client.save_cookies(self.cookies_path)
            else:
                self.client.load_cookies(self.cookies_path)
            self.initialized = True
            logger.info("Twitter client initialized successfully")
        except ImportError:
            logger.error("Twikit not installed. Install with: pip install twikit")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {e}")
            raise

    # ─── Query builders ───────────────────────────────────────────────────────

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
        handle_clause = " OR ".join(f"from:{h}" for h in handles)
        lang_fragment = "" if language == "all" else f" lang:{language}"
        return f"({handle_clause}){lang_fragment}{self._build_since_fragment(since_days)}"

    def _build_public_query(self, terms: List[str], language: str, since_days: int) -> str:
        terms_clause = " OR ".join(terms)
        lang_fragment = "" if language == "all" else f" lang:{language}"
        return f"({terms_clause}){lang_fragment}{self._build_since_fragment(since_days)}"

    def _build_hashtag_query(self, hashtag: str, language: str, since_days: int) -> str:
        """Build a search query for a specific hashtag or keyword."""
        tag = hashtag.strip()
        if not tag.startswith("#"):
            tag = f"#{tag}"
        lang_fragment = "" if language == "all" else f" lang:{language}"
        return f"{tag}{lang_fragment}{self._build_since_fragment(since_days)}"

    @staticmethod
    def _normalize_trend_location(location_name: Optional[str]) -> str:
        return (location_name or "").strip().casefold()

    @staticmethod
    def _extract_numeric_volume(value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value
        if value is None:
            return None

        text = str(value).strip().lower().replace(",", "")
        match = re.search(r"(\d+(?:\.\d+)?)\s*([km]?)", text)
        if not match:
            return None

        number = float(match.group(1))
        suffix = match.group(2)
        multiplier = 1_000 if suffix == "k" else 1_000_000 if suffix == "m" else 1
        return int(number * multiplier)

    def _resolve_trends_location(
        self,
        locations: List[Any],
        country_code: str = "IN",
        location_name: Optional[str] = None,
    ) -> Optional[Any]:
        normalized_country = (country_code or "").strip().upper()
        normalized_location = self._normalize_trend_location(location_name)

        if normalized_location:
            for location in locations:
                if self._normalize_trend_location(getattr(location, "name", "")) != normalized_location:
                    continue
                location_country_code = (getattr(location, "country_code", "") or "").upper()
                if normalized_country and location_country_code != normalized_country:
                    continue
                return location

        country_matches = [
            location
            for location in locations
            if not normalized_country or (getattr(location, "country_code", "") or "").upper() == normalized_country
        ]
        if not country_matches:
            return None

        for location in country_matches:
            place_type = getattr(location, "placeType", {}) or {}
            if str(place_type.get("name", "")).casefold() == "country":
                return location
            if self._normalize_trend_location(getattr(location, "name", "")) == self._normalize_trend_location(
                getattr(location, "country", "")
            ):
                return location

        return country_matches[0]

    def _get_cached_live_trends(
        self,
        cache_key: Tuple[str, str, int, bool],
    ) -> Optional[Dict[str, Any]]:
        with self._live_trends_lock:
            entry = self._live_trends_cache.get(cache_key)
            if not entry:
                return None

            age_seconds = (datetime.utcnow() - entry.cached_at).total_seconds()
            if age_seconds > self.LIVE_TRENDS_CACHE_TTL_SECONDS:
                self._live_trends_cache.pop(cache_key, None)
                return None

            return entry.payload

    def _store_cached_live_trends(
        self,
        cache_key: Tuple[str, str, int, bool],
        payload: Dict[str, Any],
    ) -> None:
        with self._live_trends_lock:
            self._live_trends_cache[cache_key] = LiveTrendCacheEntry(
                payload=payload,
                cached_at=datetime.utcnow(),
            )

    @staticmethod
    def _build_live_trend_item(
        name: str,
        volume: Optional[int],
        url: Optional[str] = None,
        query: Optional[str] = None,
        grouped_trends: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return {
            "hashtag": name,
            "count": volume or 0,
            "score": volume or 0,
            "volume_label": f"{volume:,} posts" if volume else "Live trend",
            "tweet_volume": volume,
            "url": url,
            "query": query,
            "grouped_trends": grouped_trends or [],
            "top_party": None,
            "party_distribution": {},
        }

    async def get_live_trending_hashtags(
        self,
        country_code: str = "IN",
        location_name: Optional[str] = None,
        count: int = 15,
        hashtags_only: bool = True,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Retrieve live trending items directly from Twitter/X.

        Defaults to India-level trends when possible.
        """
        await self._init_client()

        normalized_country = (country_code or "IN").strip().upper()
        normalized_location = self._normalize_trend_location(location_name)
        cache_key = (normalized_country, normalized_location, int(count), bool(hashtags_only))

        if use_cache:
            cached = self._get_cached_live_trends(cache_key)
            if cached:
                return cached

        live_items: List[Dict[str, Any]] = []
        resolved_location_label = None
        as_of = None

        locations = await self.client.get_available_locations()
        location = self._resolve_trends_location(
            locations,
            country_code=normalized_country,
            location_name=location_name,
        )

        if location is not None:
            place_trends = await self.client.get_place_trends(location.woeid)
            as_of = place_trends.get("as_of")
            resolved_location_label = location.name
            for trend in place_trends.get("trends", []):
                name = getattr(trend, "name", "") or ""
                if hashtags_only and not name.startswith("#"):
                    continue
                live_items.append(
                    self._build_live_trend_item(
                        name=name,
                        volume=self._extract_numeric_volume(getattr(trend, "tweet_volume", None)),
                        url=getattr(trend, "url", None),
                        query=getattr(trend, "query", None),
                    )
                )

        if len(live_items) < count:
            general_trends = await self.client.get_trends(
                "trending",
                count=max(count * 3, 30),
                retry=False,
                additional_request_params={"candidate_source": "trends"},
            )
            for trend in general_trends:
                name = getattr(trend, "name", "") or ""
                if hashtags_only and not name.startswith("#"):
                    continue
                if any(existing["hashtag"].casefold() == name.casefold() for existing in live_items):
                    continue
                live_items.append(
                    self._build_live_trend_item(
                        name=name,
                        volume=self._extract_numeric_volume(getattr(trend, "tweets_count", None)),
                        grouped_trends=getattr(trend, "grouped_trends", None),
                    )
                )

        live_items = live_items[:count]
        total_items = len(live_items)
        for index, item in enumerate(live_items):
            if not item["score"]:
                item["score"] = max(total_items - index, 1)

        payload = {
            "source": "twitter_live",
            "is_live": True,
            "location": resolved_location_label or normalized_country,
            "as_of": as_of,
            "hashtags": live_items,
        }

        if use_cache:
            self._store_cached_live_trends(cache_key, payload)

        return payload

    # ─── Core scrape loop ────────────────────────────────────────────────────

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
        from app.services.alignment_model_service import alignment_model_service
        from twikit import TooManyRequests

        target_handle_set = {
            self._normalize_handle(h).lower()
            for h in (target_handles or [])
            if str(h).strip()
        }

        stats = {"total_fetched": 0, "new_inserted": 0, "duplicates": 0, "queries": len(queries)}

        for query_idx, query in enumerate(queries):
            logger.info(f"Twitter scrape query {query_idx + 1}/{len(queries)}: {query}")
            collected = 0
            tweets = None

            while collected < target_count:
                try:
                    if tweets is None:
                        try:

                            tweets = await self.client.search_tweet(query, product)

                        except Exception as e:

                            if "KEY_BYTE" in str(e):

                                logger.warning("KEY_BYTE error — refreshing client and retrying")

                                await self._init_client(force_relogin=True)

                                import asyncio

                                await asyncio.sleep(5)

                                try:

                                    tweets = await self.client.search_tweet(query, product)

                                except Exception as retry_e:

                                    logger.error(f"Retry also failed: {retry_e}")

                                    continue

                            else:

                                logger.error(f"Query failed: {e}")

                                continue
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
                        content = repair_mojibake(content)

                        user_obj = getattr(tweet, "user", None)
                        screen_name = (getattr(user_obj, "screen_name", "") or "").strip()
                        screen_name_key = screen_name.lower()

                        source_type = (
                            "political"
                            if screen_name_key in ALL_POLITICAL_HANDLES or screen_name_key in target_handle_set
                            else "public"
                        )

                        inferred_party = party or self._resolve_party_from_username(screen_name)
                        forced_lang = language if language in {"en", "hi"} else None
                        sentiment = sentiment_analyzer.analyze_sentiment(content, forced_lang)
                        
                        # ML Alignment Prediction
                        aligned_party = None
                        aligned_conf = 0.0
                        if source_type == "public":
                            alg_res = alignment_model_service.predict_alignment(content)
                            aligned_party = alg_res.get("predicted_alignment", "Unknown")
                            aligned_conf = alg_res.get("alignment_confidence", 0.0)

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
                            predicted_alignment=aligned_party,
                            alignment_confidence=aligned_conf,
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
                    wait_time = rate_limit_reset - int(datetime.now().timestamp())
                    wait_time = max(10, wait_time + 5)
                    if wait_time > 300:
                        logger.warning(f"Twitter severely rate limited ({wait_time:.0f}s). Aborting early to prevent frontend timeout.")
                        stats["message"] = f"Rate limited. Returning partial results after waiting would take {wait_time:.0f}s."
                        return stats
                    logger.warning(f"Twitter rate limited. Waiting {wait_time:.0f}s...")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Twitter query failed: {e}")
                    db.rollback()
                    break

            logger.info(f"Completed query {query_idx + 1}: inserted {collected} posts")
            if query_idx < len(queries) - 1:
                wait_time = random.uniform(3, 7)
                logger.info(f"Query cooldown: {wait_time:.0f}s")
                await asyncio.sleep(wait_time)

        return stats

    # ─── Public scrape methods ────────────────────────────────────────────────

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
        """Scrape tweets for a political party (official handles + optional public conversation)."""
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
            db, queries=queries, party=party_key, target_handles=handles,
            language=language, target_count=target_count,
            cooldown_seconds=cooldown_seconds, product=product,
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

        normalized = list(dict.fromkeys(
            self._normalize_handle(h) for h in handles if h.strip()
        ))
        if not normalized:
            raise ValueError("handles must contain at least one valid handle")

        language = self._normalize_language(language)
        party_key = (party or "").strip().upper() or None
        queries = [self._build_handles_query(normalized, language=language, since_days=since_days)]

        stats = await self._scrape_queries(
            db, queries=queries, party=party_key, target_handles=normalized,
            language=language, target_count=target_count,
            cooldown_seconds=cooldown_seconds, product=product,
        )
        logger.info(f"Twitter handle scrape complete for {normalized}: {stats}")
        return stats

    async def scrape_hashtag(
        self,
        db: Session,
        hashtag: str,
        party: Optional[str] = None,
        language: str = "en",
        since_days: int = 7,
        target_count: int = 200,
        cooldown_seconds: tuple = (3, 8),
        product: str = "Latest",
    ) -> Dict[str, int]:
        """
        Scrape tweets matching a hashtag or keyword.

        Args:
            hashtag: Hashtag or keyword to search (e.g. '#BJP', 'Modi', '#OperationSindoor')
            party: Optional party to tag captured tweets with
            language: en, hi, or all
            since_days: Look-back window in days
            target_count: Target tweet count
            product: Latest or Top
        """
        await self._init_client()

        language = self._normalize_language(language)
        party_key = (party or "").strip().upper() or None

        query = self._build_hashtag_query(hashtag, language=language, since_days=since_days)
        logger.info(f"Hashtag scrape — query: {query}")

        stats = await self._scrape_queries(
            db, queries=[query], party=party_key, target_handles=[],
            language=language, target_count=target_count,
            cooldown_seconds=cooldown_seconds, product=product,
        )
        logger.info(f"Hashtag scrape complete for '{hashtag}': {stats}")
        return stats

    async def scrape_bilingual(
        self,
        db: Session,
        mode: str = "party",
        party: Optional[str] = None,
        handles: Optional[List[str]] = None,
        hashtag: Optional[str] = None,
        since_days: int = 30,
        target_count: int = 200,
        include_public: bool = True,
        product: str = "Latest",
    ) -> Dict[str, Dict]:
        """
        Run scraping in BOTH English and Hindi in a single call.

        Args:
            mode: 'party' | 'handle' | 'hashtag'
            party: Party name (for mode='party')
            handles: List of handles (for mode='handle')
            hashtag: Hashtag (for mode='hashtag')
            since_days, target_count, include_public, product: forwarded to the underlying scraper
        """
        results: Dict[str, Dict] = {}

        for lang in ("en", "hi"):
            logger.info(f"Bilingual scrape — language: {lang}")
            try:
                if mode == "party" and party:
                    stats = await self.scrape_party_tweets(
                        db, party=party, language=lang, since_days=since_days,
                        include_public=include_public, target_count=target_count, product=product,
                    )
                elif mode == "handle" and handles:
                    stats = await self.scrape_handles(
                        db, handles=handles, party=party, language=lang,
                        since_days=since_days, target_count=target_count, product=product,
                    )
                elif mode == "hashtag" and hashtag:
                    stats = await self.scrape_hashtag(
                        db, hashtag=hashtag, party=party, language=lang,
                        since_days=since_days, target_count=target_count, product=product,
                    )
                else:
                    stats = await self.scrape_all_parties(
                        db, language=lang, since_days=since_days,
                        include_public=include_public, target_count=target_count, product=product,
                    )
                results[lang] = stats
            except Exception as e:
                logger.error(f"Bilingual scrape failed for lang={lang}: {e}")
                results[lang] = {"error": str(e)}

        return results

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
        """Scrape all configured parties."""
        results = {}
        for party in POLITICAL_HANDLES_BY_PARTY.keys():
            logger.info(f"Starting scrape for {party}")
            try:
                stats = await self.scrape_party_tweets(
                    db, party=party, language=language, since_days=since_days,
                    include_public=include_public, target_count=target_count,
                    cooldown_seconds=cooldown_seconds, product=product,
                )
                results[party] = stats
            except Exception as e:
                logger.error(f"Failed to scrape {party}: {e}")
                results[party] = {"error": str(e)}
        return results

    # ─── Trending hashtags ────────────────────────────────────────────────────

    def get_trending_hashtags(
        self,
        db: Session,
        days: int = 1,
        limit: int = 15,
        party: Optional[str] = None,
        language: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Extract and rank trending hashtags from stored tweets.

        Parses #tag tokens from tweet content, counts occurrences,
        and enriches with total engagement (likes + retweets + replies).

        Returns a list of dicts: {hashtag, count, engagement, party_distribution}
        """
        from app.models.social_media import TwitterPost
        from sqlalchemy import desc

        cutoff = datetime.now() - timedelta(days=days)
        query = db.query(TwitterPost).filter(TwitterPost.posted_at >= cutoff)

        if party:
            query = query.filter(TwitterPost.party == party.upper())
        if language:
            query = query.filter(TwitterPost.language == language)
        if source_type:
            query = query.filter(TwitterPost.source_type == source_type)

        posts = query.all()

        # Count hashtags and accumulate engagement + party distribution
        hashtag_counts: Counter = Counter()
        hashtag_engagement: Dict[str, int] = {}
        hashtag_parties: Dict[str, Counter] = {}

        for post in posts:
            tags = _HASHTAG_RE.findall(post.content or "")
            engagement = (post.likes or 0) + (post.retweets or 0) + (post.replies or 0)
            for tag in tags:
                tag_lower = tag.lower()
                hashtag_counts[tag_lower] += 1
                hashtag_engagement[tag_lower] = hashtag_engagement.get(tag_lower, 0) + engagement
                if tag_lower not in hashtag_parties:
                    hashtag_parties[tag_lower] = Counter()
                if post.party:
                    hashtag_parties[tag_lower][post.party] += 1

        # Sort by count desc, then engagement
        top = sorted(
            hashtag_counts.items(),
            key=lambda x: (x[1], hashtag_engagement.get(x[0], 0)),
            reverse=True,
        )[:limit]

        return [
            {
                "hashtag": f"#{tag}",
                "count": count,
                "engagement": hashtag_engagement.get(tag, 0),
                "top_party": hashtag_parties[tag].most_common(1)[0][0] if hashtag_parties[tag] else None,
                "party_distribution": dict(hashtag_parties.get(tag, {})),
            }
            for tag, count in top
        ]


    # ─── Reply fetcher ────────────────────────────────────────────────────────

    async def fetch_tweet_replies(
        self, post_id: str, max_replies: int = 80
    ) -> list[dict]:
        """
        Fetch replies for a given tweet using twikit.

        Paginates via cursor.next() until max_replies is reached or no more pages.
        Filters noise: very short texts, pure @mention openers, and retweets.

        Returns a list of dicts ready to be inserted into TweetReply.
        """
        await self._init_client()
        replies: list[dict] = []

        try:
            tweet = await self.client.get_tweet_by_id(post_id)
            cursor = await tweet.replies()

            while cursor and len(replies) < max_replies:
                for reply in cursor:
                    text: str = (reply.text or "").strip()

                    # ── Noise filters ─────────────────────────────────────────
                    if len(text.split()) < 3:
                        continue  # too short (stickers, single words, emojis)
                    if text.startswith("RT "):
                        continue  # retweet — not an original reaction
                    words = text.split()
                    if text.startswith("@") and len(words) < 5:
                        continue  # pure @mention with no real content

                    replies.append(
                        {
                            "reply_id": str(reply.id),
                            "reply_username": getattr(reply.user, "screen_name", None),
                            "reply_content": text,
                            "reply_likes": int(getattr(reply, "favorite_count", 0) or 0),
                            "reply_posted_at": getattr(reply, "created_at", None),
                        }
                    )

                    if len(replies) >= max_replies:
                        break

                await asyncio.sleep(1.5)  # twikit rate-limit buffer between pages

                try:
                    cursor = await cursor.next()
                except Exception:
                    break  # no more pages or pagination error

        except Exception as exc:
            logger.warning(f"Reply fetch failed for tweet {post_id}: {exc}")

        logger.info(f"fetch_tweet_replies({post_id}): {len(replies)} replies collected")
        return replies


# Global instance
twitter_service = TwitterService()
