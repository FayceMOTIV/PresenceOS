"""
PresenceOS - AI Proposals Tests

Tests for proposal generation, approve/reject/regenerate, caption editing.
"""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.ai_proposal import AIProposal, ProposalSource, ProposalStatus
from app.models.compiled_kb import CompiledKB
from app.models.media import MediaAsset
from app.services.proposal_generator import ProposalGenerator
from app.services.prompt_builder import PromptBuilder


# ── Mock Builders ────────────────────────────────────────────────────────


def _mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    return db


def _mock_kb(version=1) -> MagicMock:
    kb = MagicMock(spec=CompiledKB)
    kb.brand_id = uuid.uuid4()
    kb.kb_version = version
    kb.identity = {"name": "Le Bistrot", "type": "restaurant", "voice": {"language": "fr"}}
    kb.menu = {"total_dishes": 3, "categories": {}}
    kb.media = {"total_assets": 2, "assets": []}
    kb.today = {"has_brief": False}
    kb.posting_history = {"last_7_days_count": 2}
    kb.performance = {}
    return kb


def _mock_claude_response(caption: str, confidence: float = 0.8) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=json.dumps({
        "caption": caption,
        "hashtags": ["#food", "#restaurant"],
        "confidence": confidence,
        "reasoning": "Test reasoning",
    }))]
    return response


def _mock_proposal(
    status="pending",
    source="request",
    caption="Test caption",
) -> MagicMock:
    proposal = MagicMock(spec=AIProposal)
    proposal.id = uuid.uuid4()
    proposal.brand_id = uuid.uuid4()
    proposal.proposal_type = "post"
    proposal.platform = "instagram"
    proposal.caption = caption
    proposal.hashtags = ["#food"]
    proposal.source = source
    proposal.source_id = None
    proposal.status = status
    proposal.kb_version = 1
    proposal.confidence_score = 0.8
    proposal.image_url = None
    proposal.video_url = None
    proposal.improved_image_url = None
    proposal.scheduled_at = None
    proposal.published_at = None
    proposal.rejection_reason = None
    proposal.created_at = datetime.now(timezone.utc)
    proposal.updated_at = datetime.now(timezone.utc)
    return proposal


# ── Generator Tests ──────────────────────────────────────────────────────


class TestGenerateFromRequest:
    """Tests for free-text request generation."""

    @pytest.mark.asyncio
    async def test_generate_from_request_success(self):
        db = _mock_db()
        kb = _mock_kb()

        # Mock KB lookup
        kb_result = MagicMock()
        kb_result.scalar_one_or_none.return_value = kb
        # Mock proposal lookup (new, not existing)
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[kb_result, no_result])

        generator = ProposalGenerator(db)

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response("Post sur nos desserts 🍰")
            )
            proposal = await generator.generate_from_request(
                str(uuid.uuid4()),
                "Fais un post sur nos desserts",
                "post",
                "instagram",
            )

        db.add.assert_called_once()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_generate_uses_sonnet_for_requests(self):
        """Free-text requests should use Sonnet (complex=True)."""
        db = _mock_db()
        kb = _mock_kb()

        kb_result = MagicMock()
        kb_result.scalar_one_or_none.return_value = kb
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[kb_result, no_result])

        generator = ProposalGenerator(db)

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response("Caption")
            )
            await generator.generate_from_request(
                str(uuid.uuid4()), "Post", "post", "instagram"
            )

            # Verify Sonnet model was used
            call_args = mock_client.return_value.messages.create.call_args
            assert "sonnet" in call_args.kwargs.get("model", "").lower() or "sonnet" in call_args[1].get("model", "").lower()


class TestGenerateFromBrief:
    """Tests for daily brief generation."""

    @pytest.mark.asyncio
    async def test_generate_from_brief_success(self):
        db = _mock_db()
        kb = _mock_kb()

        kb_result = MagicMock()
        kb_result.scalar_one_or_none.return_value = kb
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[kb_result, no_result])

        generator = ProposalGenerator(db)

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response("Plat du jour: magret 🍖")
            )
            proposal = await generator.generate_from_brief(
                str(uuid.uuid4()),
                "Aujourd'hui magret de canard en plat du jour",
            )

        db.add.assert_called_once()


class TestGenerateFromAsset:
    """Tests for asset-based generation."""

    @pytest.mark.asyncio
    async def test_generate_from_asset_success(self):
        db = _mock_db()
        kb = _mock_kb()

        asset = MagicMock(spec=MediaAsset)
        asset.id = uuid.uuid4()
        asset.public_url = "https://cdn.example.com/photo.jpg"
        asset.improved_url = None
        asset.ai_description = "Photo d'une pizza"
        asset.asset_label = "pizza"
        asset.linked_dish_id = None

        # Returns: asset, kb, no existing proposal
        asset_result = MagicMock()
        asset_result.scalar_one_or_none.return_value = asset
        kb_result = MagicMock()
        kb_result.scalar_one_or_none.return_value = kb
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[asset_result, kb_result, no_result])

        generator = ProposalGenerator(db)

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response("Notre pizza artisanale 🍕")
            )
            proposal = await generator.generate_from_asset(
                str(uuid.uuid4()),
                str(asset.id),
            )

        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_from_asset_not_found(self):
        db = _mock_db()
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=no_result)

        generator = ProposalGenerator(db)
        with pytest.raises(ValueError, match="not found"):
            await generator.generate_from_asset(
                str(uuid.uuid4()), str(uuid.uuid4())
            )


class TestRegenerateVariant:
    """Tests for proposal regeneration."""

    @pytest.mark.asyncio
    async def test_regenerate_from_request_source(self):
        db = _mock_db()
        original = _mock_proposal(source=ProposalSource.REQUEST.value, caption="Old caption")
        kb = _mock_kb(version=1)

        # Mock KB with proper attributes
        kb_orm = MagicMock(spec=CompiledKB)
        kb_orm.brand_id = original.brand_id
        kb_orm.kb_version = 1
        kb_orm.identity = {"name": "Le Bistrot", "type": "restaurant", "voice": {"language": "fr"}}
        kb_orm.menu = {"total_dishes": 3, "categories": {}}
        kb_orm.media = {"total_assets": 2, "assets": []}
        kb_orm.today = {"has_brief": False}
        kb_orm.posting_history = {"last_7_days_count": 2}
        kb_orm.performance = {}

        # Returns: KB lookup, then no existing proposal
        kb_result = MagicMock()
        kb_result.scalar_one_or_none.return_value = kb_orm
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(side_effect=[kb_result, no_result])

        generator = ProposalGenerator(db)

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response("New variant")
            )
            new_proposal = await generator.generate_from_request(
                str(original.brand_id),
                "Variante test",
                "post",
                "instagram",
            )

        db.add.assert_called()

    @pytest.mark.asyncio
    async def test_regenerate_not_found(self):
        db = _mock_db()
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=no_result)

        generator = ProposalGenerator(db)
        with pytest.raises(ValueError, match="not found"):
            await generator.regenerate_variant(str(uuid.uuid4()))


# ── LLM Response Parsing ─────────────────────────────────────────────────


class TestLLMParsing:
    """Tests for LLM response parsing."""

    @pytest.mark.asyncio
    async def test_parse_valid_json(self):
        db = _mock_db()
        generator = ProposalGenerator(db)

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(
                return_value=_mock_claude_response("Caption test", 0.92)
            )
            result = await generator._call_llm("system", "user")

        assert result["caption"] == "Caption test"
        assert result["confidence"] == 0.92

    @pytest.mark.asyncio
    async def test_parse_json_with_surrounding_text(self):
        db = _mock_db()
        generator = ProposalGenerator(db)

        response = MagicMock()
        response.content = [MagicMock(text='Sure! Here is the result:\n{"caption": "Test", "hashtags": [], "confidence": 0.7, "reasoning": "ok"}\nHope this helps!')]

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(return_value=response)
            result = await generator._call_llm("system", "user")

        assert result["caption"] == "Test"

    @pytest.mark.asyncio
    async def test_parse_no_json_raises(self):
        db = _mock_db()
        generator = ProposalGenerator(db)

        response = MagicMock()
        response.content = [MagicMock(text="I couldn't generate anything.")]

        with patch.object(generator, "_get_client") as mock_client:
            mock_client.return_value.messages.create = AsyncMock(return_value=response)
            with pytest.raises(ValueError, match="No JSON"):
                await generator._call_llm("system", "user")


class TestUpsertProposal:
    """Tests for proposal upsert logic."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new(self):
        db = _mock_db()
        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None
        # When proposal_id is None, no execute call needed
        generator = ProposalGenerator(db)

        proposal = await generator._upsert_proposal(
            proposal_id=None,
            brand_id=str(uuid.uuid4()),
            source="request",
            source_id=None,
            result={"caption": "New", "hashtags": ["#test"], "confidence": 0.8},
            kb_version=1,
        )

        db.add.assert_called_once()
        db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self):
        db = _mock_db()
        existing = _mock_proposal()
        result = MagicMock()
        result.scalar_one_or_none.return_value = existing
        db.execute = AsyncMock(return_value=result)

        generator = ProposalGenerator(db)

        proposal = await generator._upsert_proposal(
            proposal_id=str(existing.id),
            brand_id=str(existing.brand_id),
            source="request",
            source_id=None,
            result={"caption": "Updated", "hashtags": ["#new"], "confidence": 0.9},
            kb_version=2,
        )

        assert existing.caption == "Updated"
        assert existing.confidence_score == 0.9
        assert existing.kb_version == 2
