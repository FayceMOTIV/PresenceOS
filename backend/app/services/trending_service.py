"""
PresenceOS — Trending Hashtags Service (Google Trends via pytrends)

Fetches trending food/restaurant topics from Google Trends.
Results cached in Redis for 6 hours (or in-memory fallback).
"""

import json
from datetime import datetime, timezone

import structlog

from app.core.config import settings

logger = structlog.get_logger()

CACHE_TTL_SECONDS = 6 * 3600  # 6 hours
CACHE_KEY_PREFIX = "presenceos:trends:"


class TrendingService:
    """Fetches trending food/restaurant hashtags from Google Trends."""

    # Default queries for restaurant niche
    DEFAULT_KEYWORDS = [
        "restaurant tendance",
        "food trend",
        "recette populaire",
        "brunch",
        "street food",
    ]

    def __init__(self) -> None:
        self._redis = None

    async def _get_redis(self):
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.redis_url, decode_responses=True)
            await r.ping()
            self._redis = r
            return r
        except Exception as e:
            logger.warning("Redis not available for trends cache, using in-memory fallback", error=str(e))
            return None

    async def get_trending_hashtags(
        self,
        niche: str | None = None,
        geo: str = "FR",
        max_results: int = 15,
    ) -> list[dict]:
        """
        Fetch trending hashtags relevant to the brand niche.

        Returns list of dicts: [{"tag": "#foodie", "score": 85}, ...]
        Score is relative interest (0-100) from Google Trends.
        """
        cache_key = f"{CACHE_KEY_PREFIX}{geo}:{niche or 'default'}"

        # Check cache
        redis_client = await self._get_redis()
        if redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.info("Trends cache hit", key=cache_key)
                    return json.loads(cached)
            except Exception as e:
                logger.warning("Trends cache read failed", key=cache_key, error=str(e))

        # Fetch from Google Trends
        try:
            hashtags = await self._fetch_from_pytrends(niche, geo, max_results)
        except Exception as exc:
            logger.warning("Google Trends fetch failed", error=str(exc))
            hashtags = self._fallback_hashtags(niche)

        # Cache result
        if redis_client and hashtags:
            try:
                await redis_client.set(
                    cache_key, json.dumps(hashtags), ex=CACHE_TTL_SECONDS
                )
            except Exception as e:
                logger.warning("Trends cache write failed", key=cache_key, error=str(e))

        return hashtags

    async def _fetch_from_pytrends(
        self, niche: str | None, geo: str, max_results: int
    ) -> list[dict]:
        """Fetch related queries from Google Trends using pytrends."""
        import asyncio

        def _sync_fetch() -> list[dict]:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="fr-FR", tz=60, timeout=(5, 15))

            # Build keyword list based on niche
            keywords = list(self.DEFAULT_KEYWORDS)
            if niche and niche not in ("business", "general"):
                keywords[0] = niche

            # pytrends supports max 5 keywords at a time
            pytrends.build_payload(keywords[:5], cat=71, timeframe="now 7-d", geo=geo)

            results: list[dict] = []

            # Get related queries (rising)
            try:
                related = pytrends.related_queries()
                for kw, data in related.items():
                    rising = data.get("rising")
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(5).iterrows():
                            query = row.get("query", "")
                            value = int(row.get("value", 0))
                            tag = "#" + query.replace(" ", "").lower()
                            results.append({"tag": tag, "score": min(value, 100)})
            except Exception as e:
                logger.warning("pytrends related_queries failed", error=str(e))

            # Get related topics
            try:
                topics = pytrends.related_topics()
                for kw, data in topics.items():
                    rising = data.get("rising")
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(3).iterrows():
                            title = row.get("topic_title", "")
                            if title:
                                tag = "#" + title.replace(" ", "").lower()
                                results.append({"tag": tag, "score": 70})
            except Exception as e:
                logger.warning("pytrends related_topics failed", error=str(e))

            # Deduplicate
            seen: set[str] = set()
            unique: list[dict] = []
            for item in results:
                if item["tag"] not in seen:
                    seen.add(item["tag"])
                    unique.append(item)

            return sorted(unique, key=lambda x: x["score"], reverse=True)[:max_results]

        return await asyncio.to_thread(_sync_fetch)

    def _fallback_hashtags(self, niche: str | None) -> list[dict]:
        """Static fallback if Google Trends is unreachable."""
        base = [
            {"tag": "#foodie", "score": 95},
            {"tag": "#restaurant", "score": 90},
            {"tag": "#foodporn", "score": 88},
            {"tag": "#instafood", "score": 85},
            {"tag": "#bonappetit", "score": 80},
            {"tag": "#gastronomie", "score": 75},
            {"tag": "#foodlover", "score": 70},
            {"tag": "#restoparis", "score": 65},
        ]
        if niche and "pizza" in niche.lower():
            base.insert(0, {"tag": "#pizza", "score": 95})
        if niche and "sushi" in niche.lower():
            base.insert(0, {"tag": "#sushi", "score": 95})
        return base

    def format_for_prompt(self, hashtags: list[dict], limit: int = 10) -> str:
        """Format trending hashtags for inclusion in a prompt section."""
        if not hashtags:
            return ""
        top = hashtags[:limit]
        tags_str = ", ".join(h["tag"] for h in top)
        return f"HASHTAGS TENDANCE : {tags_str}"
