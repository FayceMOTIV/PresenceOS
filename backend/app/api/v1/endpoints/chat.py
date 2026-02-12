"""
PresenceOS - Content Studio Chat API

Web-based endpoints that route through ConversationEngine
using WebChatService to accumulate responses.
"""
import os
import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.autopilot import AutopilotConfig
from app.models.brand import Brand
from app.services.conversation_engine import ConversationEngine
from app.services.webchat import WebChatService

logger = structlog.get_logger()
router = APIRouter()

UPLOAD_DIR = "/tmp/presenceos/uploads"

# Fallback IDs when DB is not available
FALLBACK_BRAND_ID = "dev-brand"
FALLBACK_CONFIG_ID = "dev-config"

# Singleton engine
_conversation_engine: ConversationEngine | None = None


def _get_engine() -> ConversationEngine:
    global _conversation_engine
    if _conversation_engine is None:
        _conversation_engine = ConversationEngine()
    return _conversation_engine


class ChatMessageRequest(BaseModel):
    msg_type: str  # "text", "image", "video", "interactive"
    text: str | None = None
    button_id: str | None = None
    media_id: str | None = None
    media_url: str | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    messages: list[dict]
    session_id: str


class UploadResponse(BaseModel):
    media_id: str
    media_url: str
    mime_type: str


async def _get_optional_db():
    """Yield a DB session if available, None otherwise."""
    try:
        async for session in get_db():
            yield session
            return
    except Exception:
        yield None


async def _resolve_brand(db: Optional[AsyncSession]) -> tuple[str, str]:
    """Find brand_id and config_id. Falls back to dev IDs if no DB."""
    if db is None:
        return FALLBACK_BRAND_ID, FALLBACK_CONFIG_ID

    try:
        result = await db.execute(
            select(Brand).where(Brand.is_active == True).limit(1)
        )
        brand = result.scalar_one_or_none()

        if not brand:
            return FALLBACK_BRAND_ID, FALLBACK_CONFIG_ID

        result = await db.execute(
            select(AutopilotConfig).where(AutopilotConfig.brand_id == brand.id)
        )
        config = result.scalar_one_or_none()
        config_id = str(config.id) if config else str(brand.id)
        return str(brand.id), config_id
    except Exception:
        return FALLBACK_BRAND_ID, FALLBACK_CONFIG_ID


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatMessageRequest,
    db: Optional[AsyncSession] = Depends(_get_optional_db),
):
    """Send a message through ConversationEngine and get AI responses."""
    brand_id, config_id = await _resolve_brand(db)

    session_id = request.session_id or "web:test-user"
    webchat = WebChatService()

    # Build normalized message based on type
    if request.msg_type == "text":
        message = {"text": {"body": request.text or ""}}

    elif request.msg_type == "interactive":
        message = {
            "interactive": {
                "type": "button_reply",
                "button_reply": {"id": request.button_id or ""},
            }
        }

    elif request.msg_type in ("image", "video"):
        message = {
            request.msg_type: {
                "id": request.media_id or "",
                "caption": request.text or "",
            }
        }
    else:
        message = {"text": {"body": request.text or ""}}
        request.msg_type = "text"

    # Create a media downloader for local files
    async def web_media_downloader(media_id: str):
        path = os.path.join(UPLOAD_DIR, media_id)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Upload not found: {media_id}")
        with open(path, "rb") as f:
            data = f.read()
        ext = media_id.rsplit(".", 1)[-1].lower()
        mime_map = {
            "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "gif": "image/gif",
            "webp": "image/webp", "mp4": "video/mp4",
            "mov": "video/quicktime", "ogg": "audio/ogg",
            "webm": "video/webm",
        }
        return data, mime_map.get(ext, "image/jpeg")

    engine = _get_engine()
    try:
        await engine.handle_message(
            sender_phone=session_id,
            msg_type=request.msg_type,
            message=message,
            brand_id=brand_id,
            config_id=config_id,
            messaging_service=webchat,
            media_downloader=web_media_downloader,
        )
    except Exception as e:
        logger.error("ConversationEngine error", error=str(e))
        webchat.responses.append({
            "type": "text",
            "content": f"Erreur interne : {str(e)[:200]}",
        })

    return ChatResponse(
        messages=webchat.responses,
        session_id=session_id,
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_media(
    file: UploadFile = File(...),
):
    """Upload a photo/video for use in chat messages."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    mime = file.content_type or "image/jpeg"

    return UploadResponse(
        media_id=filename,
        media_url=f"/uploads/{filename}",
        mime_type=mime,
    )
