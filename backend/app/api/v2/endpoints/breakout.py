"""
PresenceOS — Breakout API v2 (V3 architecture)

Synchronous endpoint: photo upload -> rembg -> Remotion -> MP4 URL
~35-40s response time. No polling needed.

Keeps backward-compatible status endpoint (returns NOT_FOUND for old jobs).
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, status
from pydantic import BaseModel

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Response models ──────────────────────────────────────────────────────


class BreakoutResponse(BaseModel):
    video_url: str
    duration_seconds: int = 3
    original_url: Optional[str] = None
    cutout_url: Optional[str] = None


class BreakoutStatusResponse(BaseModel):
    job_id: str
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None
    progress: int = 0


# ── Main endpoint ────────────────────────────────────────────────────────


@router.post(
    "/{brand_id}/generate",
    summary="Upload photo -> Breakout MP4 (~35s)",
)
@limiter.limit("5/minute")
async def generate_breakout(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    photo: UploadFile = File(...),
    business_name: str = Form(default="Mon Restaurant"),
    instagram_handle: str = Form(default="@monrestaurant"),
    accent_color: str = Form(default="#F59E0B"),
):
    """
    Upload a photo -> rembg background removal -> Remotion render -> MP4.
    Returns video_url directly (no polling).
    """
    await verify_brand_access(brand_id, user, db)

    content_type = photo.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit etre une image (JPEG, PNG)",
        )

    contents = await photo.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image trop volumineuse (max 20 Mo)",
        )

    # Upload photo to fal.ai to get a public URL
    import fal_client
    from app.core.config import settings

    fal_key = settings.fal_key
    if fal_key:
        os.environ["FAL_KEY"] = fal_key

    suffix = ".jpg" if "jpeg" in content_type else ".png"

    def _upload_photo() -> str:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(contents)
            tmp = f.name
        try:
            return fal_client.upload_file(tmp)
        finally:
            os.unlink(tmp)

    image_url = await asyncio.to_thread(_upload_photo)

    # Run the V3 pipeline
    from app.services.breakout.breakout_engine import BreakoutEngine

    engine = BreakoutEngine()

    try:
        result = await engine.generate(
            image_url=image_url,
            business_name=business_name,
            likes_count=1200,
            instagram_handle=instagram_handle,
            accent_color=accent_color,
        )
    except Exception as exc:
        logger.error("Breakout V3 failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation echouee: {str(exc)[:200]}",
        )

    return BreakoutResponse(
        video_url=result["video_url"],
        duration_seconds=result.get("duration_seconds", 3),
        original_url=result.get("original_url"),
        cutout_url=result.get("cutout_url"),
    )


# ── Backward-compatible status endpoint (for old mobile versions) ────────


@router.get(
    "/{brand_id}/status/{job_id}",
    response_model=BreakoutStatusResponse,
    summary="Legacy status endpoint (V3 is synchronous)",
)
@limiter.limit("60/minute")
async def get_breakout_status(
    request: Request,
    brand_id: str,
    job_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Kept for backward compatibility. V3 is synchronous — no polling needed."""
    await verify_brand_access(brand_id, user, db)
    return BreakoutStatusResponse(job_id=job_id, status="NOT_FOUND", progress=0)
