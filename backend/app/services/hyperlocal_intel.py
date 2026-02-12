"""
PresenceOS — Hyperlocal Intelligence (Feature 10)

Contextual content suggestions based on:
- Local weather conditions
- Nearby events and holidays
- Seasonal food trends
- Day-of-week patterns

In dev mode, returns realistic mock data without external API calls.
"""
import random
from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

logger = structlog.get_logger()


def _mock_weather() -> dict[str, Any]:
    """Generate mock weather data."""
    conditions = [
        {"condition": "ensoleille", "temp": 24, "icon": "sun", "tip": "Mettez en avant votre terrasse et vos plats frais !"},
        {"condition": "nuageux", "temp": 18, "icon": "cloud", "tip": "Ambiance cosy — photo de plats chauds et reconfortants."},
        {"condition": "pluvieux", "temp": 14, "icon": "rain", "tip": "Jour de pluie = comfort food. Soupes, gratins, chocolat chaud."},
        {"condition": "froid", "temp": 5, "icon": "snow", "tip": "Mettez en avant les plats chauds et les boissons chaudes."},
    ]
    return random.choice(conditions)


def _mock_events() -> list[dict[str, Any]]:
    """Generate mock local events."""
    now = datetime.now(timezone.utc)
    events = [
        {
            "name": "Marche nocturne du centre-ville",
            "type": "market",
            "date": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            "distance_km": 0.5,
            "tip": "Annoncez votre participation ou vos offres speciales pour les visiteurs du marche.",
        },
        {
            "name": "Match de football (equipe locale)",
            "type": "sport",
            "date": (now + timedelta(days=4)).strftime("%Y-%m-%d"),
            "distance_km": 1.2,
            "tip": "Proposez un menu supporters ou une offre avant/apres match.",
        },
        {
            "name": "Festival de musique",
            "type": "festival",
            "date": (now + timedelta(days=7)).strftime("%Y-%m-%d"),
            "distance_km": 2.0,
            "tip": "Story avec ambiance festival + votre menu special evenement.",
        },
    ]
    return events


def _mock_seasonal() -> dict[str, Any]:
    """Generate seasonal context."""
    month = datetime.now().month
    if month in [12, 1, 2]:
        return {
            "season": "hiver",
            "trending_ingredients": ["truffe", "raclette", "chocolat chaud", "vin chaud"],
            "content_themes": ["comfort food", "fetes", "nouvel an", "cocooning"],
            "tip": "Les plats reconfortants et les ambiances chaleureuses performent le mieux en hiver.",
        }
    elif month in [3, 4, 5]:
        return {
            "season": "printemps",
            "trending_ingredients": ["asperges", "fraises", "menthe", "petit pois"],
            "content_themes": ["fraicheur", "terrasse", "brunch", "renouveau"],
            "tip": "Montrez la fraicheur de vos ingredients de saison et votre terrasse.",
        }
    elif month in [6, 7, 8]:
        return {
            "season": "ete",
            "trending_ingredients": ["tomate", "melon", "glace", "cocktails"],
            "content_themes": ["terrasse", "aperol", "salade", "barbecue"],
            "tip": "Le contenu estival (terrasse, soleil, couleurs vives) genere le plus d'engagement.",
        }
    else:
        return {
            "season": "automne",
            "trending_ingredients": ["potiron", "champignons", "chataignes", "gibier"],
            "content_themes": ["comfort food", "automne", "halloween", "beaujolais"],
            "tip": "Les couleurs chaudes et les plats de saison performent bien en automne.",
        }


def _mock_day_context() -> dict[str, Any]:
    """Generate day-of-week context."""
    day = datetime.now().strftime("%A").lower()
    contexts = {
        "monday": {"label": "Lundi", "tip": "Motivation lundi — montrez votre equipe en action.", "best_format": "story"},
        "tuesday": {"label": "Mardi", "tip": "Teasing du plat du jour en story pour midi.", "best_format": "story"},
        "wednesday": {"label": "Mercredi", "tip": "Milieu de semaine — menu enfant ou offre speciale.", "best_format": "post"},
        "thursday": {"label": "Jeudi", "tip": "Pre-weekend — annoncez vos evenements du weekend.", "best_format": "reel"},
        "friday": {"label": "Vendredi", "tip": "Ambiance weekend — afterwork, cocktails, terrasse.", "best_format": "reel"},
        "saturday": {"label": "Samedi", "tip": "Journee forte — stories en direct du service.", "best_format": "story"},
        "sunday": {"label": "Dimanche", "tip": "Brunch time — contenu convivial et familial.", "best_format": "post"},
    }
    return contexts.get(day, contexts["monday"])


class HyperlocalIntelService:
    """Provide hyperlocal contextual intelligence for content creation."""

    def get_context(self, brand_id: str, lat: float | None = None, lon: float | None = None) -> dict[str, Any]:
        """Get the full hyperlocal context for a brand."""
        weather = _mock_weather()
        events = _mock_events()
        seasonal = _mock_seasonal()
        day_ctx = _mock_day_context()

        # Generate content suggestions based on all context signals
        suggestions = self._generate_suggestions(weather, events, seasonal, day_ctx)

        return {
            "brand_id": brand_id,
            "weather": weather,
            "events": events,
            "seasonal": seasonal,
            "day_context": day_ctx,
            "suggestions": suggestions,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_weather(self, brand_id: str) -> dict[str, Any]:
        """Get just weather context."""
        return _mock_weather()

    def get_events(self, brand_id: str) -> list[dict[str, Any]]:
        """Get nearby events."""
        return _mock_events()

    def get_suggestions(self, brand_id: str) -> list[dict[str, Any]]:
        """Get content suggestions based on all context signals."""
        weather = _mock_weather()
        events = _mock_events()
        seasonal = _mock_seasonal()
        day_ctx = _mock_day_context()
        return self._generate_suggestions(weather, events, seasonal, day_ctx)

    def _generate_suggestions(
        self,
        weather: dict,
        events: list,
        seasonal: dict,
        day_ctx: dict,
    ) -> list[dict[str, Any]]:
        """Generate content suggestions from multiple context signals."""
        suggestions = []

        # Weather-based suggestion
        suggestions.append({
            "type": "weather",
            "priority": "high",
            "title": f"Meteo : {weather['condition']} ({weather['temp']}°C)",
            "suggestion": weather["tip"],
            "best_time": "12:00",
            "platforms": ["instagram", "facebook"],
        })

        # Event-based suggestions
        if events:
            closest = events[0]
            suggestions.append({
                "type": "event",
                "priority": "medium",
                "title": f"Evenement : {closest['name']}",
                "suggestion": closest["tip"],
                "best_time": "10:00",
                "platforms": ["instagram", "facebook", "gbp"],
            })

        # Seasonal suggestion
        suggestions.append({
            "type": "seasonal",
            "priority": "medium",
            "title": f"Saison : {seasonal['season'].capitalize()}",
            "suggestion": seasonal["tip"],
            "best_time": "11:00",
            "platforms": ["instagram"],
        })

        # Day-of-week suggestion
        suggestions.append({
            "type": "day",
            "priority": "low",
            "title": f"{day_ctx['label']}",
            "suggestion": day_ctx["tip"],
            "best_time": "09:00",
            "platforms": ["instagram", "story"],
        })

        return suggestions
