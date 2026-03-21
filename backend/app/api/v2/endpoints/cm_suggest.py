"""
PresenceOS - CM Suggest v2 Endpoint (Haiku Quick Replies)

Generates 2 fast reply suggestions using Claude Haiku 4.5.
Injects Mem0 context (search by received message) for brand-aware replies.

Model: EXCLUSIVELY claude-haiku-4-5-20251001 — real-time, cost-critical.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.core.config import settings
from app.middleware.rate_limit import limiter
from app.services.ilyas.memory import Mem0Memory

logger = structlog.get_logger()
router = APIRouter()

_mem0 = Mem0Memory()

HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Fallback replies if API call fails
FALLBACK_SUGGESTIONS = [
    "Merci pour votre message ! Nous revenons vers vous tres rapidement.",
    "Bonjour ! Merci de nous contacter, nous traitons votre demande.",
]


# ── Request / Response Models ──


class SuggestRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The received message to generate suggestions for.",
    )
    platform: str = Field(
        default="instagram",
        description="Source platform (instagram, facebook, google, etc.).",
    )
    context: str | None = Field(
        default=None,
        description="Additional context (e.g. previous messages in thread).",
    )


class SuggestResponse(BaseModel):
    suggestions: list[str]
    model: str = HAIKU_MODEL
    mem0_context_used: bool = False


# ── Helpers ──


async def _get_mem0_context(brand_id: str, query: str) -> str:
    """Search Mem0 for relevant brand context. Returns empty string on failure."""
    user_id = f"restaurant_{brand_id}"
    try:
        memories = await _mem0.search(query=query, user_id=user_id, limit=3)
        if not memories:
            return ""
        parts = [m.get("memory", m.get("text", "")) for m in memories if m.get("memory") or m.get("text")]
        return "\n".join(f"- {p}" for p in parts[:3])
    except Exception as exc:
        logger.warning("Mem0 search failed for suggest", brand_id=brand_id, error=str(exc))
        return ""


async def _call_haiku(message: str, platform: str, mem0_context: str, extra_context: str | None) -> list[str]:
    """Call Claude Haiku 4.5 to generate 2 reply suggestions."""
    import anthropic

    system_prompt = (
        "Tu es l'assistant CM (Community Manager) d'un restaurant. "
        "Genere exactement 2 reponses courtes et professionnelles au message client. "
        "Chaque reponse doit etre adaptee a la plateforme et au ton de la marque. "
        "Reponds UNIQUEMENT avec un JSON: {\"suggestions\": [\"reponse1\", \"reponse2\"]}"
    )

    user_content_parts = [f"Message recu sur {platform}:\n\"{message}\""]

    if mem0_context:
        user_content_parts.append(f"\nContexte de la marque (memoire):\n{mem0_context}")

    if extra_context:
        user_content_parts.append(f"\nContexte additionnel:\n{extra_context}")

    user_content_parts.append(
        "\nGenere 2 reponses differentes: "
        "une chaleureuse/personnelle, une professionnelle/concise. "
        "Maximum 200 caracteres chacune. En francais."
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": "\n".join(user_content_parts)}],
    )

    # Parse response
    text = response.content[0].text.strip()

    # Try JSON parse first
    import json
    try:
        parsed = json.loads(text)
        suggestions = parsed.get("suggestions", [])
        if isinstance(suggestions, list) and len(suggestions) >= 2:
            return [str(s) for s in suggestions[:2]]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # Fallback: split by newlines or numbered items
    lines = [l.strip().lstrip("0123456789.-) ") for l in text.split("\n") if l.strip()]
    if len(lines) >= 2:
        return lines[:2]

    # Last resort: return the full text as one suggestion + a generic one
    return [text[:200], FALLBACK_SUGGESTIONS[1]]


# ── Endpoint ──


@router.post("/{brand_id}/suggest")
@limiter.limit("60/minute")
async def suggest_replies(
    request: Request,
    brand_id: UUID,
    body: SuggestRequest,
    current_user: FirebaseUser,
    db: DBSession,
) -> SuggestResponse:
    """Generate 2 quick reply suggestions using Claude Haiku 4.5."""
    await verify_brand_access(str(brand_id), current_user, db)

    if not settings.anthropic_api_key:
        logger.warning("Anthropic API key not configured, returning fallback")
        return SuggestResponse(
            suggestions=FALLBACK_SUGGESTIONS,
            model=HAIKU_MODEL,
            mem0_context_used=False,
        )

    # 1. Fetch Mem0 context (non-blocking on failure)
    mem0_context = await _get_mem0_context(str(brand_id), body.message)

    # 2. Call Haiku
    try:
        suggestions = await _call_haiku(
            message=body.message,
            platform=body.platform,
            mem0_context=mem0_context,
            extra_context=body.context,
        )
        return SuggestResponse(
            suggestions=suggestions,
            model=HAIKU_MODEL,
            mem0_context_used=bool(mem0_context),
        )
    except Exception as exc:
        logger.error(
            "Haiku suggest failed",
            brand_id=str(brand_id),
            error=str(exc),
        )
        # Fallback: never crash, always return 2 suggestions
        return SuggestResponse(
            suggestions=FALLBACK_SUGGESTIONS,
            model=HAIKU_MODEL,
            mem0_context_used=False,
        )
