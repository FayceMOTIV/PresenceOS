"""
PresenceOS — Instagram Hashtag Scoring Service

Uses the Instagram Graph API to score hashtags by engagement potential.
Requires a connected Instagram Business account (via brand's facebook_access_token).
Falls back to a heuristic scoring model when API is unavailable.
"""

import json
from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

# Cache in-memory (per-process, reset on deploy)
_HASHTAG_CACHE: dict[str, dict] = {}


class InstagramHashtagService:
    """Score Instagram hashtags using the Graph API or heuristic fallback."""

    def __init__(self, ig_business_id: str | None = None, access_token: str | None = None):
        self.ig_business_id = ig_business_id
        self.access_token = access_token

    async def score_hashtags(
        self, hashtags: list[str], max_results: int = 15
    ) -> list[dict[str, Any]]:
        """
        Score a list of hashtag strings.

        Returns sorted list: [{"tag": "#foodie", "media_count": 120000000, "score": 85}, ...]
        Score (0-100): based on media_count bucket (too small = low score, too large = low too).
        Sweet spot for restaurants: 100K-5M posts.
        """
        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        for tag_str in hashtags:
            tag = tag_str.lstrip("#").lower()
            if not tag or tag in seen:
                continue
            seen.add(tag)

            # Check in-memory cache
            if tag in _HASHTAG_CACHE:
                results.append(_HASHTAG_CACHE[tag])
                continue

            scored = await self._score_single(tag)
            if scored:
                _HASHTAG_CACHE[tag] = scored
                results.append(scored)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]

    async def _score_single(self, tag: str) -> dict[str, Any] | None:
        """Score a single hashtag via Graph API or heuristic."""
        media_count = await self._fetch_media_count(tag)

        if media_count is not None:
            score = self._compute_score(media_count)
            return {"tag": f"#{tag}", "media_count": media_count, "score": score}

        # Heuristic fallback based on tag characteristics
        score = self._heuristic_score(tag)
        return {"tag": f"#{tag}", "media_count": None, "score": score}

    async def _fetch_media_count(self, tag: str) -> int | None:
        """Fetch media count for a hashtag via Instagram Graph API."""
        if not self.ig_business_id or not self.access_token:
            return None

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                # Step 1: Search hashtag ID
                search_resp = await client.get(
                    f"{GRAPH_API_BASE}/ig_hashtag_search",
                    params={
                        "user_id": self.ig_business_id,
                        "q": tag,
                        "access_token": self.access_token,
                    },
                )
                search_resp.raise_for_status()
                search_data = search_resp.json()
                hashtag_ids = search_data.get("data", [])

                if not hashtag_ids:
                    return None

                hashtag_id = hashtag_ids[0]["id"]

                # Step 2: Get hashtag info (media_count)
                info_resp = await client.get(
                    f"{GRAPH_API_BASE}/{hashtag_id}",
                    params={
                        "fields": "media_count",
                        "access_token": self.access_token,
                    },
                )
                info_resp.raise_for_status()
                info_data = info_resp.json()
                return info_data.get("media_count")

        except Exception as exc:
            logger.warning("IG hashtag API failed", tag=tag, error=str(exc))
            return None

    @staticmethod
    def _compute_score(media_count: int) -> int:
        """
        Score hashtag by media count.

        Sweet spot for restaurant accounts (10K-50K followers):
        - < 10K posts: too niche, low discoverability → 30-50
        - 10K-100K: good niche → 70-85
        - 100K-1M: ideal balance → 85-95
        - 1M-5M: high visibility, moderate competition → 75-85
        - 5M-50M: very competitive → 50-65
        - > 50M: oversaturated → 30-40
        """
        if media_count < 10_000:
            return 35
        elif media_count < 100_000:
            return 75
        elif media_count < 1_000_000:
            return 90
        elif media_count < 5_000_000:
            return 80
        elif media_count < 50_000_000:
            return 55
        else:
            return 35

    @staticmethod
    def _heuristic_score(tag: str) -> int:
        """Heuristic score when Graph API is unavailable."""
        # Longer hashtags tend to be more niche (better for small accounts)
        length_score = min(len(tag) * 5, 40) + 30

        # French food-related keywords boost
        food_keywords = {
            "food", "restaurant", "cuisine", "plat", "chef", "gastronomie",
            "recette", "menu", "terrasse", "brunch", "dessert", "pizza",
            "sushi", "burger", "bistrot", "brasserie",
        }
        if any(kw in tag for kw in food_keywords):
            length_score = min(length_score + 15, 85)

        # Location keywords boost
        if any(loc in tag for loc in ("paris", "lyon", "marseille", "bordeaux", "lille")):
            length_score = min(length_score + 10, 85)

        return min(length_score, 90)
