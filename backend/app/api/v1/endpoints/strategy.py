"""
PresenceOS - Strategy API (Market Analysis)

Endpoints for AI-powered market analysis using GPT-4.
Provides niche-specific insights on trends, tone, hashtags,
posting times, and overall content strategy.
"""
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.market_analyzer import MarketAnalyzer
from app.api.v1.deps import CurrentUser, DBSession

logger = structlog.get_logger()
router = APIRouter()

_analyzer: MarketAnalyzer | None = None


def _get_analyzer() -> MarketAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = MarketAnalyzer()
    return _analyzer


# ── Request Models ──────────────────────────────────────────────────────────


class AnalyzeNicheRequest(BaseModel):
    niche: str
    location: str = "France"


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/analyze-niche")
async def analyze_niche(
    request: AnalyzeNicheRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Run a full AI-powered market analysis for the given niche.

    Performs 5 parallel GPT-4 analyses covering:
    - Emerging trends and consumer behaviors
    - Optimal brand communication tone
    - Top-performing hashtag strategy
    - Best posting times by platform
    - Comprehensive content strategy

    Returns a consolidated report with a confidence score.
    """
    analyzer = _get_analyzer()

    try:
        analysis = await analyzer.analyze_niche(
            niche=request.niche,
            location=request.location,
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
            detail=f"Market analysis failed: {str(exc)}",
        )

    return {"success": True, "analysis": analysis}
