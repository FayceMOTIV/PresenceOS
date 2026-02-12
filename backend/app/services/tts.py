"""
PresenceOS - Text-to-Speech Service (Sprint 9C)

Uses OpenAI TTS to generate voiceover audio for video posts.
"""
import structlog
from io import BytesIO

import openai

from app.core.config import settings

logger = structlog.get_logger()


class TTSService:
    """Generate speech from text using OpenAI TTS."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.voice = settings.openai_tts_voice
        self.model = settings.openai_tts_model

    @property
    def is_configured(self) -> bool:
        return bool(settings.openai_api_key)

    async def generate_speech(
        self,
        text: str,
        voice: str | None = None,
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> bytes | None:
        """
        Generate speech audio from text.

        Args:
            text: Text to synthesize (max 4096 chars)
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            response_format: Output format (mp3, opus, aac, flac)

        Returns:
            Audio bytes or None on failure
        """
        if not self.is_configured:
            logger.warning("OpenAI API key not configured for TTS")
            return None

        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=voice or self.voice,
                input=text[:4096],
                speed=speed,
                response_format=response_format,
            )

            # Read the response content
            audio_bytes = response.content

            logger.info(
                "TTS generated",
                chars=len(text),
                voice=voice or self.voice,
                size=len(audio_bytes),
            )
            return audio_bytes

        except Exception as e:
            logger.error("TTS generation failed", error=str(e))
            return None

    async def generate_speech_for_caption(
        self,
        caption: str,
        language: str = "fr",
    ) -> bytes | None:
        """
        Generate voiceover for a social media caption.

        Strips hashtags and emojis before synthesis.
        """
        # Clean the caption for speech
        clean_text = self._clean_for_speech(caption)
        if not clean_text:
            return None

        return await self.generate_speech(clean_text)

    def _clean_for_speech(self, text: str) -> str:
        """Remove hashtags, mentions, and excessive emojis from text."""
        import re

        # Remove hashtags
        text = re.sub(r"#\w+", "", text)
        # Remove @mentions
        text = re.sub(r"@\w+", "", text)
        # Remove URLs
        text = re.sub(r"https?://\S+", "", text)
        # Remove emojis (basic)
        text = re.sub(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
            r"\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U0001F900-\U0001F9FF"
            r"\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002600-\U000026FF]+",
            "",
            text,
        )
        # Clean whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
