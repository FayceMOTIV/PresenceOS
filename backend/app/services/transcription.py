"""
PresenceOS - Transcription Service (Sprint 9B)

Uses OpenAI Whisper API to transcribe voice notes.
Standalone service for use in webhook handlers and Celery tasks.
"""
import structlog
from io import BytesIO

import openai

from app.core.config import settings

logger = structlog.get_logger()


class TranscriptionService:
    """Transcribe audio files using OpenAI Whisper."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe(
        self,
        audio_data: bytes,
        filename: str = "audio.ogg",
        language: str = "fr",
    ) -> str:
        """
        Transcribe audio bytes to text using Whisper.

        Args:
            audio_data: Raw audio bytes
            filename: Original filename (helps Whisper detect format)
            language: Language hint (default: French)

        Returns:
            Transcribed text string
        """
        try:
            audio_file = BytesIO(audio_data)
            audio_file.name = filename

            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
            )

            logger.info(
                "Audio transcribed",
                filename=filename,
                length=len(response.text),
            )
            return response.text

        except Exception as e:
            logger.error("Transcription failed", filename=filename, error=str(e))
            raise

    async def transcribe_with_timestamps(
        self,
        audio_data: bytes,
        filename: str = "audio.ogg",
        language: str = "fr",
    ) -> dict:
        """
        Transcribe audio with word-level timestamps.

        Returns:
            {"text": str, "words": [{"word": str, "start": float, "end": float}]}
        """
        try:
            audio_file = BytesIO(audio_data)
            audio_file.name = filename

            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )

            return {
                "text": response.text,
                "duration": response.duration,
                "words": [
                    {"word": w.word, "start": w.start, "end": w.end}
                    for w in (response.words or [])
                ],
            }

        except Exception as e:
            logger.error("Timestamped transcription failed", error=str(e))
            raise
