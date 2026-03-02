"""
PresenceOS — Voice API v2 (Sprint 7)

Audio transcription via OpenAI Whisper.
POST /voice/{brand_id}/transcribe — Audio → text
"""

import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.api.v2.deps import FirebaseUser, DBSession
from app.services.whisper_transcriber import get_transcriber

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/{brand_id}/transcribe",
    summary="Transcribe audio to text",
)
async def transcribe_audio(
    brand_id: str,
    user: FirebaseUser,
    db: DBSession,
    audio: UploadFile = File(...),
    language: str = Form("fr"),
):
    """
    Transcribe an audio file to text using Whisper.
    Formats: mp4, mp3, m4a, wav, webm, ogg. Max 25MB.
    """
    try:
        audio_bytes = await audio.read()
        transcriber = get_transcriber()
        result = await transcriber.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "audio.mp4",
            language=language,
        )
        return result
    except Exception as exc:
        logger.error("transcribe_audio failed", extra={"brand_id": brand_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))
