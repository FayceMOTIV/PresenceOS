"""
PresenceOS — Video Asset Service Tests (Sprint B3)

Tests for VideoAssetService CRUD + publish operations.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.video_asset import VideoAsset, VideoAssetStatus
from app.services.video_asset_service import VideoAssetService


def _mock_db(existing_asset=None):
    """Create mock AsyncSession."""
    db = AsyncMock()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing_asset

    # For list queries
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [existing_asset] if existing_asset else []
    result_mock.scalars.return_value = scalars_mock

    db.execute = AsyncMock(return_value=result_mock)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    return db


class TestVideoAssetServiceSave:

    @pytest.mark.asyncio
    @patch("app.services.video_asset_service.get_storage_service")
    @patch("app.services.video_asset_service.httpx.AsyncClient")
    async def test_save_video_downloads_and_uploads(self, mock_http_cls, mock_storage_fn):
        # Mock httpx download
        mock_response = MagicMock()
        mock_response.content = b"fake-video-bytes"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_cls.return_value = mock_client

        # Mock storage
        mock_storage = MagicMock()
        mock_storage.generate_key.return_value = "brands/xxx/media/2026/03/abc_video_5s.mp4"
        mock_storage.upload_bytes = AsyncMock(return_value={
            "key": "brands/xxx/media/2026/03/abc_video_5s.mp4",
            "url": "https://storage.example.com/brands/xxx/media/2026/03/abc_video_5s.mp4",
            "size": 16,
        })
        mock_storage_fn.return_value = mock_storage

        db = _mock_db()
        svc = VideoAssetService(db)
        brand_id = uuid.uuid4()

        asset = await svc.save_video(
            brand_id=brand_id,
            fal_url="https://fal.ai/tmp/video.mp4",
            prompt="Couscous fumant dans un plat",
            duration_seconds=5,
        )

        # Verify download was called
        mock_client.get.assert_called_once_with("https://fal.ai/tmp/video.mp4")
        # Verify upload was called
        mock_storage.upload_bytes.assert_called_once()
        # Verify DB add + commit
        db.add.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.video_asset_service.get_storage_service")
    @patch("app.services.video_asset_service.httpx.AsyncClient")
    async def test_save_video_sets_correct_metadata(self, mock_http_cls, mock_storage_fn):
        mock_response = MagicMock()
        mock_response.content = b"x" * 1024
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_http_cls.return_value = mock_client

        mock_storage = MagicMock()
        mock_storage.generate_key.return_value = "key.mp4"
        mock_storage.upload_bytes = AsyncMock(return_value={
            "key": "key.mp4", "url": "https://s3/key.mp4", "size": 1024,
        })
        mock_storage_fn.return_value = mock_storage

        db = _mock_db()
        svc = VideoAssetService(db)

        await svc.save_video(
            brand_id=uuid.uuid4(),
            fal_url="https://fal.ai/v.mp4",
            prompt="Tajine",
            duration_seconds=10,
            aspect_ratio="16:9",
            style="vibrant",
        )

        # Check the object added to DB
        added_asset = db.add.call_args[0][0]
        assert added_asset.duration_seconds == 10
        assert added_asset.aspect_ratio == "16:9"
        assert added_asset.style == "vibrant"
        assert added_asset.file_size == 1024
        assert added_asset.status == VideoAssetStatus.SAVED.value


class TestVideoAssetServicePublish:

    @pytest.mark.asyncio
    async def test_publish_not_found_raises(self):
        db = _mock_db(existing_asset=None)
        svc = VideoAssetService(db)

        with pytest.raises(ValueError, match="not found"):
            await svc.publish_video(
                asset_id=uuid.uuid4(),
                platform="instagram",
                caption="Mon plat",
                account_username="lefamilys",
            )

    @pytest.mark.asyncio
    @patch("app.services.video_asset_service.VideoAssetService.get_asset")
    async def test_publish_success(self, mock_get):
        asset = MagicMock(spec=VideoAsset)
        asset.id = uuid.uuid4()
        asset.brand_id = uuid.uuid4()
        asset.public_url = "https://s3/video.mp4"
        asset.status = VideoAssetStatus.SAVED.value
        asset.published_at = None

        # Mock DB to return asset on select
        db = _mock_db(existing_asset=asset)
        svc = VideoAssetService(db)

        with patch("app.connectors.upload_post.UploadPostConnector.publish") as mock_publish:
            mock_publish.return_value = {
                "post_id": "12345",
                "post_url": "https://instagram.com/p/12345",
            }

            result = await svc.publish_video(
                asset_id=asset.id,
                platform="instagram",
                caption="Couscous royal",
                account_username="lefamilys",
            )

        assert asset.status == VideoAssetStatus.PUBLISHED.value
        assert asset.post_id == "12345"
        assert db.commit.call_count >= 2  # once for status update, once for publish result

    @pytest.mark.asyncio
    async def test_publish_failure_sets_error(self):
        asset = MagicMock(spec=VideoAsset)
        asset.id = uuid.uuid4()
        asset.brand_id = uuid.uuid4()
        asset.public_url = "https://s3/video.mp4"
        asset.status = VideoAssetStatus.SAVED.value
        asset.published_at = None

        db = _mock_db(existing_asset=asset)
        svc = VideoAssetService(db)

        with patch("app.connectors.upload_post.UploadPostConnector.publish") as mock_publish:
            mock_publish.side_effect = Exception("Upload-Post timeout")

            result = await svc.publish_video(
                asset_id=asset.id,
                platform="tiktok",
                caption="Tajine",
                account_username="lefamilys",
            )

        assert asset.status == VideoAssetStatus.FAILED.value
        assert "timeout" in asset.publish_error.lower()


class TestVideoAssetServiceList:

    @pytest.mark.asyncio
    async def test_list_returns_assets(self):
        asset = MagicMock(spec=VideoAsset)
        asset.brand_id = uuid.uuid4()
        asset.created_at = datetime.now(timezone.utc)

        db = _mock_db(existing_asset=asset)
        svc = VideoAssetService(db)
        result = await svc.list_assets(asset.brand_id)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_empty(self):
        db = _mock_db(existing_asset=None)
        svc = VideoAssetService(db)
        result = await svc.list_assets(uuid.uuid4())
        assert result == []


class TestVideoAssetServiceGet:

    @pytest.mark.asyncio
    async def test_get_existing(self):
        asset = MagicMock(spec=VideoAsset)
        asset.id = uuid.uuid4()
        db = _mock_db(existing_asset=asset)
        svc = VideoAssetService(db)
        result = await svc.get_asset(asset.id)
        assert result is asset

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        db = _mock_db(existing_asset=None)
        svc = VideoAssetService(db)
        result = await svc.get_asset(uuid.uuid4())
        assert result is None
