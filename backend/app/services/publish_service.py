"""
Publish Service RS3 — Unified video/content publishing.

Priority: Postiz self-hosted > Upload-Post API > warning.
IMPORTANT: meta.py and tiktok.py are SCAFFOLDS — never import them.
"""

import structlog

from app.core.config import settings
from app.core.observability import capture_exception

logger = structlog.get_logger()


def _postiz_configured() -> bool:
    """Check if Postiz is configured (URL + API key both present)."""
    return bool(settings.postiz_url and settings.postiz_api_key)


def _upload_post_configured() -> bool:
    """Check if Upload-Post is configured."""
    return bool(settings.upload_post_api_key)


async def publish_video_to_platform(
    video_url: str,
    caption: str,
    platform: str,
    brand_id: str,
    account_username: str = "",
    integration_id: str = "",
) -> dict:
    """Publish a video to a social platform using the best available provider.

    Priority chain:
        1. Postiz (if POSTIZ_URL + POSTIZ_API_KEY configured)
        2. Upload-Post (if UPLOAD_POST_API_KEY configured)
        3. Warning log — returns failure dict

    Args:
        video_url: S3 public URL of the video.
        caption: Post caption text.
        platform: Target platform (instagram, facebook, tiktok, etc.).
        brand_id: Brand UUID.
        account_username: Social account username (for Upload-Post).
        integration_id: Postiz integration ID (for Postiz).

    Returns:
        Dict with success, provider, post_id, post_url, error keys.
    """
    # -- 1. Try Postiz --
    if _postiz_configured():
        try:
            from app.services.postiz_service import PostizService

            if not integration_id:
                # Auto-detect integration for this brand + platform
                integ = await PostizService.get_integration_by_platform(brand_id, platform)
                if integ:
                    integration_id = integ.get("id", "")

            if integration_id:
                result = await PostizService.publish_now(
                    integration_ids=[integration_id],
                    content=caption,
                    media_urls=[video_url],
                )
                logger.info(
                    "publish.postiz_success",
                    brand_id=brand_id,
                    platform=platform,
                )
                return {
                    "success": True,
                    "provider": "postiz",
                    "post_id": result.get("id"),
                    "post_url": None,
                    "error": None,
                }
            else:
                logger.warning(
                    "publish.postiz_no_integration",
                    brand_id=brand_id,
                    platform=platform,
                )
                # Fall through to Upload-Post
        except Exception as exc:
            logger.error(
                "publish.postiz_failed",
                brand_id=brand_id,
                platform=platform,
                error=str(exc),
            )
            capture_exception(exc, {"context": "publish_service.postiz", "brand_id": brand_id})
            # Fall through to Upload-Post

    # -- 2. Try Upload-Post --
    if _upload_post_configured():
        try:
            from app.connectors.upload_post import UploadPostConnector

            connector = UploadPostConnector(platform=platform)
            result = await connector.publish(
                access_token="",
                content={
                    "caption": caption,
                    "account_username": account_username,
                    "platform": platform,
                },
                media_urls=[video_url],
            )
            logger.info(
                "publish.upload_post_success",
                brand_id=brand_id,
                platform=platform,
                post_id=result.get("post_id"),
            )
            return {
                "success": True,
                "provider": "upload_post",
                "post_id": result.get("post_id"),
                "post_url": result.get("post_url"),
                "error": None,
            }
        except Exception as exc:
            logger.error(
                "publish.upload_post_failed",
                brand_id=brand_id,
                platform=platform,
                error=str(exc),
            )
            capture_exception(exc, {"context": "publish_service.upload_post", "brand_id": brand_id})

    # -- 3. Nothing configured --
    logger.warning(
        "publish.no_provider_configured",
        brand_id=brand_id,
        platform=platform,
        hint="Set POSTIZ_URL+POSTIZ_API_KEY or UPLOAD_POST_API_KEY in environment.",
    )
    return {
        "success": False,
        "provider": None,
        "post_id": None,
        "post_url": None,
        "error": "No publishing provider configured. Set POSTIZ or UPLOAD_POST env vars.",
    }


async def save_video_as_draft(
    video_url: str,
    caption: str,
    brand_id: str,
    duration_seconds: int = 15,
    aspect_ratio: str = "9:16",
    style: str = "cinematic",
    db=None,
) -> dict:
    """Save a video as a draft VideoAsset (not yet published).

    Args:
        video_url: S3 public URL.
        caption: Draft caption.
        brand_id: Brand UUID string.
        duration_seconds: Video duration.
        aspect_ratio: Aspect ratio.
        style: Video style label.
        db: AsyncSession (required for DB operations).

    Returns:
        Dict with success, asset_id, status keys.
    """
    if db is None:
        logger.warning("save_video_as_draft.no_db_session")
        return {"success": False, "asset_id": None, "status": "error", "error": "No database session"}

    try:
        import uuid as _uuid
        from app.services.video_asset_service import VideoAssetService
        from app.models.video_asset import VideoAsset, VideoAssetStatus

        service = VideoAssetService(db)

        asset = VideoAsset(
            brand_id=_uuid.UUID(brand_id) if isinstance(brand_id, str) else brand_id,
            storage_key="",  # Already on S3, URL is the public_url
            public_url=video_url,
            prompt=caption,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            style=style,
            fal_url=None,
            status=VideoAssetStatus.SAVED.value,
        )
        db.add(asset)
        await db.commit()
        await db.refresh(asset)

        logger.info(
            "publish.draft_saved",
            brand_id=brand_id,
            asset_id=str(asset.id),
        )
        return {
            "success": True,
            "asset_id": str(asset.id),
            "status": "draft",
            "error": None,
        }
    except Exception as exc:
        logger.error("save_video_as_draft.failed", error=str(exc))
        capture_exception(exc, {"context": "publish_service.save_draft", "brand_id": brand_id})
        return {
            "success": False,
            "asset_id": None,
            "status": "error",
            "error": str(exc)[:200],
        }
