"""
PresenceOS - Tests for Ilyas Agent

Tests covering system prompt building, proposal extraction,
chat flow, session management, vision integration, and error handling.
"""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ilyas.agent import IlyasAgent


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


def _make_session(brand_id=None, title="Nouvelle conversation", message_count=0, source="ilyas"):
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


def _mock_claude_response(content="Voici ma suggestion !", input_tokens=100, output_tokens=50):
    response = MagicMock()
    block = MagicMock()
    block.text = content
    response.content = [block]
    response.usage = MagicMock()
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    return response


# ── System Prompt Tests ──────────────────────────────────────────────────


class TestBuildSystemPrompt:
    """Tests for Ilyas system prompt generation."""

    @pytest.mark.asyncio
    async def test_contains_ilyas_persona(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        brand = _make_brand(name="Le Bistrot")

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(return_value=[])
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        assert "Ilyas" in prompt

    @pytest.mark.asyncio
    async def test_contains_brand_name(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        brand = _make_brand(name="Chez Marco")

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(return_value=[])
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        assert "Chez Marco" in prompt

    @pytest.mark.asyncio
    async def test_contains_voice_info(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        voice = _make_voice(tone_formal=70, tone_playful=30)
        brand = _make_brand(voice=voice)

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(return_value=[])
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        assert "formel" in prompt

    @pytest.mark.asyncio
    async def test_contains_proposals_instruction(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        brand = _make_brand()

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(return_value=[])
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        assert "<proposals>" in prompt

    @pytest.mark.asyncio
    async def test_includes_brand_brain_memories(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        brand = _make_brand()

        brain_memories = [
            {"content": "Le restaurant aime les tons chauds", "confidence": 0.95}
        ]

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(return_value=brain_memories)
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        assert "tons chauds" in prompt

    @pytest.mark.asyncio
    async def test_includes_mem0_memories(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[
            {"memory": "Publie le mardi à 18h"}
        ])
        brand = _make_brand()

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(return_value=[])
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        assert "mardi à 18h" in prompt

    @pytest.mark.asyncio
    async def test_brain_failure_doesnt_crash(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        brand = _make_brand()

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(side_effect=Exception("DB error"))
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        # Should still produce a valid prompt
        assert "Ilyas" in prompt

    @pytest.mark.asyncio
    async def test_french_rules(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        brand = _make_brand()

        with patch("app.services.brand_brain.BrandBrain") as MockBrain:
            MockBrain.return_value.recall = AsyncMock(return_value=[])
            with patch("app.services.ilyas.agent.CalendarIntelligence") as MockCal:
                MockCal.return_value.get_temporal_context = AsyncMock(return_value=None)
                prompt = await agent._build_system_prompt(brand, "user-123")

        assert "français" in prompt


# ── Proposal Extraction Tests ────────────────────────────────────────────


class TestExtractProposals:
    """Tests for <proposals> block parsing (same regex as CMChatService)."""

    def test_extract_single_proposal(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        text = (
            'Voici mon idée :\n'
            '<proposals>\n'
            '[{"type":"post","platform":"instagram","caption":"Belle journée !","hashtags":["#food"]}]\n'
            '</proposals>'
        )
        result = agent._extract_proposals(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "post"
        assert result[0]["caption"] == "Belle journée !"

    def test_extract_multiple_proposals(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        text = (
            '<proposals>\n'
            '[{"type":"post","platform":"instagram","caption":"Post 1","hashtags":["#a"]},'
            '{"type":"reel","platform":"instagram","caption":"Reel 1","hashtags":["#b"]}]\n'
            '</proposals>'
        )
        result = agent._extract_proposals(text)
        assert result is not None
        assert len(result) == 2

    def test_single_dict_wrapped_in_list(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        text = (
            '<proposals>\n'
            '{"type":"story","platform":"instagram","caption":"Story !"}\n'
            '</proposals>'
        )
        result = agent._extract_proposals(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["type"] == "story"

    def test_no_proposals_returns_none(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        text = "Voici quelques conseils pour ta stratégie."
        result = agent._extract_proposals(text)
        assert result is None

    def test_invalid_json_returns_none(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        text = "<proposals>\n{invalid json}\n</proposals>"
        result = agent._extract_proposals(text)
        assert result is None


# ── Chat Flow Tests ──────────────────────────────────────────────────────


class TestChat:
    """Tests for the core chat flow."""

    @pytest.mark.asyncio
    async def test_chat_saves_user_and_assistant_messages(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.add = AsyncMock()

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        claude_response = _mock_claude_response("Bonjour ! Comment puis-je t'aider ?")

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "System prompt"
            with patch.object(agent, "_get_client") as mock_client:
                mock_client.return_value.messages.create = AsyncMock(return_value=claude_response)

                result = await agent.chat(brand, session, "Bonjour", "user-123")

        # user msg + assistant msg = 2 add() calls
        assert db.add.call_count == 2
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_with_proposals_creates_ai_proposals(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.add = AsyncMock()

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
        claude_response = _mock_claude_response(ai_text)

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "System prompt"
            with patch.object(agent, "_get_client") as mock_client:
                mock_client.return_value.messages.create = AsyncMock(return_value=claude_response)

                await agent.chat(brand, session, "Propose un post", "user-123")

        # user msg + assistant msg + 1 AIProposal = 3 add() calls
        assert db.add.call_count == 3

    @pytest.mark.asyncio
    async def test_chat_auto_titles_session(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.add = AsyncMock()

        brand = _make_brand()
        session = _make_session(
            brand_id=brand.id,
            title="Nouvelle conversation",
            message_count=0,
        )

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        claude_response = _mock_claude_response("Bien sûr !")

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "System prompt"
            with patch.object(agent, "_get_client") as mock_client:
                mock_client.return_value.messages.create = AsyncMock(return_value=claude_response)

                await agent.chat(brand, session, "Aide-moi avec Instagram", "user-123")

        assert session.title == "Aide-moi avec Instagram"

    @pytest.mark.asyncio
    async def test_chat_claude_failure_returns_fallback(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.add = AsyncMock()

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "System prompt"
            with patch.object(agent, "_get_client") as mock_client:
                mock_client.return_value.messages.create = AsyncMock(
                    side_effect=Exception("API down")
                )

                result = await agent.chat(brand, session, "Test", "user-123")

        # Should still save user + fallback assistant message
        assert db.add.call_count == 2
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_increments_message_count(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.add = AsyncMock()

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        claude_response = _mock_claude_response("OK")

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "System prompt"
            with patch.object(agent, "_get_client") as mock_client:
                mock_client.return_value.messages.create = AsyncMock(return_value=claude_response)

                await agent.chat(brand, session, "Test", "user-123")

        # message_count incremented twice: once for user, once for assistant
        assert session.message_count == 2

    @pytest.mark.asyncio
    async def test_chat_with_vision(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.add = AsyncMock()
        agent._vision = MagicMock()
        agent._vision.analyze_food_photo = AsyncMock(
            return_value="Un magnifique tartare de bœuf, bien dressé."
        )

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        claude_response = _mock_claude_response("Super photo de tartare !")

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "System prompt"
            with patch.object(agent, "_get_client") as mock_client:
                mock_client.return_value.messages.create = AsyncMock(return_value=claude_response)

                await agent.chat(
                    brand, session, "Voici mon plat", "user-123",
                    image_url="https://example.com/photo.jpg"
                )

        # Vision analyzer should have been called
        agent._vision.analyze_food_photo.assert_called_once_with(
            "https://example.com/photo.jpg",
            f"{brand.name} — {brand.niche}",
        )

    @pytest.mark.asyncio
    async def test_chat_stores_mem0_after_response(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.add = AsyncMock()

        brand = _make_brand()
        session = _make_session(brand_id=brand.id, message_count=0)

        history_result = MagicMock()
        history_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=history_result)

        claude_response = _mock_claude_response("Noté !")

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "System prompt"
            with patch.object(agent, "_get_client") as mock_client:
                mock_client.return_value.messages.create = AsyncMock(return_value=claude_response)

                await agent.chat(brand, session, "On publie le vendredi", "user-123")

        agent._memory.add.assert_called_once()
        call_kwargs = agent._memory.add.call_args.kwargs
        assert call_kwargs["user_id"] == "user-123"
        assert len(call_kwargs["messages"]) == 2


# ── Client Init Tests ────────────────────────────────────────────────────


class TestClientInit:
    def test_no_api_key_raises(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        with patch("app.services.ilyas.agent.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            with pytest.raises(RuntimeError, match="Anthropic API key"):
                agent._get_client()

    def test_client_reuses_existing(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        mock_client = MagicMock()
        agent._client = mock_client
        assert agent._get_client() is mock_client


# ── Context Debug Tests ──────────────────────────────────────────────────


class TestGetContext:
    @pytest.mark.asyncio
    async def test_get_context_returns_dict(self):
        db = _mock_db()
        agent = IlyasAgent(db)
        agent._memory = MagicMock()
        agent._memory.search = AsyncMock(return_value=[])
        agent._memory.get_all = AsyncMock(return_value=[])
        brand = _make_brand()

        with patch.object(agent, "_build_system_prompt", new_callable=AsyncMock) as mock_prompt:
            mock_prompt.return_value = "A" * 500

            result = await agent.get_context(brand, "user-123")

        assert "system_prompt_length" in result
        assert result["system_prompt_length"] == 500
        assert "mem0_memories_count" in result
        assert result["mem0_memories_count"] == 0
        assert "model" in result
