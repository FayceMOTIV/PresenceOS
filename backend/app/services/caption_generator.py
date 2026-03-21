"""
PresenceOS - Caption Generator with Brain Context
Bug Fix #3: generate_caption_with_brain() is a defined, importable function.
"""
import json
import uuid

import structlog
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.brand_brain import BrandBrain

logger = structlog.get_logger()

# ── Hashtag rules per platform ──────────────────────────────────
HASHTAG_RULES = {
    "instagram": {"min": 5, "max": 15, "style": "mix of popular and niche"},
    "tiktok": {"min": 3, "max": 5, "style": "trending and niche only"},
    "facebook": {"min": 0, "max": 3, "style": "minimal, broad"},
    "linkedin": {"min": 2, "max": 5, "style": "professional industry terms"},
}


async def generate_caption_with_brain(
    brand_id: uuid.UUID,
    db: AsyncSession,
    topic: str,
    platform: str = "instagram",
    brand_dna: dict | None = None,
    niche: str = "restaurant",
    tone: str = "engaging",
) -> dict:
    """
    Generate a caption using BrandBrain context.
    Returns: {"caption": str, "hashtags": list[str], "brain_context_used": bool}
    """
    brain = BrandBrain(brand_id, db)

    # Get brain context
    context = await brain.get_context_for_generation(topic, platform)
    has_context = len(context.get("relevant_memories", [])) > 0

    # Build system prompt
    memories_text = ""
    if has_context:
        memories_text = "\n".join([
            f"- {m['content']} (confidence: {m['confidence']})"
            for m in context["relevant_memories"][:5]
        ])

    rules_text = ""
    if context.get("content_rules"):
        rules_text = "\n".join([
            f"- {r['content']}"
            for r in context["content_rules"]
        ])

    dna_text = ""
    if brand_dna:
        dna_text = f"\nBrandDNA: {json.dumps(brand_dna, ensure_ascii=False)[:500]}"

    hashtag_config = HASHTAG_RULES.get(platform, HASHTAG_RULES["instagram"])

    if not settings.openai_api_key:
        return {
            "caption": f"[No API key] {topic}",
            "hashtags": [],
            "brain_context_used": False,
        }

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""Tu es un expert en copywriting pour {niche} sur {platform}.
Ton: {tone}. Langue: Français.

{"Souvenirs pertinents:" + chr(10) + memories_text if memories_text else ""}
{"Règles de contenu:" + chr(10) + rules_text if rules_text else ""}
{dna_text}

Hashtags: {hashtag_config['min']}-{hashtag_config['max']} ({hashtag_config['style']})

Réponds en JSON: {{"caption": "...", "hashtags": ["#tag1", "#tag2"]}}""",
            },
            {"role": "user", "content": f"Crée une légende pour: {topic}"},
        ],
        max_tokens=500,
        temperature=0.8,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content)
        return {
            "caption": data.get("caption", topic),
            "hashtags": data.get("hashtags", []),
            "brain_context_used": has_context,
        }
    except Exception as e:
        logger.error("Caption generation failed", error=str(e))
        return {"caption": topic, "hashtags": [], "brain_context_used": False}


async def generate_hashtags(
    topic: str,
    platform: str = "instagram",
    niche: str = "restaurant",
    count: int = 10,
) -> list[str]:
    """Generate hashtags for a topic."""
    if not settings.openai_api_key:
        return []

    config = HASHTAG_RULES.get(platform, HASHTAG_RULES["instagram"])
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"Génère {count} hashtags pour {niche} sur {platform}. Style: {config['style']}. Réponds en JSON: {{\"hashtags\": [\"#tag1\"]}}",
            },
            {"role": "user", "content": f"Sujet: {topic}"},
        ],
        max_tokens=200,
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    try:
        data = json.loads(response.choices[0].message.content)
        return data.get("hashtags", [])
    except Exception as e:
        logger.warning("Hashtag generation JSON parse failed", error=str(e))
        return []
