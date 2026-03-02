"""
Tests — Sprint 4: Ilyas Conversational Onboarding + Business DNA
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.business_dna import BusinessDNA
from app.services.ilyas.onboarding_agent import (
    OnboardingAgent,
    ONBOARDING_QUESTIONS,
    TOTAL_STEPS,
)


# ── BusinessDNA model tests ──


class TestBusinessDNA:
    """Tests for the BusinessDNA dataclass."""

    def test_default_values(self):
        dna = BusinessDNA()
        assert dna.business_name == ""
        assert dna.business_type == ""
        assert dna.favorite_platforms == []
        assert dna.signature_dishes == []
        assert dna.no_go_topics == []
        assert dna.onboarding_complete is False
        assert dna.raw_answers == {}

    def test_to_dict(self):
        dna = BusinessDNA(
            business_name="Le Family's",
            business_type="restaurant",
            city="Marseille",
        )
        d = dna.to_dict()
        assert d["business_name"] == "Le Family's"
        assert d["business_type"] == "restaurant"
        assert d["city"] == "Marseille"
        assert isinstance(d["favorite_platforms"], list)

    def test_from_dict(self):
        data = {
            "business_name": "Chez Marcel",
            "business_type": "boulangerie",
            "cuisine_style": "viennoiseries",
            "city": "Paris",
            "onboarding_complete": True,
        }
        dna = BusinessDNA.from_dict(data)
        assert dna.business_name == "Chez Marcel"
        assert dna.business_type == "boulangerie"
        assert dna.onboarding_complete is True

    def test_from_dict_ignores_unknown_fields(self):
        data = {
            "business_name": "Test",
            "unknown_field": "should be ignored",
            "another_random": 42,
        }
        dna = BusinessDNA.from_dict(data)
        assert dna.business_name == "Test"
        assert not hasattr(dna, "unknown_field")

    def test_roundtrip(self):
        original = BusinessDNA(
            business_name="La Boucherie",
            business_type="boucherie",
            city="Lyon",
            neighborhood="Vieux Lyon",
            favorite_platforms=["instagram", "facebook"],
            signature_dishes=["côte de boeuf", "saucisson"],
            onboarding_complete=True,
            raw_answers={"business_name": "La Boucherie"},
        )
        data = original.to_dict()
        restored = BusinessDNA.from_dict(data)
        assert restored.business_name == original.business_name
        assert restored.favorite_platforms == original.favorite_platforms
        assert restored.signature_dishes == original.signature_dishes
        assert restored.onboarding_complete is True

    def test_system_prompt_section_empty(self):
        dna = BusinessDNA()
        assert dna.to_system_prompt_section() == ""

    def test_system_prompt_section_full(self):
        dna = BusinessDNA(
            business_name="Le Family's",
            business_type="restaurant",
            cuisine_style="libanais",
            city="Marseille",
            neighborhood="Vieux-Port",
            ambiance="cosy et familial",
            unique_selling_point="vue mer panoramique",
            target_audience="familles",
            tone_of_voice="chaleureux",
            favorite_platforms=["instagram", "tiktok"],
            posting_frequency="3 fois par semaine",
            signature_dishes=["fattoush", "kafta"],
            price_range="€€",
        )
        section = dna.to_system_prompt_section()
        assert "Le Family's" in section
        assert "libanais" in section
        assert "Marseille (Vieux-Port)" in section
        assert "cosy et familial" in section
        assert "instagram, tiktok" in section
        assert "fattoush, kafta" in section

    def test_system_prompt_section_partial(self):
        dna = BusinessDNA(business_name="Test", city="Paris")
        section = dna.to_system_prompt_section()
        assert "Test" in section
        assert "Paris" in section
        assert "Cuisine" not in section  # empty field not included


# ── OnboardingAgent tests ──


class TestOnboardingAgent:
    """Tests for the OnboardingAgent."""

    def test_questions_count(self):
        assert TOTAL_STEPS == 8
        assert len(ONBOARDING_QUESTIONS) == 8

    def test_questions_have_required_fields(self):
        for i, q in enumerate(ONBOARDING_QUESTIONS):
            assert "id" in q, f"Question {i} missing 'id'"
            assert "question" in q, f"Question {i} missing 'question'"
            assert "extract_prompt" in q, f"Question {i} missing 'extract_prompt'"
            assert len(q["question"]) > 10, f"Question {i} too short"

    def test_get_question_valid(self):
        agent = OnboardingAgent()
        q = agent.get_question(0)
        assert q is not None
        assert q["id"] == "business_name"

        q7 = agent.get_question(7)
        assert q7 is not None
        assert q7["id"] == "signature_dishes"

    def test_get_question_out_of_range(self):
        agent = OnboardingAgent()
        assert agent.get_question(-1) is None
        assert agent.get_question(8) is None
        assert agent.get_question(100) is None

    @pytest.mark.asyncio
    async def test_start_onboarding_fresh(self):
        """Start onboarding with no existing DNA."""
        agent = OnboardingAgent()
        agent._firestore = MagicMock()
        agent._firestore.get_subcollection_doc = AsyncMock(return_value=None)

        result = await agent.start_onboarding("biz-123")

        assert result["step"] == 0
        assert result["complete"] is False
        assert result["question"] is not None
        assert "Ilyas" in result["question"]

    @pytest.mark.asyncio
    async def test_start_onboarding_resume(self):
        """Resume onboarding from step 3 (3 answers already given)."""
        existing_dna = BusinessDNA(
            business_name="Le Family's",
            business_type="restaurant",
            city="Marseille",
            raw_answers={
                "business_name": "Le Family's",
                "business_type_and_cuisine": "restaurant libanais",
                "location": "Marseille Vieux-Port",
            },
        )
        agent = OnboardingAgent()
        agent._firestore = MagicMock()
        agent._firestore.get_subcollection_doc = AsyncMock(
            return_value=existing_dna.to_dict()
        )

        result = await agent.start_onboarding("biz-123")

        assert result["step"] == 3  # Next unanswered step
        assert result["complete"] is False
        assert result["question"] is not None

    @pytest.mark.asyncio
    async def test_start_onboarding_already_complete(self):
        """Start onboarding when DNA is already complete."""
        dna = BusinessDNA(onboarding_complete=True)
        agent = OnboardingAgent()
        agent._firestore = MagicMock()
        agent._firestore.get_subcollection_doc = AsyncMock(
            return_value=dna.to_dict()
        )

        result = await agent.start_onboarding("biz-123")

        assert result["complete"] is True
        assert result["question"] is None
        assert result["step"] == TOTAL_STEPS

    @pytest.mark.asyncio
    async def test_process_answer_step_0(self):
        """Process first answer (business name)."""
        agent = OnboardingAgent()
        agent._firestore = MagicMock()
        agent._firestore.get_subcollection_doc = AsyncMock(return_value=None)
        agent._firestore.set_subcollection_doc = AsyncMock(return_value=True)

        # Mock Haiku extraction
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"business_name": "Le Family\'s"}')]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        agent._client = mock_client

        result = await agent.process_answer("biz-123", 0, "C'est Le Family's")

        assert result["step"] == 0
        assert result["extracted"]["business_name"] == "Le Family's"
        assert result["next_step"] == 1
        assert result["next_question"] is not None
        assert result["complete"] is False

    @pytest.mark.asyncio
    async def test_process_answer_last_step(self):
        """Process last answer — should complete onboarding."""
        dna = BusinessDNA(
            business_name="Le Family's",
            raw_answers={q["id"]: "test" for q in ONBOARDING_QUESTIONS[:7]},
        )
        agent = OnboardingAgent()
        agent._firestore = MagicMock()
        agent._firestore.get_subcollection_doc = AsyncMock(
            return_value=dna.to_dict()
        )
        agent._firestore.set_subcollection_doc = AsyncMock(return_value=True)

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='{"signature_dishes": ["kafta", "fattoush"], "no_go_topics": []}')
        ]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        agent._client = mock_client

        result = await agent.process_answer("biz-123", 7, "kafta et fattoush")

        assert result["step"] == 7
        assert result["complete"] is True
        assert result["next_step"] is None
        assert result["next_question"] is None
        assert result["dna"]["onboarding_complete"] is True

    @pytest.mark.asyncio
    async def test_process_answer_extraction_failure_graceful(self):
        """Extraction failure should not crash — empty dict returned."""
        agent = OnboardingAgent()
        agent._firestore = MagicMock()
        agent._firestore.get_subcollection_doc = AsyncMock(return_value=None)
        agent._firestore.set_subcollection_doc = AsyncMock(return_value=True)

        # Mock client that raises
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        agent._client = mock_client

        result = await agent.process_answer("biz-123", 0, "Le Family's")

        assert result["step"] == 0
        assert result["extracted"] == {}
        assert result["next_step"] == 1  # Still advances
        assert result["complete"] is False

    def test_extract_answer_strips_markdown_code_blocks(self):
        """Haiku sometimes wraps JSON in ```json blocks."""
        agent = OnboardingAgent()

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text='```json\n{"business_name": "Chez Marcel"}\n```')
        ]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        agent._client = mock_client

        result = agent.extract_answer(0, "Chez Marcel")
        assert result["business_name"] == "Chez Marcel"


# ── FirestoreService tests ──


class TestFirestoreService:
    """Tests for FirestoreService graceful degradation."""

    @pytest.mark.asyncio
    async def test_get_document_no_firebase(self):
        """Should return None gracefully when Firebase not configured."""
        from app.services.firebase_firestore import FirestoreService

        svc = FirestoreService()
        with patch("app.services.firebase_firestore.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(firebase_project_id="")
            result = await svc.get_document("test", "doc1")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_document_no_firebase(self):
        """Should return False gracefully when Firebase not configured."""
        from app.services.firebase_firestore import FirestoreService

        svc = FirestoreService()
        with patch("app.services.firebase_firestore.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(firebase_project_id="")
            result = await svc.set_document("test", "doc1", {"key": "val"})
            assert result is False

    @pytest.mark.asyncio
    async def test_get_subcollection_doc_no_firebase(self):
        from app.services.firebase_firestore import FirestoreService

        svc = FirestoreService()
        with patch("app.services.firebase_firestore.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(firebase_project_id="")
            result = await svc.get_subcollection_doc("businesses", "biz1", "dna", "profile")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_subcollection_doc_no_firebase(self):
        from app.services.firebase_firestore import FirestoreService

        svc = FirestoreService()
        with patch("app.services.firebase_firestore.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(firebase_project_id="")
            result = await svc.set_subcollection_doc(
                "businesses", "biz1", "dna", "profile", {"key": "val"}
            )
            assert result is False


# ── Onboarding API endpoint tests ──


class TestOnboardingAPI:
    """Tests for the /v2/onboarding API endpoints."""

    @pytest.mark.asyncio
    async def test_start_endpoint_exists(self):
        """Verify the router has the start endpoint."""
        from app.api.v2.endpoints.onboarding import router

        routes = [r.path for r in router.routes]
        assert "/brands/{brand_id}/onboarding/start" in routes

    @pytest.mark.asyncio
    async def test_answer_endpoint_exists(self):
        from app.api.v2.endpoints.onboarding import router

        routes = [r.path for r in router.routes]
        assert "/brands/{brand_id}/onboarding/answer" in routes

    @pytest.mark.asyncio
    async def test_dna_endpoint_exists(self):
        from app.api.v2.endpoints.onboarding import router

        routes = [r.path for r in router.routes]
        assert "/brands/{brand_id}/onboarding/dna" in routes

    def test_answer_request_validation(self):
        from app.api.v2.endpoints.onboarding import AnswerRequest

        # Valid
        req = AnswerRequest(step=0, answer="Le Family's")
        assert req.step == 0

        # Invalid step (>= TOTAL_STEPS)
        with pytest.raises(Exception):
            AnswerRequest(step=99, answer="test")

        # Empty answer
        with pytest.raises(Exception):
            AnswerRequest(step=0, answer="")


# ── Agent DNA injection tests ──


class TestIlyasDNAInjection:
    """Tests for DNA context injection in Ilyas system prompt."""

    @pytest.mark.asyncio
    async def test_get_dna_context_returns_section(self):
        """When DNA exists, it should return a formatted section."""
        from app.services.ilyas.agent import IlyasAgent

        agent = IlyasAgent(db=MagicMock())

        dna = BusinessDNA(
            business_name="Le Family's",
            business_type="restaurant",
            cuisine_style="libanais",
            city="Marseille",
            onboarding_complete=True,
        )

        with patch(
            "app.services.ilyas.onboarding_agent.OnboardingAgent"
        ) as MockAgent:
            mock_onb = MockAgent.return_value
            mock_onb.get_dna = AsyncMock(return_value=dna)

            result = await agent._get_dna_context("biz-123")

        assert "Le Family's" in result
        assert "libanais" in result
        assert "Marseille" in result

    @pytest.mark.asyncio
    async def test_get_dna_context_returns_empty_when_no_dna(self):
        from app.services.ilyas.agent import IlyasAgent

        agent = IlyasAgent(db=MagicMock())

        with patch(
            "app.services.ilyas.onboarding_agent.OnboardingAgent"
        ) as MockAgent:
            mock_onb = MockAgent.return_value
            mock_onb.get_dna = AsyncMock(return_value=None)

            result = await agent._get_dna_context("biz-123")

        assert result == ""

    @pytest.mark.asyncio
    async def test_get_dna_context_returns_empty_when_incomplete(self):
        from app.services.ilyas.agent import IlyasAgent

        agent = IlyasAgent(db=MagicMock())
        dna = BusinessDNA(business_name="Test", onboarding_complete=False)

        with patch(
            "app.services.ilyas.onboarding_agent.OnboardingAgent"
        ) as MockAgent:
            mock_onb = MockAgent.return_value
            mock_onb.get_dna = AsyncMock(return_value=dna)

            result = await agent._get_dna_context("biz-123")

        assert result == ""

    @pytest.mark.asyncio
    async def test_get_dna_context_graceful_on_error(self):
        from app.services.ilyas.agent import IlyasAgent

        agent = IlyasAgent(db=MagicMock())

        with patch(
            "app.services.ilyas.onboarding_agent.OnboardingAgent",
            side_effect=Exception("Import error"),
        ):
            result = await agent._get_dna_context("biz-123")

        assert result == ""
