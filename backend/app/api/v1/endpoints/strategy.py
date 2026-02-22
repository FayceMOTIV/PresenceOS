"""
PresenceOS - Strategy API (Market Analysis)

Endpoints for AI-powered market analysis using GPT-4.
Provides niche-specific insights on trends, tone, hashtags,
posting times, and overall content strategy.

When a brand_id is provided, the analysis is hyper-personalized
using the Brand's name, type, description, audience, locations,
constraints, content pillars, and BrandVoice settings.
"""
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.middleware.rate_limit import limiter

from app.ai.market_analyzer import MarketAnalyzer
from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.brand import Brand

logger = structlog.get_logger()
router = APIRouter()

_analyzer: MarketAnalyzer | None = None


def _get_analyzer() -> MarketAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = MarketAnalyzer()
    return _analyzer


# ── Helpers ─────────────────────────────────────────────────────────────────


async def _load_brand_context(
    db: AsyncSession, brand_id: UUID, current_user,
) -> dict[str, Any]:
    """Load Brand + BrandVoice from DB and build a context dict for the AI.

    Verifies the current user has access to the brand's workspace before
    loading any data (prevents IDOR).
    """
    # Ownership check via deps.get_brand (raises 403/404)
    brand = await get_brand(brand_id, current_user, db)

    ctx: dict[str, Any] = {
        "name": brand.name,
        "brand_type": brand.brand_type.value if brand.brand_type else None,
        "description": brand.description,
        "target_persona": brand.target_persona,
        "locations": brand.locations,
        "constraints": brand.constraints,
        "content_pillars": brand.content_pillars,
    }

    if brand.voice:
        v = brand.voice
        ctx["voice"] = {
            "tone_formal": v.tone_formal,
            "tone_playful": v.tone_playful,
            "tone_bold": v.tone_bold,
            "tone_technical": v.tone_technical,
            "tone_emotional": v.tone_emotional,
            "example_phrases": v.example_phrases,
            "words_to_avoid": v.words_to_avoid,
            "words_to_prefer": v.words_to_prefer,
            "emojis_allowed": v.emojis_allowed,
            "max_emojis_per_post": v.max_emojis_per_post,
            "hashtag_style": v.hashtag_style,
            "primary_language": v.primary_language,
            "allow_english_terms": v.allow_english_terms,
            "custom_instructions": v.custom_instructions,
        }

    return ctx


# ── Request Models ──────────────────────────────────────────────────────────


class AnalyzeNicheRequest(BaseModel):
    niche: str = Field(..., min_length=2, max_length=200)
    location: str = Field(default="France", max_length=200)
    brand_id: UUID | None = Field(
        default=None,
        description="Optional brand ID for hyper-personalized analysis",
    )


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/analyze-niche")
@limiter.limit("5/minute")
async def analyze_niche(
    request: AnalyzeNicheRequest,
    current_user: CurrentUser,
    db: DBSession,
    http_request: Request = None,
) -> dict:
    """Run a full AI-powered market analysis for the given niche.

    Performs parallel GPT-4 analyses covering:
    - Emerging trends and consumer behaviors
    - Optimal brand communication tone
    - Top-performing hashtag strategy
    - Best posting times by platform
    - Comprehensive content strategy

    When brand_id is provided, every analysis is personalized using
    the brand's identity, audience, locations, and voice settings.

    Returns a consolidated report with a confidence score.
    """
    analyzer = _get_analyzer()

    # Load brand context if a brand_id was provided (with ownership check)
    brand_context: dict[str, Any] | None = None
    if request.brand_id:
        brand_context = await _load_brand_context(db, request.brand_id, current_user)

    try:
        analysis = await analyzer.analyze_niche(
            niche=request.niche,
            location=request.location,
            brand_context=brand_context,
        )
    except RuntimeError as exc:
        logger.error(
            "Market analysis configuration error",
            user_id=str(current_user.id),
            niche=request.niche,
            error=str(exc),
        )
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Market analysis failed",
            user_id=str(current_user.id),
            niche=request.niche,
            location=request.location,
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Market analysis failed. Please try again.",
        )

    return {"success": True, "analysis": analysis}
