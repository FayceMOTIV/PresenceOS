"""Tests for AIVideoService (fal.ai Kling 2.6 / Wan 2.6)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAIVideoService:
    """Tests for AIVideoService."""

    @patch("app.services.ai_video_service.settings")
    def test_init_raises_without_fal_key(self, mock_settings):
        """Should raise RuntimeError when FAL_KEY is not set."""
        mock_settings.fal_key = ""
        from app.services.ai_video_service import AIVideoService
        with pytest.raises(RuntimeError, match="FAL_KEY not configured"):
            AIVideoService()

    @patch("app.services.ai_video_service.settings")
    def test_init_succeeds_with_fal_key(self, mock_settings):
        """Should initialize when FAL_KEY is set."""
        mock_settings.fal_key = "test-fal-key"
        from app.services.ai_video_service import AIVideoService
        svc = AIVideoService()
        assert svc._fal_key == "test-fal-key"

    @pytest.mark.asyncio
    @patch("app.services.ai_video_service.settings")
    async def test_text_to_video_kling(self, mock_settings):
        """Should call Kling 2.6 Pro for text-to-video."""
        mock_settings.fal_key = "test-fal-key"
        from app.services.ai_video_service import AIVideoService
        svc = AIVideoService()

        mock_fal_result = {"video": {"url": "https://fal.ai/temp/video.mp4"}}

        with patch.object(svc, "_persist_video", new_callable=AsyncMock, return_value="https://s3.example.com/video.mp4"):
            with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_fal_result):
                result = await svc.text_to_video(
                    prompt="A steaming bowl of ramen",
                    duration=5,
                    aspect_ratio="9:16",
                    brand_id="test-brand",
                    model="kling",
                )

        assert result["url"] == "https://s3.example.com/video.mp4"
        assert result["duration"] == 5
        assert result["aspect_ratio"] == "9:16"
        assert result["persisted"] is True

    @pytest.mark.asyncio
    @patch("app.services.ai_video_service.settings")
    async def test_text_to_video_wan_budget(self, mock_settings):
        """Should use Wan model for budget option."""
        mock_settings.fal_key = "test-fal-key"
        from app.services.ai_video_service import AIVideoService
        svc = AIVideoService()

        mock_fal_result = {"video": {"url": "https://fal.ai/temp/wan.mp4"}}

        with patch.object(svc, "_persist_video", new_callable=AsyncMock, return_value="https://s3.example.com/wan.mp4"):
            with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_fal_result):
                result = await svc.text_to_video(
                    prompt="A sunset over the ocean",
                    duration=5,
                    model="wan",
                )

        assert result["url"] == "https://s3.example.com/wan.mp4"

    @pytest.mark.asyncio
    @patch("app.services.ai_video_service.settings")
    async def test_text_to_video_raises_on_no_url(self, mock_settings):
        """Should raise ValueError when fal.ai returns no video URL."""
        mock_settings.fal_key = "test-fal-key"
        from app.services.ai_video_service import AIVideoService
        svc = AIVideoService()

        with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value={"video": {}}):
            with pytest.raises(ValueError, match="no video URL"):
                await svc.text_to_video(prompt="Test", duration=5)

    @pytest.mark.asyncio
    async def test_persist_video(self):
        """Should download video from fal.ai and upload to S3."""
        from app.services.ai_video_service import AIVideoService

        fake_video = b"\x00" * 1000

        mock_resp = MagicMock()
        mock_resp.content = fake_video
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        mock_storage = MagicMock()
        mock_storage.generate_key.return_value = "brands/test/media/2026/03/video.mp4"
        mock_storage.upload_bytes = AsyncMock(return_value={
            "key": "brands/test/media/2026/03/video.mp4",
            "url": "https://s3.example.com/video.mp4",
            "size": 1000,
        })

        with (
            patch("app.services.ai_video_service.httpx.AsyncClient", return_value=mock_client),
            patch("app.services.ai_video_service.get_storage_service", return_value=mock_storage),
        ):
            url = await AIVideoService._persist_video(
                "https://fal.ai/temp/video.mp4", "test-brand", "kling", 5,
            )

        assert url == "https://s3.example.com/video.mp4"
        mock_storage.upload_bytes.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.ai_video_service.settings")
    async def test_image_to_video(self, mock_settings):
        """Should call Kling I2V endpoint."""
        mock_settings.fal_key = "test-fal-key"
        from app.services.ai_video_service import AIVideoService
        svc = AIVideoService()

        mock_fal_result = {"video": {"url": "https://fal.ai/temp/i2v.mp4"}}

        with patch.object(svc, "_persist_video", new_callable=AsyncMock, return_value="https://s3.example.com/i2v.mp4"):
            with patch("fal_client.subscribe_async", new_callable=AsyncMock, return_value=mock_fal_result):
                result = await svc.image_to_video(
                    image_url="https://example.com/photo.jpg",
                    prompt="Slow zoom in with steam rising",
                    duration=5,
                )

        assert result["url"] == "https://s3.example.com/i2v.mp4"
        assert result["persisted"] is True
