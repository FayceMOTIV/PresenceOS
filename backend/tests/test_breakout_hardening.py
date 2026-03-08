"""
PresenceOS - Tests for Breakout Railway Hardening

Tests the retry logic, timeout handling, and base64 response parsing
in the Remotion render call path.
"""

import base64

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBreakoutEngineRetry:
    """Test the Remotion call retry and timeout logic."""

    @pytest.mark.asyncio
    async def test_retry_on_503_warming(self):
        """Should retry when Remotion returns 503 (warming up)."""
        from app.services.breakout.breakout_engine import BreakoutEngine

        # Mock: 2x 503, then 200 with base64 video
        video_data = b"fake-video-data"
        b64 = base64.b64encode(video_data).decode()

        responses = []
        for _ in range(2):
            r = MagicMock()
            r.status_code = 503
            responses.append(r)

        success = MagicMock()
        success.status_code = 200
        success.json.return_value = {"success": True, "video_base64": b64}
        responses.append(success)

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        mock_client = AsyncMock()
        mock_client.post = mock_post

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                engine = BreakoutEngine()
                result = await engine._call_remotion(
                    original_photo_url="https://example.com/original.jpg",
                    cutout_url="https://example.com/cutout.png",
                    business_name="Test Restaurant",
                    likes_count=1200,
                    instagram_handle="@test",
                    accent_color="#F59E0B",
                )

        assert result == video_data
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self):
        """Should raise RuntimeError after exhausting all warming retries."""
        from app.services.breakout.breakout_engine import BreakoutEngine

        warming_response = MagicMock()
        warming_response.status_code = 503

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=warming_response)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                engine = BreakoutEngine()
                with pytest.raises(RuntimeError, match="unavailable after max retries"):
                    await engine._call_remotion(
                        original_photo_url="https://example.com/img.jpg",
                        cutout_url="https://example.com/cutout.png",
                        business_name="Test",
                        likes_count=1200,
                        instagram_handle="@test",
                        accent_color="#F59E0B",
                    )

    @pytest.mark.asyncio
    async def test_timeout_retries_then_raises(self):
        """Should retry on timeout, then raise RuntimeError."""
        from app.services.breakout.breakout_engine import BreakoutEngine

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            with patch("asyncio.sleep", new_callable=AsyncMock):
                engine = BreakoutEngine()
                with pytest.raises(RuntimeError, match="timed out"):
                    await engine._call_remotion(
                        original_photo_url="https://example.com/img.jpg",
                        cutout_url="https://example.com/cutout.png",
                        business_name="Test",
                        likes_count=1200,
                        instagram_handle="@test",
                        accent_color="#F59E0B",
                    )

    @pytest.mark.asyncio
    async def test_non_200_raises(self):
        """Should raise RuntimeError on 500 from Remotion."""
        from app.services.breakout.breakout_engine import BreakoutEngine

        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal render error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=error_response)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            engine = BreakoutEngine()
            with pytest.raises(RuntimeError, match="500"):
                await engine._call_remotion(
                    original_photo_url="https://example.com/img.jpg",
                    cutout_url="https://example.com/cutout.png",
                    business_name="Test",
                    likes_count=1200,
                    instagram_handle="@test",
                    accent_color="#F59E0B",
                )

    @pytest.mark.asyncio
    async def test_base64_decoded_correctly(self):
        """Should correctly decode base64 video from response."""
        from app.services.breakout.breakout_engine import BreakoutEngine

        original_video = b"\x00\x01\x02\x03" * 100  # 400 bytes
        b64 = base64.b64encode(original_video).decode()

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "success": True,
            "video_base64": b64,
            "size_bytes": len(original_video),
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=success_response)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            engine = BreakoutEngine()
            result = await engine._call_remotion(
                original_photo_url="https://example.com/img.jpg",
                cutout_url="https://example.com/cutout.png",
                business_name="Test",
                likes_count=1200,
                instagram_handle="@test",
                accent_color="#F59E0B",
            )

        assert result == original_video

    @pytest.mark.asyncio
    async def test_missing_video_base64_raises(self):
        """Should raise when response has no video_base64."""
        from app.services.breakout.breakout_engine import BreakoutEngine

        bad_response = MagicMock()
        bad_response.status_code = 200
        bad_response.json.return_value = {"success": True}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=bad_response)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            engine = BreakoutEngine()
            with pytest.raises(RuntimeError, match="No video_base64"):
                await engine._call_remotion(
                    original_photo_url="https://example.com/img.jpg",
                    cutout_url="https://example.com/cutout.png",
                    business_name="Test",
                    likes_count=1200,
                    instagram_handle="@test",
                    accent_color="#F59E0B",
                )
