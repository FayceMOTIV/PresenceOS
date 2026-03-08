"""Tests for ImageService (Gemini Image generation)."""
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.image_service import ImageService


class TestImageService:
    """Tests for ImageService."""

    @patch("app.services.image_service.settings")
    def test_get_api_key_google(self, mock_settings):
        """Should return google_api_key when set."""
        mock_settings.google_api_key = "test-google-key"
        mock_settings.gemini_api_key = ""
        svc = ImageService()
        assert svc._get_api_key() == "test-google-key"

    @patch("app.services.image_service.settings")
    def test_get_api_key_gemini_fallback(self, mock_settings):
        """Should fall back to gemini_api_key."""
        mock_settings.google_api_key = ""
        mock_settings.gemini_api_key = "test-gemini-key"
        svc = ImageService()
        assert svc._get_api_key() == "test-gemini-key"

    @patch("app.services.image_service.settings")
    def test_get_api_key_raises_when_missing(self, mock_settings):
        """Should raise RuntimeError when no API key configured."""
        mock_settings.google_api_key = ""
        mock_settings.gemini_api_key = ""
        svc = ImageService()
        with pytest.raises(RuntimeError, match="Google API key not configured"):
            svc._get_api_key()

    def test_extract_image_bytes_from_b64(self):
        """Should extract and decode base64 image bytes."""
        fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        fake_b64 = base64.b64encode(fake_image).decode()

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = fake_b64

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        result = ImageService._extract_image_bytes(mock_response)
        assert result == fake_image

    def test_extract_image_bytes_raw(self):
        """Should handle raw bytes (not base64)."""
        fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50

        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = fake_image

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        result = ImageService._extract_image_bytes(mock_response)
        assert result == fake_image

    def test_extract_image_bytes_none(self):
        """Should return None when no image in response."""
        mock_part = MagicMock()
        mock_part.inline_data = None

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        result = ImageService._extract_image_bytes(mock_response)
        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.image_service.get_storage_service")
    @patch("app.services.image_service.settings")
    async def test_generate_food_image_success(self, mock_settings, mock_get_storage):
        """Should generate image and persist to S3."""
        mock_settings.google_api_key = "test-key"
        mock_settings.gemini_api_key = ""

        fake_image = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        fake_b64 = base64.b64encode(fake_image).decode()

        # Mock Gemini response
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = fake_b64

        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content.parts = [mock_part]

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        # Mock storage
        mock_storage = MagicMock()
        mock_storage.generate_key.return_value = "brands/test/media/2026/03/test.png"
        mock_storage.upload_bytes = AsyncMock(return_value={
            "key": "brands/test/media/2026/03/test.png",
            "url": "https://s3.example.com/test.png",
            "size": len(fake_image),
        })
        mock_get_storage.return_value = mock_storage

        svc = ImageService()

        with patch.object(svc, "_get_model", return_value=mock_model):
            with patch("app.services.image_service.asyncio") as mock_asyncio:
                mock_loop = MagicMock()
                mock_loop.run_in_executor = AsyncMock(return_value=mock_response)
                mock_asyncio.get_event_loop.return_value = mock_loop

                result = await svc.generate_food_image(
                    dish_name="Coq au Vin",
                    description="Classic French dish",
                    brand_id="test-brand",
                    quality="fast",
                )

        assert result["url"] == "https://s3.example.com/test.png"
        assert result["persisted"] is True
        assert result["quality"] == "fast"
        assert "generated_at" in result

    @pytest.mark.asyncio
    @patch("app.services.image_service.get_storage_service")
    async def test_persist_image(self, mock_get_storage):
        """Should upload bytes to S3 and return URL."""
        mock_storage = MagicMock()
        mock_storage.generate_key.return_value = "brands/ai/media/2026/03/test.png"
        mock_storage.upload_bytes = AsyncMock(return_value={
            "key": "brands/ai/media/2026/03/test.png",
            "url": "https://s3.example.com/test.png",
            "size": 100,
        })
        mock_get_storage.return_value = mock_storage

        url = await ImageService._persist_image(b"\x00" * 100, "test-brand", "food.png")
        assert url == "https://s3.example.com/test.png"
        mock_storage.upload_bytes.assert_called_once()
