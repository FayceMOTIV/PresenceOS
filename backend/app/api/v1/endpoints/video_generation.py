"""
PresenceOS - Video Generation API (fal.ai Kling 3.0)

POST /video/generate — Generate a video from text prompt
GET  /video/credits/{brand_id} — Get remaining credits
GET  /video/history/{brand_id} — List generated videos
"""
import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.core.config import settings
from app.models.video_credits import VideoCredits, VideoPlan

logger = structlog.get_logger()
router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────

class GenerateVideoRequest(BaseModel):
    brand_id: str
    prompt: str = Field(..., min_length=5, max_length=1000)
    duration: int = Field(default=5, description="Duration in seconds: 5, 10, or 15")
    style: str = Field(default="cinematic", description="cinematic | natural | vibrant")


class VideoCreditsResponse(BaseModel):
    credits_remaining: int
    credits_total: int
    plan: str
    reset_date: str | None


class GenerateVideoResponse(BaseModel):
    video_url: str | None
    duration: int
    credits_used: int
    credits_remaining: int
    status: str  # "completed" | "failed" | "no_api_key"


# ── Style prompt modifiers ───────────────────────────────────────────

STYLE_MODIFIERS = {
    "cinematic": "cinematic lighting, shallow depth of field, film grain, warm tones, professional food photography style",
    "natural": "natural daylight, authentic, candid restaurant atmosphere, soft shadows, realistic",
    "vibrant": "vibrant saturated colors, high contrast, energetic, social media optimized, eye-catching",
}


# ── Helpers ──────────────────────────────────────────────────────────

def _credits_for_duration(duration: int) -> int:
    """Calculate credits needed: 1 credit per 5 seconds."""
    if duration <= 5:
        return 1
    if duration <= 10:
        return 2
    return 3  # 15s


async def _ensure_credits(brand_id: uuid.UUID, db) -> VideoCredits:
    """Get or create video credits for a brand."""
    result = await db.execute(
        select(VideoCredits).where(VideoCredits.brand_id == brand_id)
    )
    credits = result.scalar_one_or_none()

    if not credits:
        # Auto-create trial credits for new brands
        credits = VideoCredits(
            brand_id=brand_id,
            plan=VideoPlan.TRIAL.value,
            credits_remaining=10,
            credits_total=10,
        )
        db.add(credits)
        await db.commit()
        await db.refresh(credits)

    return credits


# ── Endpoints ────────────────────────────────────────────────────────


@router.get("/credits/{brand_id}")
async def get_credits(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> VideoCreditsResponse:
    """Get video credits for a brand."""
    await get_brand(brand_id, current_user, db)
    credits = await _ensure_credits(brand_id, db)

    return VideoCreditsResponse(
        credits_remaining=credits.credits_remaining,
        credits_total=credits.credits_total,
        plan=credits.plan,
        reset_date=credits.reset_date.isoformat() if credits.reset_date else None,
    )


@router.post("/generate")
async def generate_video(
    body: GenerateVideoRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> GenerateVideoResponse:
    """Generate a video using fal.ai Kling 3.0."""
    brand_id = uuid.UUID(body.brand_id)
    await get_brand(brand_id, current_user, db)

    # Validate duration
    if body.duration not in (5, 10, 15):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be 5, 10, or 15 seconds",
        )

    # Validate style
    if body.style not in STYLE_MODIFIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Style must be one of: {', '.join(STYLE_MODIFIERS.keys())}",
        )

    # Check credits
    credits = await _ensure_credits(brand_id, db)
    needed = _credits_for_duration(body.duration)

    if credits.credits_remaining < needed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Crédits insuffisants. {needed} requis, {credits.credits_remaining} restants.",
        )

    # Check FAL_KEY
    fal_key = getattr(settings, "fal_key", "") or ""
    if not fal_key:
        logger.warning("FAL_KEY not configured, video generation unavailable")
        return GenerateVideoResponse(
            video_url=None,
            duration=body.duration,
            credits_used=0,
            credits_remaining=credits.credits_remaining,
            status="no_api_key",
        )

    # Build enhanced prompt
    style_mod = STYLE_MODIFIERS[body.style]
    enhanced_prompt = f"{body.prompt}. {style_mod}"

    # Call fal.ai (async to avoid blocking the event loop)
    try:
        import os
        os.environ["FAL_KEY"] = fal_key
        import fal_client

        result = await fal_client.subscribe_async(
            "fal-ai/kling-video/v2.1/standard/text-to-video",
            arguments={
                "prompt": enhanced_prompt,
                "duration": str(body.duration),
                "aspect_ratio": "9:16",  # Mobile-first vertical
            },
        )

        video_url = result.get("video", {}).get("url") if isinstance(result, dict) else None

        if not video_url:
            logger.error("fal.ai returned no video URL", result=str(result)[:200])
            return GenerateVideoResponse(
                video_url=None,
                duration=body.duration,
                credits_used=0,
                credits_remaining=credits.credits_remaining,
                status="failed",
            )

        # Deduct credits
        credits.credits_remaining -= needed
        await db.commit()

        logger.info(
            "Video generated",
            brand_id=str(brand_id),
            duration=body.duration,
            credits_used=needed,
            credits_remaining=credits.credits_remaining,
        )

        return GenerateVideoResponse(
            video_url=video_url,
            duration=body.duration,
            credits_used=needed,
            credits_remaining=credits.credits_remaining,
            status="completed",
        )

    except Exception as exc:
        logger.error("Video generation failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Échec de la génération vidéo : {str(exc)[:200]}",
        )


@router.get("/history/{brand_id}")
async def get_video_history(
    brand_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Get video generation history (from proposals with video_url)."""
    from app.models.ai_proposal import AIProposal

    await get_brand(brand_id, current_user, db)

    result = await db.execute(
        select(AIProposal)
        .where(
            AIProposal.brand_id == brand_id,
            AIProposal.video_url.isnot(None),
        )
        .order_by(AIProposal.created_at.desc())
        .limit(20)
    )
    videos = result.scalars().all()

    return {
        "videos": [
            {
                "id": str(v.id),
                "video_url": v.video_url,
                "caption": v.caption,
                "status": v.status,
                "created_at": v.created_at.isoformat(),
            }
            for v in videos
        ]
    }
