"""
PresenceOS - Telegram Bot Adapter Tests.

Tests:
  1. TelegramService can be instantiated
  2. TelegramService.is_configured reflects token presence
  3. TelegramAdapter can be instantiated
  4. TelegramAdapter._normalize_message handles text
  5. TelegramAdapter._normalize_message handles photo
  6. TelegramAdapter._normalize_message handles video
  7. TelegramAdapter._normalize_message handles voice
  8. TelegramAdapter._normalize_message handles callback_query
  9. ConversationEngine.handle_message accepts messaging_service param
  10. Telegram webhook endpoint exists and returns 200
  11. Telegram webhook rejects invalid secret
  12. TelegramService.send_text_message returns None when not configured
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from httpx import AsyncClient


# ── TelegramService tests ──────────────────────────────────────────


def test_telegram_service_init():
    """TelegramService peut etre instancie."""
    from app.services.telegram import TelegramService

    svc = TelegramService()
    assert svc is not None
    assert svc.token is not None


def test_telegram_service_is_configured_with_token():
    """is_configured est True quand le token est present."""
    from app.services.telegram import TelegramService

    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = "test-token-123"
        svc = TelegramService()
        assert svc.is_configured is True


def test_telegram_service_not_configured_without_token():
    """is_configured est False sans token."""
    from app.services.telegram import TelegramService

    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = ""
        svc = TelegramService()
        assert svc.is_configured is False


@pytest.mark.asyncio
async def test_telegram_service_send_text_unconfigured():
    """send_text_message retourne None quand non configure."""
    from app.services.telegram import TelegramService

    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = ""
        svc = TelegramService()
        result = await svc.send_text_message("12345", "Hello")
        assert result is None


@pytest.mark.asyncio
async def test_telegram_service_send_buttons_unconfigured():
    """send_interactive_buttons retourne None quand non configure."""
    from app.services.telegram import TelegramService

    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = ""
        svc = TelegramService()
        result = await svc.send_interactive_buttons(
            "12345", "Test", [{"id": "btn1", "title": "OK"}]
        )
        assert result is None


@pytest.mark.asyncio
async def test_telegram_service_send_media_unconfigured():
    """send_media_message retourne None quand non configure."""
    from app.services.telegram import TelegramService

    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = ""
        svc = TelegramService()
        result = await svc.send_media_message(
            "12345", "https://example.com/img.jpg"
        )
        assert result is None


@pytest.mark.asyncio
async def test_telegram_service_send_reaction_unconfigured():
    """send_reaction retourne False quand non configure."""
    from app.services.telegram import TelegramService

    with patch("app.services.telegram.settings") as mock_settings:
        mock_settings.telegram_bot_token = ""
        svc = TelegramService()
        result = await svc.send_reaction("12345", 1)
        assert result is False


# ── TelegramAdapter normalization tests ────────────────────────────


def test_telegram_adapter_init():
    """TelegramAdapter peut etre instancie."""
    from app.services.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter()
    assert adapter is not None
    assert adapter.tg is not None


def test_normalize_text_message():
    """Normalise un message texte Telegram."""
    from app.services.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter()
    msg = {"text": "Bonjour", "chat": {"id": 123}}
    msg_type, normalized = adapter._normalize_message(msg)

    assert msg_type == "text"
    assert normalized["text"]["body"] == "Bonjour"


def test_normalize_photo_message():
    """Normalise un message photo Telegram."""
    from app.services.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter()
    msg = {
        "photo": [
            {"file_id": "small_id", "width": 90, "height": 90},
            {"file_id": "medium_id", "width": 320, "height": 320},
            {"file_id": "large_id", "width": 800, "height": 800},
        ],
        "caption": "Mon plat du jour",
        "chat": {"id": 123},
    }
    msg_type, normalized = adapter._normalize_message(msg)

    assert msg_type == "image"
    assert normalized["image"]["id"] == "large_id"  # Takes largest
    assert normalized["image"]["caption"] == "Mon plat du jour"


def test_normalize_video_message():
    """Normalise un message video Telegram."""
    from app.services.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter()
    msg = {
        "video": {"file_id": "video_file_id", "duration": 30},
        "caption": "Notre ambiance",
        "chat": {"id": 123},
    }
    msg_type, normalized = adapter._normalize_message(msg)

    assert msg_type == "video"
    assert normalized["video"]["id"] == "video_file_id"
    assert normalized["video"]["caption"] == "Notre ambiance"


def test_normalize_voice_message():
    """Normalise un message vocal Telegram."""
    from app.services.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter()
    msg = {
        "voice": {"file_id": "voice_file_id", "duration": 5},
        "chat": {"id": 123},
    }
    msg_type, normalized = adapter._normalize_message(msg)

    assert msg_type == "audio"
    assert normalized["audio"]["id"] == "voice_file_id"


def test_normalize_audio_message():
    """Normalise un fichier audio Telegram."""
    from app.services.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter()
    msg = {
        "audio": {"file_id": "audio_file_id", "duration": 120},
        "chat": {"id": 123},
    }
    msg_type, normalized = adapter._normalize_message(msg)

    assert msg_type == "audio"
    assert normalized["audio"]["id"] == "audio_file_id"


def test_normalize_unsupported_message():
    """Retourne None pour un type de message non supporte."""
    from app.services.telegram_adapter import TelegramAdapter

    adapter = TelegramAdapter()
    msg = {"sticker": {"file_id": "sticker_id"}, "chat": {"id": 123}}
    msg_type, normalized = adapter._normalize_message(msg)

    assert msg_type is None
    assert normalized == {}


# ── ConversationEngine accepts messaging_service ───────────────────


@pytest.mark.asyncio
async def test_engine_accepts_messaging_service():
    """ConversationEngine.handle_message accepte messaging_service."""
    from app.services.conversation_engine import ConversationEngine, _InMemoryRedis

    engine = ConversationEngine()
    engine.store._redis = _InMemoryRedis()

    mock_service = AsyncMock()
    mock_service.send_text_message = AsyncMock(return_value=1)
    mock_service.send_interactive_buttons = AsyncMock(return_value=1)
    mock_service.is_configured = True

    # Text in IDLE asks for a photo (new flow: photo-first)
    await engine.handle_message(
        sender_phone="tg_12345",
        msg_type="text",
        message={"text": {"body": "Poste sur Instagram"}},
        brand_id="brand-123",
        config_id="config-456",
        messaging_service=mock_service,
    )

    # The mock service should have been called (asks user to send a photo)
    assert mock_service.send_text_message.called
    call_text = mock_service.send_text_message.call_args[0][1]
    assert "photo" in call_text.lower()


# ── Webhook endpoint tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_telegram_webhook_endpoint(client: AsyncClient):
    """POST /webhooks/telegram retourne 200."""
    # Send a minimal update with no message (should still return 200)
    response = await client.post(
        "/webhooks/telegram",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "presenceos_telegram_secret"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_telegram_webhook_rejects_bad_secret(client: AsyncClient):
    """POST /webhooks/telegram rejette un secret invalide."""
    response = await client.post(
        "/webhooks/telegram",
        json={"update_id": 1},
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
    )
    assert response.status_code == 403


# ── Integration: all telegram modules importable ───────────────────


def test_all_telegram_modules_importable():
    """Tous les modules Telegram sont importables."""
    from app.services.telegram import TelegramService
    from app.services.telegram_adapter import TelegramAdapter
    from app.api.webhooks.telegram import router

    assert TelegramService is not None
    assert TelegramAdapter is not None
    assert router is not None
