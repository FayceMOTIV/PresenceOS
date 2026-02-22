"""
PresenceOS - Asset Processor Service (Content Library)

Handles media upload processing: S3 storage, thumbnail generation,
AI quality scoring, and fal.ai FLUX Kontext photo improvement.
"""
import io
import json
import uuid
from datetime import datetime, timezone

import httpx
import structlog
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.media import MediaAsset, ProcessingStatus
from app.services.storage import get_storage_service

logger = structlog.get_logger()

THUMBNAIL_SIZE = (300, 300)


class AssetProcessorService:
    """Processes uploaded media assets: thumbnails, quality scoring, AI improvement."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage_service()

    async def process_upload(
        self,
        brand_id: str,
        asset_id: str,
        file_bytes: bytes,
        content_type: str,
    ) -> MediaAsset:
        """Process an uploaded asset: upload to S3, generate thumbnail,
        estimate quality via Claude Vision, set status to ready.

        Triggers KB rebuild on completion.
        """
        stmt = select(MediaAsset).where(MediaAsset.id == asset_id)
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        asset.processing_status = ProcessingStatus.PROCESSING.value

        try:
            # Upload original to S3
            key = self.storage.generate_key(str(brand_id), "media", asset.original_filename or "upload")
            upload_result = await self.storage.upload_bytes(
                file_bytes, key, content_type
            )
            asset.storage_key = key
            asset.public_url = upload_result["url"]

            # Generate thumbnail
            if content_type.startswith("image/"):
                thumbnail_url = await self._generate_thumbnail(
                    file_bytes, brand_id, key
                )
                if thumbnail_url:
                    asset.thumbnail_url = thumbnail_url

            # Estimate quality via Claude Vision
            if content_type.startswith("image/"):
                quality = await self._estimate_quality(file_bytes, content_type)
                asset.quality_score = quality

            asset.processing_status = ProcessingStatus.READY.value
            await self.db.commit()
            await self.db.refresh(asset)

            # Trigger KB rebuild
            from app.services.knowledge_base_service import KnowledgeBaseService
            kb_service = KnowledgeBaseService(self.db)
            await kb_service.rebuild_debounced(str(brand_id))

            logger.info("Asset processed", asset_id=asset_id, quality=asset.quality_score)
            return asset

        except Exception as exc:
            asset.processing_status = ProcessingStatus.FAILED.value
            asset.error_message = str(exc)[:500]
            await self.db.commit()
            logger.error("Asset processing failed", asset_id=asset_id, error=str(exc))
            raise

    async def improve_with_flux_kontext(
        self,
        brand_id: str,
        asset_id: str,
        prompt: str = "Enhance this food photo to look professional, well-lit, and appetizing for social media",
        logo_url: str | None = None,
    ) -> MediaAsset:
        """Improve an asset using fal.ai FLUX Kontext.

        Sets status to 'improving', calls fal-ai API, saves improved
        image to S3, updates MediaAsset.improved_url.
        """
        if not settings.fal_key:
            raise RuntimeError("FAL_KEY is not configured")

        stmt = select(MediaAsset).where(MediaAsset.id == asset_id)
        result = await self.db.execute(stmt)
        asset = result.scalar_one_or_none()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")

        asset.processing_status = ProcessingStatus.IMPROVING.value
        await self.db.commit()

        try:
            # Call fal.ai FLUX Kontext
            improved_url = await self._call_flux_kontext(
                asset.public_url, prompt
            )

            # Download improved image and upload to S3
            async with httpx.AsyncClient() as client:
                resp = await client.get(improved_url, timeout=60.0)
                resp.raise_for_status()
                improved_bytes = resp.content

            improved_key = self.storage.generate_key(
                str(brand_id), "improved", f"improved_{asset.original_filename or 'photo.jpg'}"
            )
            upload_result = await self.storage.upload_bytes(
                improved_bytes, improved_key, "image/jpeg"
            )

            asset.improved_url = upload_result["url"]
            asset.processing_status = ProcessingStatus.READY.value
            asset.error_message = None
            await self.db.commit()
            await self.db.refresh(asset)

            logger.info("Asset improved with FLUX Kontext", asset_id=asset_id)
            return asset

        except Exception as exc:
            asset.processing_status = ProcessingStatus.FAILED.value
            asset.error_message = f"FLUX Kontext error: {str(exc)[:400]}"
            await self.db.commit()
            logger.error("FLUX Kontext improvement failed", asset_id=asset_id, error=str(exc))
            raise

    # ── Private Helpers ───────────────────────────────────────────────────

    async def _generate_thumbnail(
        self, image_bytes: bytes, brand_id: str, original_key: str
    ) -> str | None:
        """Generate a 300x300 thumbnail and upload to S3."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

            # Convert to RGB if necessary (RGBA, P mode, etc.)
            if img.mode not in ("RGB",):
                img = img.convert("RGB")

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            thumb_bytes = buf.getvalue()

            thumb_key = original_key.rsplit(".", 1)[0] + "_thumb.jpg"
            result = await self.storage.upload_bytes(
                thumb_bytes, thumb_key, "image/jpeg"
            )
            return result["url"]
        except Exception as exc:
            logger.warning("Thumbnail generation failed", error=str(exc))
            return None

    async def _estimate_quality(
        self, image_bytes: bytes, mime_type: str
    ) -> float:
        """Estimate food photo quality (0.0-1.0) via Claude Haiku Vision."""
        try:
            import base64
            import anthropic

            if not settings.anthropic_api_key:
                return 0.5  # Default if no API key

            b64 = base64.b64encode(image_bytes).decode("utf-8")
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Rate this food/restaurant photo for social media quality "
                                    "on a scale of 0.0 to 1.0. Consider lighting, composition, "
                                    "appetizing appeal, and professional look. "
                                    "Reply with ONLY a JSON: {\"score\": 0.X}"
                                ),
                            },
                        ],
                    }
                ],
            )

            raw = response.content[0].text
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(raw[start:end])
                score = float(result.get("score", 0.5))
                return max(0.0, min(1.0, score))

            return 0.5
        except Exception as exc:
            logger.warning("Quality estimation failed", error=str(exc))
            return 0.5

    async def _call_flux_kontext(
        self, image_url: str, prompt: str
    ) -> str:
        """Call fal.ai FLUX Kontext API to improve an image.

        Returns the URL of the improved image.
        """
        try:
            import fal_client

            result = await fal_client.subscribe_async(
                "fal-ai/flux-kontext/dev",
                arguments={
                    "prompt": prompt,
                    "image_url": image_url,
                },
            )

            images = result.get("images", [])
            if not images:
                raise ValueError("FLUX Kontext returned no images")

            return images[0]["url"]

        except ImportError:
            # Fallback: use httpx directly
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://queue.fal.run/fal-ai/flux-kontext/dev",
                    headers={
                        "Authorization": f"Key {settings.fal_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "prompt": prompt,
                        "image_url": image_url,
                    },
                    timeout=120.0,
                )
                resp.raise_for_status()
                result = resp.json()

                images = result.get("images", [])
                if not images:
                    raise ValueError("FLUX Kontext returned no images")

                return images[0]["url"]
