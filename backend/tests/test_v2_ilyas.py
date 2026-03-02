"""
PresenceOS - Tests for Ilyas v2 Endpoints

Tests covering POST /chat, GET /sessions, GET /sessions/{id}/messages,
DELETE /sessions/{id}, GET /context.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v2.endpoints.ilyas import (
    IlyasChatRequest,
    IlyasChatResponse,
    MessageResponse,
    SessionResponse,
    _message_response,
    _session_response,
    chat,
    delete_session,
    get_context,
    get_session_messages,
    list_sessions,
)


# ── Helpers ──────────────────────────────────────────────────────────────


def _mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@presenceos.dev"
    return user


def _mock_db():
    return AsyncMock()


def _make_session_obj(brand_id=None, title="Test Session", message_count=2, source="ilyas"):
    session = MagicMock()
    session.id = uuid.uuid4()
    session.brand_id = brand_id or uuid.uuid4()
    session.title = title
    session.status = "active"
    session.message_count = message_count
    session.summary = None
    session.source = source
    session.created_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)
    return session


def _make_message_obj(session_id=None, role="assistant", content="Salut !", proposals=None):
    msg = MagicMock()
    msg.id = uuid.uuid4()
    msg.session_id = session_id or uuid.uuid4()
    msg.role = role
    msg.content = content
    msg.proposals = proposals
    msg.tokens_used = 150
    msg.created_at = datetime.now(timezone.utc)
    return msg


def _make_brand_obj():
    brand = MagicMock()
    brand.id = uuid.uuid4()
    brand.name = "Le Bistrot"
    return brand


# ── Helper Function Tests ────────────────────────────────────────────────


class TestHelpers:
    def test_session_response_serialization(self):
        session = _make_session_obj(title="Ma conversation")
        result = _session_response(session)
        assert isinstance(result, SessionResponse)
        assert result.title == "Ma conversation"
        assert result.source == "ilyas"
        assert result.id == str(session.id)

    def test_message_response_serialization(self):
        msg = _make_message_obj(content="Bonjour !")
        result = _message_response(msg)
        assert isinstance(result, MessageResponse)
        assert result.content == "Bonjour !"
        assert result.role == "assistant"
        assert result.tokens_used == 150

    def test_message_response_with_proposals(self):
        proposals = [{"type": "post", "caption": "Test"}]
        msg = _make_message_obj(proposals=proposals)
        result = _message_response(msg)
        assert result.proposals == proposals


# ── POST /chat Tests ─────────────────────────────────────────────────────


class TestChatEndpoint:
    @pytest.mark.asyncio
    async def test_chat_creates_session_and_returns_response(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        brand = _make_brand_obj()

        session = _make_session_obj(brand_id=brand_id)
        assistant_msg = _make_message_obj(
            session_id=session.id,
            content="Je suis Ilyas, ton CM !",
        )

        body = IlyasChatRequest(message="Bonjour Ilyas")

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock) as mock_get_brand:
            mock_get_brand.return_value = brand

            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.get_or_create_session = AsyncMock(return_value=session)
                agent_instance.chat = AsyncMock(return_value=assistant_msg)

                result = await chat(
                    brand_id=brand_id,
                    body=body,
                    current_user=user,
                    db=db,
                )

        assert isinstance(result, IlyasChatResponse)
        assert result.message.content == "Je suis Ilyas, ton CM !"
        assert result.session.id == str(session.id)

    @pytest.mark.asyncio
    async def test_chat_with_existing_session(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        brand = _make_brand_obj()
        session_id = uuid.uuid4()

        session = _make_session_obj(brand_id=brand_id)
        session.id = session_id
        assistant_msg = _make_message_obj(session_id=session_id)

        body = IlyasChatRequest(message="Suite", session_id=str(session_id))

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock) as mock_get_brand:
            mock_get_brand.return_value = brand

            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.get_or_create_session = AsyncMock(return_value=session)
                agent_instance.chat = AsyncMock(return_value=assistant_msg)

                result = await chat(
                    brand_id=brand_id,
                    body=body,
                    current_user=user,
                    db=db,
                )

        agent_instance.get_or_create_session.assert_called_once_with(brand_id, session_id)

    @pytest.mark.asyncio
    async def test_chat_with_image_url(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        brand = _make_brand_obj()

        session = _make_session_obj(brand_id=brand_id)
        assistant_msg = _make_message_obj(session_id=session.id)

        body = IlyasChatRequest(
            message="Voici mon plat",
            image_url="https://example.com/photo.jpg",
        )

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock) as mock_get_brand:
            mock_get_brand.return_value = brand

            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.get_or_create_session = AsyncMock(return_value=session)
                agent_instance.chat = AsyncMock(return_value=assistant_msg)

                result = await chat(
                    brand_id=brand_id,
                    body=body,
                    current_user=user,
                    db=db,
                )

        call_kwargs = agent_instance.chat.call_args.kwargs
        assert call_kwargs["image_url"] == "https://example.com/photo.jpg"


# ── GET /sessions Tests ──────────────────────────────────────────────────


class TestListSessions:
    @pytest.mark.asyncio
    async def test_list_sessions_returns_sessions(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()

        sessions = [
            _make_session_obj(brand_id=brand_id, title="Session 1"),
            _make_session_obj(brand_id=brand_id, title="Session 2"),
        ]

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock):
            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.list_sessions = AsyncMock(return_value=(sessions, 2))

                result = await list_sessions(
                    brand_id=brand_id,
                    current_user=user,
                    db=db,
                    limit=20,
                    offset=0,
                )

        assert result["total"] == 2
        assert len(result["sessions"]) == 2
        assert result["sessions"][0].title == "Session 1"

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock):
            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.list_sessions = AsyncMock(return_value=([], 0))

                result = await list_sessions(
                    brand_id=brand_id,
                    current_user=user,
                    db=db,
                )

        assert result["total"] == 0
        assert result["sessions"] == []


# ── GET /sessions/{id}/messages Tests ────────────────────────────────────


class TestGetSessionMessages:
    @pytest.mark.asyncio
    async def test_get_messages_returns_messages(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        session_id = uuid.uuid4()

        messages = [
            _make_message_obj(session_id=session_id, role="user", content="Bonjour"),
            _make_message_obj(session_id=session_id, role="assistant", content="Salut !"),
        ]

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock):
            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.get_session_messages = AsyncMock(return_value=messages)

                result = await get_session_messages(
                    brand_id=brand_id,
                    session_id=session_id,
                    current_user=user,
                    db=db,
                )

        assert len(result["messages"]) == 2
        assert result["messages"][0].role == "user"
        assert result["messages"][1].role == "assistant"

    @pytest.mark.asyncio
    async def test_get_messages_empty_session(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        session_id = uuid.uuid4()

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock):
            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.get_session_messages = AsyncMock(return_value=[])

                result = await get_session_messages(
                    brand_id=brand_id,
                    session_id=session_id,
                    current_user=user,
                    db=db,
                )

        assert result["messages"] == []


# ── DELETE /sessions/{id} Tests ──────────────────────────────────────────


class TestDeleteSession:
    @pytest.mark.asyncio
    async def test_delete_session_success(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        session_id = uuid.uuid4()

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock):
            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.delete_session = AsyncMock(return_value=True)

                result = await delete_session(
                    brand_id=brand_id,
                    session_id=session_id,
                    current_user=user,
                    db=db,
                )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_session_not_found_raises_404(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        session_id = uuid.uuid4()

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock):
            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.delete_session = AsyncMock(return_value=False)

                from fastapi import HTTPException
                with pytest.raises(HTTPException) as exc_info:
                    await delete_session(
                        brand_id=brand_id,
                        session_id=session_id,
                        current_user=user,
                        db=db,
                    )

                assert exc_info.value.status_code == 404


# ── GET /context Tests ───────────────────────────────────────────────────


class TestGetContext:
    @pytest.mark.asyncio
    async def test_get_context_returns_debug_info(self):
        user = _mock_user()
        db = _mock_db()
        brand_id = uuid.uuid4()
        brand = _make_brand_obj()

        with patch("app.api.v2.endpoints.ilyas.get_brand", new_callable=AsyncMock) as mock_get_brand:
            mock_get_brand.return_value = brand

            with patch("app.api.v2.endpoints.ilyas.IlyasAgent") as MockAgent:
                agent_instance = MockAgent.return_value
                agent_instance.get_context = AsyncMock(return_value={
                    "system_prompt_length": 1200,
                    "system_prompt_preview": "Tu es Ilyas...",
                    "mem0_memories_count": 5,
                    "model": "claude-sonnet-4-20250514",
                })

                result = await get_context(
                    brand_id=brand_id,
                    current_user=user,
                    db=db,
                )

        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["mem0_memories_count"] == 5


# ── Pydantic Model Tests ────────────────────────────────────────────────


class TestModels:
    def test_ilyas_chat_request_minimal(self):
        req = IlyasChatRequest(message="Bonjour")
        assert req.session_id is None
        assert req.image_url is None

    def test_ilyas_chat_request_full(self):
        sid = str(uuid.uuid4())
        req = IlyasChatRequest(
            message="Voici mon plat",
            session_id=sid,
            image_url="https://example.com/photo.jpg",
        )
        assert req.session_id == sid
        assert req.image_url == "https://example.com/photo.jpg"

    def test_ilyas_chat_request_rejects_empty_message(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            IlyasChatRequest(message="")

    def test_session_response_defaults(self):
        resp = SessionResponse(
            id="abc",
            brand_id="def",
            title="Test",
            status="active",
            message_count=0,
            created_at="2026-03-01T00:00:00",
            updated_at="2026-03-01T00:00:00",
        )
        assert resp.source == "ilyas"
        assert resp.summary is None
