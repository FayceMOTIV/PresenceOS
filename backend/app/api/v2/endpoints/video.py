"""
PresenceOS — Video Assets API v2 (Sprint B3)

Save generated videos to S3 and publish to social media via Upload-Post.
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.services.video_asset_service import VideoAssetService

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response Models ────────────────────────────────────────


class SaveVideoRequest(BaseModel):
    fal_url: str = Field(..., min_length=10, max_length=2000, description="fal.ai temporary video URL")
    prompt: str = Field(..., min_length=1, max_length=1000)
    duration_seconds: int = Field(..., ge=5, le=15)
    aspect_ratio: str = Field(default="9:16")
    style: str = Field(default="cinematic")


class PublishVideoRequest(BaseModel):
    asset_id: str = Field(..., description="VideoAsset UUID")
    platform: str = Field(..., description="instagram | facebook | tiktok")
    caption: str = Field(..., min_length=1, max_length=2200)
    account_username: str = Field(..., min_length=1, max_length=100)


class VideoAssetResponse(BaseModel):
    id: str
    public_url: str
    prompt: str
    duration_seconds: int
    aspect_ratio: str
    style: str
    status: str
    platform: str | None
    caption: str | None
    post_url: str | None
    published_at: str | None
    created_at: str


def _asset_to_response(asset) -> dict[str, Any]:
    return {
        "id": str(asset.id),
        "public_url": asset.public_url,
        "prompt": asset.prompt,
        "duration_seconds": asset.duration_seconds,
        "aspect_ratio": asset.aspect_ratio,
        "style": asset.style,
        "status": asset.status,
        "platform": asset.platform,
        "caption": asset.caption,
        "post_url": asset.post_url,
        "published_at": asset.published_at.isoformat() if asset.published_at else None,
        "created_at": asset.created_at.isoformat(),
    }


# ── Endpoints ────────────────────────────────────────────────────────


@router.post(
    "/brands/{brand_id}/videos/save",
    response_model=VideoAssetResponse,
    summary="Save a generated video to S3",
)
@limiter.limit("10/minute")
async def save_video(
    request: Request,
    brand_id: str,
    body: SaveVideoRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Download video from fal.ai and persist to S3 storage."""
    brand = await verify_brand_access(brand_id, user, db)
    svc = VideoAssetService(db)

    try:
        asset = await svc.save_video(
            brand_id=brand.id,
            fal_url=body.fal_url,
            prompt=body.prompt,
            duration_seconds=body.duration_seconds,
            aspect_ratio=body.aspect_ratio,
            style=body.style,
        )
        return _asset_to_response(asset)
    except Exception as exc:
        logger.error("save_video failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc)[:200])


@router.post(
    "/brands/{brand_id}/videos/publish",
    response_model=VideoAssetResponse,
    summary="Publish a saved video to social media",
)
@limiter.limit("5/minute")
async def publish_video(
    request: Request,
    brand_id: str,
    body: PublishVideoRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Publish a saved video via Upload-Post to Instagram/Facebook/TikTok."""
    brand = await verify_brand_access(brand_id, user, db)

    if body.platform not in ("instagram", "facebook", "tiktok"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform must be instagram, facebook, or tiktok",
        )

    svc = VideoAssetService(db)

    # Verify asset belongs to this brand
    asset = await svc.get_asset(uuid.UUID(body.asset_id))
    if not asset or asset.brand_id != brand.id:
        raise HTTPException(status_code=404, detail="Video not found")

    asset = await svc.publish_video(
        asset_id=uuid.UUID(body.asset_id),
        platform=body.platform,
        caption=body.caption,
        account_username=body.account_username,
    )
    return _asset_to_response(asset)


@router.get(
    "/brands/{brand_id}/videos",
    summary="List saved videos for a brand",
)
@limiter.limit("30/minute")
async def list_videos(
    request: Request,
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """List all saved video assets for a brand."""
    brand = await verify_brand_access(brand_id, user, db)
    svc = VideoAssetService(db)
    assets = await svc.list_assets(brand.id)
    return {"videos": [_asset_to_response(a) for a in assets]}
