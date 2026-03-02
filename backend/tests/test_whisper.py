"""
PresenceOS — Whisper Transcriber Tests (Sprint 7)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.whisper_transcriber import WhisperTranscriber, get_transcriber


class TestWhisperTranscriber:
    """Tests for WhisperTranscriber."""

    @pytest.fixture
    def transcriber(self):
        return WhisperTranscriber()

    @pytest.mark.asyncio
    async def test_returns_error_without_api_key(self, transcriber):
        with patch("app.services.whisper_transcriber.settings") as mock_s:
            mock_s.openai_api_key = ""
            result = await transcriber.transcribe(b"audio_data")
            assert result["success"] is False
            assert "API key" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_for_large_file(self, transcriber):
        with patch("app.services.whisper_transcriber.settings") as mock_s:
            mock_s.openai_api_key = "sk-test"
            large_audio = b"x" * (26 * 1024 * 1024)
            result = await transcriber.transcribe(large_audio)
            assert result["success"] is False
            assert "too large" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_for_empty_file(self, transcriber):
        with patch("app.services.whisper_transcriber.settings") as mock_s:
            mock_s.openai_api_key = "sk-test"
            result = await transcriber.transcribe(b"")
            assert result["success"] is False
            assert "Empty" in result["error"]

    @pytest.mark.asyncio
    async def test_successful_transcription(self, transcriber):
        with patch("app.services.whisper_transcriber.settings") as mock_s:
            mock_s.openai_api_key = "sk-test"

            mock_response = MagicMock()
            mock_response.json.return_value = {
                "text": "Fais un post pour notre promo du weekend",
                "language": "fr",
                "duration": 5.2,
            }
            mock_response.raise_for_status = MagicMock()

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__ = AsyncMock(
                    return_value=mock_client.return_value
                )
                mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
                mock_client.return_value.post = AsyncMock(return_value=mock_response)

                result = await transcriber.transcribe(b"audio_data", filename="test.mp4")
                assert result["success"] is True
                assert result["text"] == "Fais un post pour notre promo du weekend"
                assert result["language"] == "fr"
                assert result["duration_seconds"] == 5.2

    @pytest.mark.asyncio
    async def test_handles_api_error(self, transcriber):
        with patch("app.services.whisper_transcriber.settings") as mock_s:
            mock_s.openai_api_key = "sk-test"

            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__ = AsyncMock(
                    return_value=mock_client.return_value
                )
                mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
                mock_client.return_value.post = AsyncMock(
                    side_effect=Exception("Network error")
                )

                result = await transcriber.transcribe(b"audio_data")
                assert result["success"] is False
                assert "error" in result

    def test_get_transcriber_singleton(self):
        t1 = get_transcriber()
        t2 = get_transcriber()
        assert t1 is t2


class TestVoiceEndpoint:
    """Tests for voice API endpoint registration."""

    def test_voice_route_registered(self):
        from app.api.v2.router import api_v2_router

        paths = [r.path for r in api_v2_router.routes]
        assert any("transcribe" in p for p in paths), f"No voice route in: {paths}"
