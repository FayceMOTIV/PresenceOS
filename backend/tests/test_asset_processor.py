"""
PresenceOS - Asset Processor Service Tests

Tests for upload flow, thumbnail generation, quality scoring,
FLUX Kontext mock, and error states.
"""
import io
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest
from PIL import Image

from app.models.media import MediaAsset, ProcessingStatus, MediaType, MediaSource
from app.services.asset_processor import AssetProcessorService, THUMBNAIL_SIZE


# ── Mock Builders ────────────────────────────────────────────────────────


def _make_test_image(width=800, height=600, format="JPEG") -> bytes:
    """Create a test image as bytes."""
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _mock_asset(
    brand_id=None,
    public_url="https://cdn.example.com/photo.jpg",
    status="pending",
) -> MagicMock:
    asset = MagicMock(spec=MediaAsset)
    asset.id = uuid.uuid4()
    asset.brand_id = brand_id or uuid.uuid4()
    asset.public_url = public_url
    asset.storage_key = "brands/xxx/media/2024/01/abc_photo.jpg"
    asset.original_filename = "photo.jpg"
    asset.mime_type = "image/jpeg"
    asset.media_type = MediaType.IMAGE
    asset.processing_status = status
    asset.quality_score = None
    asset.improved_url = None
    asset.thumbnail_url = None
    asset.error_message = None
    asset.ai_description = "A food photo"
    asset.asset_label = "pizza"
    asset.linked_dish_id = None
    return asset


# ── Thumbnail Tests ──────────────────────────────────────────────────────


class TestThumbnailGeneration:
    """Tests for thumbnail generation."""

    @pytest.mark.asyncio
    async def test_generate_thumbnail_success(self):
        db = _mock_db()
        service = AssetProcessorService(db)
        service.storage = MagicMock()
        service.storage.upload_bytes = AsyncMock(return_value={"url": "https://cdn.example.com/thumb.jpg"})

        image_bytes = _make_test_image(800, 600)
        result = await service._generate_thumbnail(image_bytes, str(uuid.uuid4()), "brands/x/media/2024/01/photo.jpg")

        assert result == "https://cdn.example.com/thumb.jpg"
        service.storage.upload_bytes.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_thumbnail_rgba_converts_to_rgb(self):
        """RGBA images should be converted to RGB before saving as JPEG."""
        db = _mock_db()
        service = AssetProcessorService(db)
        service.storage = MagicMock()
        service.storage.upload_bytes = AsyncMock(return_value={"url": "https://cdn.example.com/thumb.jpg"})

        img = Image.new("RGBA", (400, 400), color=(255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        result = await service._generate_thumbnail(image_bytes, str(uuid.uuid4()), "brands/x/media/2024/01/photo.png")
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_thumbnail_failure_returns_none(self):
        db = _mock_db()
        service = AssetProcessorService(db)
        service.storage = MagicMock()
        service.storage.upload_bytes = AsyncMock(side_effect=Exception("Upload failed"))

        result = await service._generate_thumbnail(b"invalid_image", str(uuid.uuid4()), "key")
        assert result is None


# ── Quality Estimation Tests ─────────────────────────────────────────────


class TestQualityEstimation:
    """Tests for AI quality scoring."""

    @pytest.mark.asyncio
    async def test_estimate_quality_success(self):
        db = _mock_db()
        service = AssetProcessorService(db)

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"score": 0.85}')]

        with patch("app.services.asset_processor.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("anthropic.AsyncAnthropic") as mock_anthropic:
                mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)
                score = await service._estimate_quality(_make_test_image(), "image/jpeg")

        assert score == 0.85

    @pytest.mark.asyncio
    async def test_estimate_quality_no_api_key(self):
        db = _mock_db()
        service = AssetProcessorService(db)

        with patch("app.services.asset_processor.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            score = await service._estimate_quality(_make_test_image(), "image/jpeg")

        assert score == 0.5  # Default fallback

    @pytest.mark.asyncio
    async def test_estimate_quality_clamps_to_0_1(self):
        db = _mock_db()
        service = AssetProcessorService(db)

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"score": 1.5}')]

        with patch("app.services.asset_processor.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("anthropic.AsyncAnthropic") as mock_anthropic:
                mock_anthropic.return_value.messages.create = AsyncMock(return_value=mock_response)
                score = await service._estimate_quality(_make_test_image(), "image/jpeg")

        assert score == 1.0

    @pytest.mark.asyncio
    async def test_estimate_quality_api_failure(self):
        db = _mock_db()
        service = AssetProcessorService(db)

        with patch("app.services.asset_processor.settings") as mock_settings:
            mock_settings.anthropic_api_key = "test-key"
            with patch("anthropic.AsyncAnthropic") as mock_anthropic:
                mock_anthropic.return_value.messages.create = AsyncMock(
                    side_effect=Exception("API error")
                )
                score = await service._estimate_quality(_make_test_image(), "image/jpeg")

        assert score == 0.5


# ── Process Upload Tests ─────────────────────────────────────────────────


class TestProcessUpload:
    """Tests for the full upload processing pipeline."""

    @pytest.mark.asyncio
    async def test_process_upload_sets_ready(self):
        db = _mock_db()
        asset = _mock_asset(status="pending")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute = AsyncMock(return_value=mock_result)

        service = AssetProcessorService(db)
        service.storage = MagicMock()
        service.storage.generate_key = MagicMock(return_value="brands/x/media/2024/01/photo.jpg")
        service.storage.upload_bytes = AsyncMock(return_value={"url": "https://cdn.example.com/photo.jpg", "key": "k", "size": 1000})

        with patch.object(service, "_generate_thumbnail", new_callable=AsyncMock, return_value="https://cdn.example.com/thumb.jpg"):
            with patch.object(service, "_estimate_quality", new_callable=AsyncMock, return_value=0.75):
                with patch("app.services.knowledge_base_service.KnowledgeBaseService") as mock_kb:
                    mock_kb_instance = MagicMock()
                    mock_kb_instance.rebuild_debounced = AsyncMock(return_value=True)
                    mock_kb.return_value = mock_kb_instance

                    result = await service.process_upload(
                        str(uuid.uuid4()), str(asset.id),
                        _make_test_image(), "image/jpeg"
                    )

        assert asset.processing_status == ProcessingStatus.READY.value
        assert asset.quality_score == 0.75
        assert asset.thumbnail_url == "https://cdn.example.com/thumb.jpg"

    @pytest.mark.asyncio
    async def test_process_upload_not_found(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        service = AssetProcessorService(db)
        with pytest.raises(ValueError, match="not found"):
            await service.process_upload(
                str(uuid.uuid4()), str(uuid.uuid4()),
                b"data", "image/jpeg"
            )

    @pytest.mark.asyncio
    async def test_process_upload_failure_sets_failed(self):
        db = _mock_db()
        asset = _mock_asset(status="pending")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = asset
        db.execute = AsyncMock(return_value=mock_result)

        service = AssetProcessorService(db)
        service.storage = MagicMock()
        service.storage.generate_key = MagicMock(return_value="key")
        service.storage.upload_bytes = AsyncMock(side_effect=Exception("S3 error"))

        with pytest.raises(Exception, match="S3 error"):
            await service.process_upload(
                str(uuid.uuid4()), str(asset.id),
                b"data", "image/jpeg"
            )

        assert asset.processing_status == ProcessingStatus.FAILED.value
        assert "S3 error" in asset.error_message


# ── FLUX Kontext Tests ───────────────────────────────────────────────────


class TestFluxKontext:
    """Tests for fal.ai FLUX Kontext improvement."""

    @pytest.mark.asyncio
    async def test_improve_no_fal_key_raises(self):
        db = _mock_db()
        service = AssetProcessorService(db)

        with patch("app.services.asset_processor.settings") as mock_settings:
            mock_settings.fal_key = ""
            with pytest.raises(RuntimeError, match="FAL_KEY"):
                await service.improve_with_flux_kontext(
                    str(uuid.uuid4()), str(uuid.uuid4())
                )

    @pytest.mark.asyncio
    async def test_improve_asset_not_found(self):
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        service = AssetProcessorService(db)
        with patch("app.services.asset_processor.settings") as mock_settings:
            mock_settings.fal_key = "test-key"
            with pytest.raises(ValueError, match="not found"):
                await service.improve_with_flux_kontext(
                    str(uuid.uuid4()), str(uuid.uuid4())
                )
