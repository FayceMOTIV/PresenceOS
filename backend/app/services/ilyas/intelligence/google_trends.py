"""
Ilyas Intelligence — Google Trends Module
Uses pytrends (free, no API key) to detect food & restaurant trends in France.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class GoogleTrendsIntel:
    """Google Trends intelligence for restaurant/food topics."""

    def __init__(self) -> None:
        self._pytrends = None

    def _get_client(self):
        if self._pytrends is None:
            from pytrends.request import TrendReq
            self._pytrends = TrendReq(hl="fr-FR", tz=60)
        return self._pytrends

    def _fetch_trending_now(self, category: str = "restaurant") -> dict:
        """Fetch current trending searches related to food/restaurant in France."""
        try:
            pt = self._get_client()

            keywords = [category]
            pt.build_payload(keywords, cat=0, timeframe="now 7-d", geo="FR")
            related = pt.related_queries()

            result = {
                "keyword": category,
                "timestamp": datetime.utcnow().isoformat(),
                "rising": [],
                "top": [],
            }

            if category in related:
                rising_df = related[category].get("rising")
                if rising_df is not None and not rising_df.empty:
                    result["rising"] = rising_df.head(10).to_dict("records")

                top_df = related[category].get("top")
                if top_df is not None and not top_df.empty:
                    result["top"] = top_df.head(10).to_dict("records")

            return result
        except Exception as e:
            logger.warning("Google Trends fetch failed: %s", e)
            return {"keyword": category, "error": str(e), "rising": [], "top": []}

    def _fetch_interest_over_time(self, keywords: list[str]) -> dict:
        """Fetch interest over time for specific keywords."""
        try:
            pt = self._get_client()
            pt.build_payload(keywords[:5], timeframe="today 3-m", geo="FR")
            df = pt.interest_over_time()

            if df.empty:
                return {"keywords": keywords, "data": []}

            records = []
            for col in keywords[:5]:
                if col in df.columns:
                    records.append({
                        "keyword": col,
                        "avg_interest": int(df[col].mean()),
                        "max_interest": int(df[col].max()),
                        "trend": "up" if df[col].iloc[-1] > df[col].iloc[0] else "down",
                    })
            return {"keywords": keywords, "data": records}
        except Exception as e:
            logger.warning("Google Trends interest_over_time failed: %s", e)
            return {"keywords": keywords, "error": str(e), "data": []}

    async def get_food_trends(self, category: str = "restaurant") -> dict:
        """Get trending food/restaurant searches in France (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._fetch_trending_now, category)

    async def compare_keywords(self, keywords: list[str]) -> dict:
        """Compare interest for multiple keywords over 3 months (async wrapper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self._fetch_interest_over_time, keywords)
