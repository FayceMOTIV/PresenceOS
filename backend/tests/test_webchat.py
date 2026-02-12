"""
PresenceOS - WebChat Service & Chat API Tests.

Tests:
  1. WebChatService accumulates text responses
  2. WebChatService accumulates button responses
  3. WebChatService accumulates media responses
  4. WebChatService is_configured always True
  5. POST /chat/message with text returns messages
  6. POST /chat/message with interactive returns messages
  7. POST /chat/upload accepts image file
  8. Chat module importable
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# ── WebChatService unit tests ────────────────────────────────────

@pytest.mark.asyncio
async def test_webchat_accumulates_text():
    """WebChatService accumulates text messages."""
    from app.services.webchat import WebChatService

    svc = WebChatService()
    result = await svc.send_text_message("user-1", "Bonjour !")
    assert result == "web-1"
    assert len(svc.responses) == 1
    assert svc.responses[0]["type"] == "text"
    assert svc.responses[0]["content"] == "Bonjour !"


@pytest.mark.asyncio
async def test_webchat_accumulates_buttons():
    """WebChatService accumulates button messages."""
    from app.services.webchat import WebChatService

    svc = WebChatService()
    result = await svc.send_interactive_buttons(
        "user-1",
        body_text="Choisis une option",
        buttons=[{"id": "btn1", "title": "Option 1"}, {"id": "btn2", "title": "Option 2"}],
        header_text="Test Header",
    )
    assert result == "web-1"
    assert len(svc.responses) == 1
    assert svc.responses[0]["type"] == "buttons"
    assert svc.responses[0]["content"] == "Choisis une option"
    assert svc.responses[0]["header"] == "Test Header"
    assert len(svc.responses[0]["buttons"]) == 2
    assert svc.responses[0]["buttons"][0]["id"] == "btn1"


@pytest.mark.asyncio
async def test_webchat_accumulates_media():
    """WebChatService accumulates media messages."""
    from app.services.webchat import WebChatService

    svc = WebChatService()
    result = await svc.send_media_message(
        "user-1", "https://example.com/img.jpg", caption="Belle photo", media_type="image"
    )
    assert result == "web-1"
    assert svc.responses[0]["type"] == "media"
    assert svc.responses[0]["media_url"] == "https://example.com/img.jpg"
    assert svc.responses[0]["content"] == "Belle photo"


@pytest.mark.asyncio
async def test_webchat_accumulates_reaction():
    """WebChatService accumulates reactions."""
    from app.services.webchat import WebChatService

    svc = WebChatService()
    result = await svc.send_reaction("user-1", "msg-1", "thumbsup")
    assert result is True
    assert svc.responses[0]["type"] == "reaction"


def test_webchat_is_configured():
    """WebChatService is always configured."""
    from app.services.webchat import WebChatService

    svc = WebChatService()
    assert svc.is_configured is True


@pytest.mark.asyncio
async def test_webchat_multiple_messages():
    """WebChatService accumulates multiple messages in order."""
    from app.services.webchat import WebChatService

    svc = WebChatService()
    await svc.send_text_message("u", "msg1")
    await svc.send_text_message("u", "msg2")
    await svc.send_interactive_buttons("u", "choose", [{"id": "a", "title": "A"}])

    assert len(svc.responses) == 3
    assert svc.responses[0]["content"] == "msg1"
    assert svc.responses[1]["content"] == "msg2"
    assert svc.responses[2]["type"] == "buttons"


# ── Chat engine integration via WebChatService ───────────────────

@pytest.mark.asyncio
async def test_chat_engine_with_webchat():
    """ConversationEngine works with WebChatService (text in IDLE asks for photo)."""
    from app.services.conversation_engine import ConversationEngine, _InMemoryRedis
    from app.services.webchat import WebChatService

    engine = ConversationEngine()
    engine.store._redis = _InMemoryRedis()
    webchat = WebChatService()

    await engine.handle_message(
        sender_phone="web:user-1",
        msg_type="text",
        message={"text": {"body": "Hello"}},
        brand_id="brand-1",
        config_id="config-1",
        messaging_service=webchat,
    )

    assert len(webchat.responses) >= 1
    assert "photo" in webchat.responses[0]["content"].lower()


# ── API endpoint tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_upload_endpoint():
    """POST /chat/upload accepts an image file (no auth, no DB)."""
    import io
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        response = await ac.post(
            "/api/v1/chat/upload",
            files={"file": ("test.jpg", fake_image, "image/jpeg")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "media_id" in data
    assert data["media_id"].endswith(".jpg")
    assert data["mime_type"] == "image/jpeg"


# ── Module importability ──────────────────────────────────────────

def test_chat_modules_importable():
    """All chat modules are importable."""
    from app.services.webchat import WebChatService
    from app.api.v1.endpoints.chat import router

    assert WebChatService is not None
    assert router is not None
