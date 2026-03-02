# PresenceOS — Whisper Transcriber (Sprint 7)
# Transcription vocale via OpenAI Whisper API
# Cost: ~$0.006/min | Max 25MB | Formats: mp4, mp3, webm, m4a, wav, ogg

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"


class WhisperTranscriber:
    """Transcribes audio files using OpenAI Whisper API."""

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.mp4",
        language: str = "fr",
    ) -> dict:
        """
        Transcribe audio to text.

        Returns: {"success": bool, "text": str, "language": str, "duration_seconds": float}
        """
        if not settings.openai_api_key:
            return {
                "success": False,
                "text": "",
                "error": "OpenAI API key not configured",
            }

        if len(audio_bytes) > 25 * 1024 * 1024:
            return {"success": False, "text": "", "error": "File too large (max 25MB)"}

        if len(audio_bytes) == 0:
            return {"success": False, "text": "", "error": "Empty audio file"}

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    WHISPER_URL,
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    files={"file": (filename, audio_bytes, "audio/mp4")},
                    data={
                        "model": "whisper-1",
                        "language": language,
                        "response_format": "verbose_json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "text": data.get("text", "").strip(),
                    "language": data.get("language", language),
                    "duration_seconds": data.get("duration", 0),
                }

        except Exception as exc:
            logger.error("Whisper transcription failed", extra={"error": str(exc)})
            return {"success": False, "text": "", "error": str(exc)}


# Singleton
_transcriber: Optional[WhisperTranscriber] = None


def get_transcriber() -> WhisperTranscriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = WhisperTranscriber()
    return _transcriber
