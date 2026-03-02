"""
PresenceOS - Tests for CM Chat Service

Tests covering session management, message sending, proposal extraction,
system prompt building, and error handling.
"""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cm_chat_service import CMChatService


# ── Mock Builders ────────────────────────────────────────────────────────


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    return db


def _make_brand(
    name="Le Bistrot",
    brand_type="restaurant",
    description="Bistrot parisien chaleureux",
    niche="restaurant",
    locations=None,
    voice=None,
    knowledge_items=None,
    brand_dna=None,
    constraints=None,
):
    brand = MagicMock()
    brand.id = uuid.uuid4()
    brand.name = name
    brand.brand_type = MagicMock()
    brand.brand_type.value = brand_type
    brand.description = description
    brand.niche = niche
    brand.locations = locations or ["Paris 11e"]
    brand.voice = voice
    brand.knowledge_items = knowledge_items or []
    brand.brand_dna = brand_dna
    brand.constraints = constraints
    return brand


def _make_voice(
    tone_formal=30,
    tone_playful=75,
    custom_instructions=None,
    words_to_avoid=None,
):
    voice = MagicMock()
    voice.tone_formal = tone_formal
    voice.tone_playful = tone_playful
    voice.custom_instructions = custom_instructions
    voice.words_to_avoid = words_to_avoid or []
    return voice


def _make_session(brand_id=None, title="Nouvelle conversation", message_count=0):
    session = MagicMock()
    session.id = uuid.uuid4()
    session.brand_id = brand_id or uuid.uuid4()
    session.title = title
    session.status = "active"
    session.message_count = message_count
    session.summary = None
    session.created_at = datetime.now(timezone.utc)
    session.updated_at = datetime.now(timezone.utc)
    session.messages = []
    return session


def _make_message(session_id=None, role="user", content="Hello", proposals=None):
    msg = MagicMock()
    msg.id = uuid.uuid4()
    msg.session_id = session_id or uuid.uuid4()
    msg.role = role
    msg.content = content
    msg.proposals = proposals
    msg.tokens_used = 100
    msg.created_at = datetime.now(timezone.utc)
    msg.updated_at = datetime.now(timezone.utc)
    return msg


def _mock_openai_response(content="Voici ma suggestion !", tokens=150):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    response.usage = MagicMock()
    response.usage.total_tokens = tokens
    return response


# ── System Prompt Tests ──────────────────────────────────────────────────


class TestBuildSystemPrompt:
    """Tests for dynamic system prompt generation."""

    @pytest.mark.asyncio
    async def test_contains_brand_name(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand(name="Le Bistrot")
        prompt = await service._build_system_prompt(brand)
        assert "Le Bistrot" in prompt

    @pytest.mark.asyncio
    async def test_contains_niche(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand(niche="restaurant")
        prompt = await service._build_system_prompt(brand)
        assert "restaurant" in prompt

    @pytest.mark.asyncio
    async def test_contains_locations(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand(locations=["Paris 11e", "Lyon 6e"])
        prompt = await service._build_system_prompt(brand)
        assert "Paris 11e" in prompt
        assert "Lyon 6e" in prompt

    @pytest.mark.asyncio
    async def test_contains_description(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand(description="Meilleur couscous de Paris")
        prompt = await service._build_system_prompt(brand)
        assert "Meilleur couscous de Paris" in prompt

    @pytest.mark.asyncio
    async def test_contains_voice_tone(self):
        db = _mock_db()
        service = CMChatService(db)
        voice = _make_voice(tone_formal=70, tone_playful=30)
        brand = _make_brand(voice=voice)
        prompt = await service._build_system_prompt(brand)
        assert "formel" in prompt

    @pytest.mark.asyncio
    async def test_contains_voice_playful(self):
        db = _mock_db()
        service = CMChatService(db)
        voice = _make_voice(tone_formal=30, tone_playful=75)
        brand = _make_brand(voice=voice)
        prompt = await service._build_system_prompt(brand)
        assert "joueur" in prompt

    @pytest.mark.asyncio
    async def test_contains_custom_instructions(self):
        db = _mock_db()
        service = CMChatService(db)
        voice = _make_voice(custom_instructions="Toujours mentionner le brunch")
        brand = _make_brand(voice=voice)
        prompt = await service._build_system_prompt(brand)
        assert "brunch" in prompt

    @pytest.mark.asyncio
    async def test_contains_words_to_avoid(self):
        db = _mock_db()
        service = CMChatService(db)
        voice = _make_voice(words_to_avoid=["cheap", "discount"])
        brand = _make_brand(voice=voice)
        prompt = await service._build_system_prompt(brand)
        assert "cheap" in prompt

    @pytest.mark.asyncio
    async def test_contains_knowledge_items(self):
        db = _mock_db()
        service = CMChatService(db)
        ki = MagicMock()
        ki.is_active = True
        ki.knowledge_type = MagicMock()
        ki.knowledge_type.value = "faq"
        ki.title = "Horaires"
        ki.content = "Ouvert du mardi au dimanche"
        brand = _make_brand(knowledge_items=[ki])
        prompt = await service._build_system_prompt(brand)
        assert "Horaires" in prompt
        assert "mardi" in prompt

    @pytest.mark.asyncio
    async def test_skips_inactive_knowledge_items(self):
        db = _mock_db()
        service = CMChatService(db)
        ki = MagicMock()
        ki.is_active = False
        ki.title = "Ancien menu"
        ki.content = "Ne doit pas apparaitre"
        brand = _make_brand(knowledge_items=[ki])
        prompt = await service._build_system_prompt(brand)
        assert "Ancien menu" not in prompt

    @pytest.mark.asyncio
    async def test_contains_brand_dna(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand(brand_dna={"mission": "Cuisiner avec passion"})
        prompt = await service._build_system_prompt(brand)
        assert "Cuisiner avec passion" in prompt

    @pytest.mark.asyncio
    async def test_contains_constraints(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand(constraints={"max_posts_per_day": 3})
        prompt = await service._build_system_prompt(brand)
        assert "max_posts_per_day" in prompt

    @pytest.mark.asyncio
    async def test_contains_proposals_instruction(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand()
        prompt = await service._build_system_prompt(brand)
        assert "<proposals>" in prompt

    @pytest.mark.asyncio
    async def test_contains_french_rule(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand()
        prompt = await service._build_system_prompt(brand)
        assert "français" in prompt

    @pytest.mark.asyncio
    async def test_no_voice_still_works(self):
        db = _mock_db()
        service = CMChatService(db)
        brand = _make_brand(voice=None)
        prompt = await service._build_system_prompt(brand)
        assert "Le Bistrot" in prompt


# ── Proposal Extraction Tests ────────────────────────────────────────────


class TestExtractProposals:
    """Tests for <proposals> block parsing."""

    def test_extract_single_proposal(self):
        db = _mock_db()
        service = CMChatService(db)
        text = (
            'Voici mon idée :\n'
            '<proposals>\n'
            '[{"type":"post","platform":"instagram","caption":"Belle journée !","hashtags":["#food"]}]\n'
            '</proposals>'
        )
        result = service._extract_proposals(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "post"
        assert result[0]["caption"] == "Belle journée !"

    def test_extract_multiple_proposals(self):
        db = _mock_db()
        service = CMChatService(db)
        text = (
            '<proposals>\n'
            '[{"type":"post","platform":"instagram","caption":"Post 1","hashtags":["#a"]},'
            '{"type":"reel","platform":"instagram","caption":"Reel 1","hashtags":["#b"]}]\n'
            '</proposals>'
        )
        result = service._extract_proposals(text)
        assert result is not None
        assert len(result) == 2

    def test_extract_single_dict_wrapped_in_list(self):
        db = _mock_db()
        service = CMChatService(db)
        text = (
            '<proposals>\n'
            '{"type":"story","platform":"instagram","caption":"Story !"}\n'
            '</proposals>'
        )
        result = service._extract_proposals(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "story"

    def test_no_proposals_returns_none(self):
        db = _mock_db()
        service = CMChatService(db)
        text = "Voici quelques conseils pour votre stratégie."
        result = service._extract_proposals(text)
        assert result is None

    def test_invalid_json_returns_none(self):
        db = _mock_db()
        service = CMChatService(db)
        text = "<proposals>\n{invalid json here}\n</proposals>"
        result = service._extract_proposals(text)
        assert result is None


# ── Session Management Tests ─────────────────────────────────────────────


class TestSessionManagement:
    """Tests for session CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_new_session(self):
        db = _mock_db()
        service = CMChatService(db)
        brand_id = uuid.uuid4()

        # No session_id means create new
        with patch("app.services.cm_chat_service.CmSession") as MockSession:
            mock_instance = _make_session(brand_id=brand_id)
            MockSession.return_value = mock_instance

            session = await service.get_or_create_session(brand_id, None)

            db.add.assert_called_once()
            db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_existing_session(self):
        db = _mock_db()
        service = CMChatService(db)

        existing_session = _make_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_session
        db.execute = AsyncMock(return_value=result_mock)

        session = await service.get_or_create_session(
            existing_session.brand_id, existing_session.id
        )

        assert session is existing_session

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_creates_new(self):
        db = _mock_db()
        service = CMChatService(db)

        # First call (select query) returns None → session not found
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        brand_id = uuid.uuid4()
        # Don't patch CmSession class (breaks SQLAlchemy select) — just verify add() is called
        session = await service.get_or_create_session(brand_id, uuid.uuid4())

        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_success(self):
        db = _mock_db()
        service = CMChatService(db)

        existing_session = _make_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_session
        db.execute = AsyncMock(return_value=result_mock)

        deleted = await service.delete_session(
            existing_session.id, existing_session.brand_id
        )

        assert deleted is True
        db.delete.assert_called_once_with(existing_session)
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self):
        db = _mock_db()
        service = CMChatService(db)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        deleted = await service.delete_session(uuid.uuid4(), uuid.uuid4())

        assert deleted is False
        db.delete.assert_not_called()


# ── Send Message Tests ───────────────────────────────────────────────────


class TestSendMessage:
    """Tests for the core send_message flow."""

    @pytest.mark.asyncio
    async def test_send_message_saves_user_and_assistant_msgs(self):
        db = _mock_db()
        service = CMChatService(db)

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        # Mock history query
        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        ai_response = _mock_openai_response("Bonjour ! Comment puis-je aider ?", 120)

        with patch.object(service, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=ai_response
            )

            result = await service.send_message(brand, session, "Bonjour")

        # user msg + assistant msg = 2 add() calls
        assert db.add.call_count == 2
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_proposals(self):
        db = _mock_db()
        service = CMChatService(db)

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        ai_text = (
            'Voici une idée :\n'
            '<proposals>\n'
            '[{"type":"post","platform":"instagram","caption":"Plat du jour","hashtags":["#food"]}]\n'
            '</proposals>'
        )
        ai_response = _mock_openai_response(ai_text, 200)

        with patch.object(service, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=ai_response
            )

            result = await service.send_message(
                brand, session, "Propose un post pour le plat du jour"
            )

        # user msg + assistant msg + 1 AIProposal = 3 add() calls
        assert db.add.call_count == 3

    @pytest.mark.asyncio
    async def test_send_message_auto_titles_session(self):
        db = _mock_db()
        service = CMChatService(db)

        brand = _make_brand()
        session = _make_session(
            brand_id=brand.id,
            title="Nouvelle conversation",
            message_count=0,
        )

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        ai_response = _mock_openai_response("Bien sûr !", 100)

        with patch.object(service, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=ai_response
            )

            await service.send_message(brand, session, "Aide-moi avec Instagram")

        assert session.title == "Aide-moi avec Instagram"

    @pytest.mark.asyncio
    async def test_send_message_gpt4o_failure_returns_fallback(self):
        db = _mock_db()
        service = CMChatService(db)

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        with patch.object(service, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                side_effect=Exception("API down")
            )

            result = await service.send_message(brand, session, "Test")

        # Should still save a fallback assistant message
        assert db.add.call_count == 2
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_increments_message_count(self):
        db = _mock_db()
        service = CMChatService(db)

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        ai_response = _mock_openai_response("OK", 50)

        with patch.object(service, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=ai_response
            )

            await service.send_message(brand, session, "Test")

        # message_count incremented twice: once for user, once for assistant
        assert session.message_count == 2


# ── Client Init Tests ────────────────────────────────────────────────────


class TestClientInit:
    """Tests for OpenAI client initialization."""

    def test_no_api_key_raises(self):
        db = _mock_db()
        service = CMChatService(db)
        with patch("app.services.cm_chat_service.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            with pytest.raises(RuntimeError, match="OpenAI API key"):
                service._get_client()

    def test_client_reuses_existing(self):
        db = _mock_db()
        service = CMChatService(db)
        mock_client = MagicMock()
        service._client = mock_client
        assert service._get_client() is mock_client
