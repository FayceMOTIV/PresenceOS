"""
PresenceOS - Telegram Webhook

Mounted at /webhooks/telegram (outside /api/v1, same pattern as WhatsApp).
Handles:
  - POST /webhooks/telegram → incoming updates from Telegram Bot API
"""
import hmac
import hashlib
import structlog
from fastapi import APIRouter, Request, HTTPException

from app.core.config import settings
from app.services.telegram_adapter import TelegramAdapter

logger = structlog.get_logger()

router = APIRouter(tags=["Telegram Webhook"])

# Singleton adapter
_adapter: TelegramAdapter | None = None


def _get_adapter() -> TelegramAdapter:
    global _adapter
    if _adapter is None:
        _adapter = TelegramAdapter()
    return _adapter


@router.post("/webhooks/telegram")
async def handle_telegram_webhook(request: Request):
    """
    Process incoming Telegram webhook updates.

    Telegram sends a JSON Update object for each event (message, callback_query, etc).
    Optional: verify X-Telegram-Bot-Api-Secret-Token header.
    """
    # Verify secret token if configured
    if settings.telegram_webhook_secret:
        secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if secret_header != settings.telegram_webhook_secret:
            logger.warning("Telegram webhook secret mismatch")
            raise HTTPException(status_code=403, detail="Invalid secret token")

    try:
        update = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Process asynchronously
    try:
        adapter = _get_adapter()
        await adapter.handle_telegram_update(update)
    except Exception as e:
        logger.error("Telegram webhook processing error", error=str(e))

    # Always return 200 to Telegram
    return {"status": "ok"}
