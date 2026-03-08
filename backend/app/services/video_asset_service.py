"""
PresenceOS — Video Asset Service (Sprint B3)

Downloads fal.ai video → uploads to S3 → publishes via Upload-Post.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video_asset import VideoAsset, VideoAssetStatus
from app.services.storage import get_storage_service

logger = structlog.get_logger()


class VideoAssetService:
    """Manages video asset persistence and publishing."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save_video(
        self,
        brand_id: uuid.UUID,
        fal_url: str,
        prompt: str,
        duration_seconds: int,
        aspect_ratio: str = "9:16",
        style: str = "cinematic",
    ) -> VideoAsset:
        """Download video from fal.ai URL and persist to S3."""
        # Download video from fal.ai
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.get(fal_url)
            resp.raise_for_status()
            video_bytes = resp.content

        # Upload to S3
        storage = get_storage_service()
        key = storage.generate_key(str(brand_id), "video", f"video_{duration_seconds}s.mp4")
        result = await storage.upload_bytes(
            video_bytes, key, content_type="video/mp4"
        )

        asset = VideoAsset(
            brand_id=brand_id,
            storage_key=result["key"],
            public_url=result["url"],
            prompt=prompt,
            duration_seconds=duration_seconds,
            aspect_ratio=aspect_ratio,
            style=style,
            file_size=result["size"],
            fal_url=fal_url,
            status=VideoAssetStatus.SAVED.value,
        )
        self._db.add(asset)
        await self._db.commit()
        await self._db.refresh(asset)

        logger.info(
            "Video saved to S3",
            asset_id=str(asset.id),
            brand_id=str(brand_id),
            size=result["size"],
        )
        return asset

    async def publish_video(
        self,
        asset_id: uuid.UUID,
        platform: str,
        caption: str,
        account_username: str,
    ) -> VideoAsset:
        """Publish a saved video via Upload-Post."""
        result = await self._db.execute(
            select(VideoAsset).where(VideoAsset.id == asset_id)
        )
        asset = result.scalar_one_or_none()
        if not asset:
            raise ValueError(f"VideoAsset {asset_id} not found")

        asset.status = VideoAssetStatus.PUBLISHING.value
        asset.platform = platform
        asset.caption = caption
        await self._db.commit()

        try:
            from app.connectors.upload_post import UploadPostConnector

            connector = UploadPostConnector(platform=platform)
            publish_result = await connector.publish(
                access_token="",
                content={
                    "caption": caption,
                    "account_username": account_username,
                    "platform": platform,
                },
                media_urls=[asset.public_url],
            )

            asset.status = VideoAssetStatus.PUBLISHED.value
            asset.post_id = publish_result.get("post_id")
            asset.post_url = publish_result.get("post_url")
            asset.published_at = datetime.now(timezone.utc)
            asset.publish_error = None

            logger.info(
                "Video published",
                asset_id=str(asset.id),
                platform=platform,
                post_id=asset.post_id,
            )

        except Exception as exc:
            asset.status = VideoAssetStatus.FAILED.value
            asset.publish_error = str(exc)[:500]
            logger.error(
                "Video publish failed",
                asset_id=str(asset.id),
                error=str(exc),
            )

        await self._db.commit()
        await self._db.refresh(asset)
        return asset

    async def list_assets(
        self, brand_id: uuid.UUID, limit: int = 20
    ) -> list[VideoAsset]:
        """List video assets for a brand, most recent first."""
        result = await self._db.execute(
            select(VideoAsset)
            .where(VideoAsset.brand_id == brand_id)
            .order_by(VideoAsset.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_asset(self, asset_id: uuid.UUID) -> VideoAsset | None:
        """Get a single video asset by ID."""
        result = await self._db.execute(
            select(VideoAsset).where(VideoAsset.id == asset_id)
        )
        return result.scalar_one_or_none()
