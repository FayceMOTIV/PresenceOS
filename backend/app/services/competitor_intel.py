"""
PresenceOS — Competitor Intelligence (Feature 5)

Social media competitive analysis:
- Track competitor profiles and metrics
- Benchmark your brand against competitors
- Identify competitor content strategies
- Gap analysis and recommendations

In dev mode, returns mock competitor data for restaurant context.
"""
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

logger = structlog.get_logger()

_MOCK_COMPETITORS = [
    {
        "name": "Burger Palace",
        "handle": "@burgerpalace",
        "platform": "instagram",
        "followers": 5200,
        "engagement_rate": 3.8,
        "post_frequency": 5,
        "top_content": "Photos burger gourmet + stories coulisses",
        "strength": "Branding visuel fort, feed coherent",
        "weakness": "Peu d'interaction en commentaires",
    },
    {
        "name": "Le Gourmet Lab",
        "handle": "@legourmetlab",
        "platform": "instagram",
        "followers": 3800,
        "engagement_rate": 5.1,
        "post_frequency": 7,
        "top_content": "Reels preparation + ASMR",
        "strength": "Fort engagement, communaute active",
        "weakness": "Frequence irreguliere",
    },
    {
        "name": "Pizza Napoli",
        "handle": "@pizzanapoli",
        "platform": "instagram",
        "followers": 8900,
        "engagement_rate": 2.9,
        "post_frequency": 3,
        "top_content": "Photos ambiance + offres promo",
        "strength": "Large audience, marque reconnue",
        "weakness": "Contenu peu original, engagement faible",
    },
]

# In-memory competitor tracking
_tracked: dict[str, list[dict]] = {}


class CompetitorIntelService:
    """Analyze and track competitor social media activity."""

    def _ensure_competitors(self, brand_id: str) -> list[dict]:
        """Ensure mock competitor data exists for a brand."""
        if brand_id not in _tracked:
            competitors = []
            for mock in _MOCK_COMPETITORS:
                competitors.append({
                    "id": str(uuid.uuid4()),
                    "brand_id": brand_id,
                    **mock,
                    "tracked_since": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 90))).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                })
            _tracked[brand_id] = competitors
        return _tracked[brand_id]

    def get_competitors(self, brand_id: str) -> list[dict[str, Any]]:
        """List tracked competitors."""
        return self._ensure_competitors(brand_id)

    def add_competitor(
        self, brand_id: str, name: str, handle: str, platform: str = "instagram"
    ) -> dict[str, Any]:
        """Add a competitor to track."""
        competitors = self._ensure_competitors(brand_id)
        new_comp = {
            "id": str(uuid.uuid4()),
            "brand_id": brand_id,
            "name": name,
            "handle": handle,
            "platform": platform,
            "followers": random.randint(500, 10000),
            "engagement_rate": round(random.uniform(1.5, 7.0), 1),
            "post_frequency": random.randint(2, 10),
            "top_content": "En cours d'analyse...",
            "strength": "En cours d'analyse...",
            "weakness": "En cours d'analyse...",
            "tracked_since": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        competitors.append(new_comp)
        return new_comp

    def remove_competitor(self, brand_id: str, competitor_id: str) -> bool:
        """Remove a tracked competitor."""
        competitors = self._ensure_competitors(brand_id)
        before = len(competitors)
        _tracked[brand_id] = [c for c in competitors if c["id"] != competitor_id]
        return len(_tracked[brand_id]) < before

    def get_benchmark(self, brand_id: str) -> dict[str, Any]:
        """Compare your brand metrics against competitors."""
        competitors = self._ensure_competitors(brand_id)
        your_metrics = {
            "followers": 2450,
            "engagement_rate": 4.2,
            "post_frequency": 4,
        }

        avg_followers = sum(c["followers"] for c in competitors) / len(competitors) if competitors else 0
        avg_engagement = sum(c["engagement_rate"] for c in competitors) / len(competitors) if competitors else 0
        avg_frequency = sum(c["post_frequency"] for c in competitors) / len(competitors) if competitors else 0

        return {
            "brand_id": brand_id,
            "your_metrics": your_metrics,
            "competitor_avg": {
                "followers": round(avg_followers),
                "engagement_rate": round(avg_engagement, 1),
                "post_frequency": round(avg_frequency, 1),
            },
            "ranking": {
                "followers": sum(1 for c in competitors if c["followers"] < your_metrics["followers"]) + 1,
                "engagement": sum(1 for c in competitors if c["engagement_rate"] < your_metrics["engagement_rate"]) + 1,
                "total_competitors": len(competitors),
            },
            "gaps": [
                "Augmentez votre frequence de publication (+1 post/semaine)",
                "Votre engagement est au-dessus de la moyenne — capitalisez !",
                "Testez les Reels ASMR comme Le Gourmet Lab",
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
