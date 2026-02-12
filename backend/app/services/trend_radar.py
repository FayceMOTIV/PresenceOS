"""
PresenceOS — Trend Radar (Feature 8)

Detects local food trends and provides content suggestions with virality scores.
In dev mode, returns realistic mock trend data for restaurant industry.
"""
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

logger = structlog.get_logger()

_MOCK_TRENDS = [
    {
        "topic": "Bowl poke maison",
        "category": "food_trend",
        "virality_score": 92,
        "platforms": ["instagram", "tiktok"],
        "description": "Les bowls poke faits maison explosent sur TikTok. Le hashtag #pokebowl a depasse 5M de vues cette semaine.",
        "content_suggestion": "Filmez la preparation de votre bowl signature en 30s avec une transition avant/apres.",
        "hashtags": ["pokebowl", "healthyfood", "homemade", "foodtok"],
    },
    {
        "topic": "Menu secret",
        "category": "marketing_trend",
        "virality_score": 88,
        "platforms": ["instagram", "tiktok"],
        "description": "Les restaurants avec des menus secrets generent 3x plus d'engagement. Effet d'exclusivite.",
        "content_suggestion": "Creez un plat 'secret' disponible uniquement en mentionnant un code en story.",
        "hashtags": ["secretmenu", "menucanache", "foodie", "exclusive"],
    },
    {
        "topic": "ASMR food",
        "category": "content_format",
        "virality_score": 85,
        "platforms": ["tiktok", "instagram"],
        "description": "Les videos ASMR de preparation culinaire ont un taux de completion 2x superieur.",
        "content_suggestion": "Filmez le croquant de vos plats en gros plan avec un micro sensible.",
        "hashtags": ["asmrfood", "foodasmr", "satisfying", "croquant"],
    },
    {
        "topic": "Behind the scenes",
        "category": "content_format",
        "virality_score": 82,
        "platforms": ["instagram", "facebook", "tiktok"],
        "description": "Les coulisses de cuisine generent 45% plus d'engagement que les photos produit.",
        "content_suggestion": "Montrez votre chef en action pendant le rush du service.",
        "hashtags": ["behindthescenes", "cuisinepro", "cheflife", "coulisses"],
    },
    {
        "topic": "Plats de saison automne",
        "category": "seasonal",
        "virality_score": 78,
        "platforms": ["instagram", "facebook"],
        "description": "Les plats automne/hiver (soupes, gratins, fondues) voient un pic d'engagement en ce moment.",
        "content_suggestion": "Photographiez vos plats de saison avec une ambiance chaleureuse (bougies, bois).",
        "hashtags": ["platdesaison", "automne", "comfortfood", "saison"],
    },
    {
        "topic": "Eco-responsable",
        "category": "values_trend",
        "virality_score": 75,
        "platforms": ["linkedin", "instagram", "facebook"],
        "description": "Le contenu eco-responsable (local, anti-gaspi, bio) fidelize une audience croissante.",
        "content_suggestion": "Presentez vos fournisseurs locaux et votre demarche anti-gaspillage.",
        "hashtags": ["ecoresponsable", "circuitcourt", "antigaspi", "local"],
    },
    {
        "topic": "UGC client",
        "category": "marketing_trend",
        "virality_score": 72,
        "platforms": ["instagram", "tiktok"],
        "description": "Repartager le contenu de vos clients (UGC) booste la confiance de 40%.",
        "content_suggestion": "Encouragez vos clients a vous taguer et repostez les meilleures photos.",
        "hashtags": ["ugc", "clientsheureux", "repost", "communaute"],
    },
]


class TrendRadarService:
    """Detect and suggest content based on food industry trends."""

    def get_trends(
        self,
        brand_id: str,
        category: str | None = None,
        platform: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get trending topics relevant to the restaurant industry."""
        trends = []
        now = datetime.now(timezone.utc)

        for i, mock in enumerate(_MOCK_TRENDS):
            trend = {
                "id": str(uuid.uuid4()),
                "brand_id": brand_id,
                **mock,
                "detected_at": (now - timedelta(hours=random.randint(2, 72))).isoformat(),
                "expires_in_hours": random.randint(24, 168),
            }
            trends.append(trend)

        if category:
            trends = [t for t in trends if t["category"] == category]
        if platform:
            trends = [t for t in trends if platform in t["platforms"]]

        trends.sort(key=lambda t: t["virality_score"], reverse=True)
        return trends[:limit]

    def get_trend(self, trend_id: str) -> dict[str, Any] | None:
        """Get a specific trend — returns None in mock mode."""
        return None

    def get_categories(self) -> list[dict[str, str]]:
        """Get available trend categories."""
        return [
            {"id": "food_trend", "label": "Tendances food"},
            {"id": "marketing_trend", "label": "Marketing"},
            {"id": "content_format", "label": "Formats contenu"},
            {"id": "seasonal", "label": "Saisonnier"},
            {"id": "values_trend", "label": "Valeurs"},
        ]

    def get_summary(self, brand_id: str) -> dict[str, Any]:
        """Get a summary of current trend landscape."""
        trends = self.get_trends(brand_id)
        return {
            "brand_id": brand_id,
            "total_trends": len(trends),
            "top_trend": trends[0] if trends else None,
            "avg_virality": round(sum(t["virality_score"] for t in trends) / len(trends), 1) if trends else 0,
            "trending_platforms": ["tiktok", "instagram"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
