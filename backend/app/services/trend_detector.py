"""
PresenceOS - Trend Detector Service
Detects trending topics and events relevant to the brand's niche.
Uses GPT-4o-mini for analysis.
"""
import json
import structlog
from datetime import datetime, timezone

from openai import AsyncOpenAI
from app.core.config import settings
from app.services.calendar_service import get_upcoming_events

logger = structlog.get_logger()


async def detect_trends(
    niche: str = "restaurant",
    location: str = "France",
    season: str | None = None,
) -> dict:
    """Detect current trends relevant to the niche."""
    if not settings.openai_api_key:
        return {"trends": [], "error": "No API key"}

    if season is None:
        month = datetime.now(timezone.utc).month
        seasons = {1: "hiver", 2: "hiver", 3: "printemps", 4: "printemps",
                   5: "printemps", 6: "été", 7: "été", 8: "été",
                   9: "automne", 10: "automne", 11: "automne", 12: "hiver"}
        season = seasons.get(month, "")

    # Include upcoming calendar events for context
    events = get_upcoming_events(days_ahead=14)
    events_text = ", ".join([e["name"] for e in events[:5]]) if events else "aucun événement proche"

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Tu es un expert en tendances social media pour le secteur {niche} en {location}. "
                    f"Saison actuelle: {season}. "
                    f"Événements à venir: {events_text}. "
                    "Génère 5-8 tendances actuelles pour du contenu Instagram/TikTok. "
                    "Réponds en JSON."
                ),
            },
            {
                "role": "user",
                "content": f"Quelles sont les tendances actuelles pour un {niche} en {location} ? "
                           f"JSON: {{\"trends\": [{{\"topic\": \"...\", \"hashtags\": [\"#...\"], \"content_idea\": \"...\", \"urgency\": \"high|medium|low\"}}]}}",
            },
        ],
        max_tokens=600,
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content)
        trends = data.get("trends", [])
        logger.info("Trends detected", niche=niche, count=len(trends))
        return {"trends": trends, "season": season, "events_context": events_text}
    except Exception as e:
        logger.error("Trend detection failed", error=str(e))
        return {"trends": [], "error": str(e)}


async def get_trending_content_ideas(
    niche: str = "restaurant",
    count: int = 3,
) -> list[dict]:
    """Get specific content ideas based on current trends."""
    result = await detect_trends(niche=niche)
    trends = result.get("trends", [])

    # Sort by urgency
    urgency_order = {"high": 0, "medium": 1, "low": 2}
    trends.sort(key=lambda t: urgency_order.get(t.get("urgency", "low"), 2))

    return trends[:count]
