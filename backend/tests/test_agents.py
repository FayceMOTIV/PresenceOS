"""Tests pour les agents IA."""
import pytest
from unittest.mock import patch, MagicMock


def test_agents_config_import():
    """Test importing config module."""
    from app.agents.config import get_crew_llm, get_crew_verbose, get_crew_max_rpm
    assert callable(get_crew_llm)
    assert callable(get_crew_verbose)
    assert callable(get_crew_max_rpm)


def test_tools_import():
    """Test importing tool classes."""
    from app.agents.tools.brand_knowledge import BrandKnowledgeTool
    from app.agents.tools.web_scraper import WebScraperTool
    from app.agents.tools.trend_scanner import TrendScannerTool
    from app.agents.tools.metrics_reader import MetricsReaderTool

    assert BrandKnowledgeTool().name == "brand_knowledge"
    assert WebScraperTool().name == "web_scraper"
    assert TrendScannerTool().name == "trend_scanner"
    assert MetricsReaderTool().name == "metrics_reader"


def test_trend_scanner_generic():
    """Test trend scanner with generic fallback."""
    from app.agents.tools.trend_scanner import TrendScannerTool
    tool = TrendScannerTool()
    result = tool._run(industry="restaurant", platforms=["instagram"])
    assert "restaurant" in result.lower()
    assert "instagram" in result.lower()


def test_web_scraper_fallback():
    """Test web scraper fallback without API key."""
    from app.agents.tools.web_scraper import WebScraperTool
    tool = WebScraperTool()
    # With no firecrawl key, should use fallback
    result = tool._run(url="https://example.com")
    assert isinstance(result, str)


def test_agents_creation():
    """Test creating agents with mocked LLM."""
    with patch("app.agents.config.get_crew_llm") as mock_llm, \
         patch("app.agents.config.get_crew_verbose", return_value=False):
        # Create a mock LLM object with required attributes
        from crewai import LLM
        mock_llm.return_value = LLM(model="openai/gpt-4", api_key="test-key")

        from app.agents.agents.researcher import create_researcher_agent
        from app.agents.agents.writer import create_writer_agent
        from app.agents.agents.critic import create_critic_agent
        from app.agents.agents.analyst import create_analyst_agent

        researcher = create_researcher_agent()
        writer = create_writer_agent()
        critic = create_critic_agent()
        analyst = create_analyst_agent()

        assert researcher.role == "Veilleur Marketing Digital"
        assert writer.role == "Redacteur de Contenu Social Media"
        assert critic.role == "Editeur & Critique de Contenu"
        assert analyst.role == "Analyste de Performance Social Media"


def test_crews_import():
    """Test importing crew modules."""
    from app.agents.crews.content_crew import run_content_crew
    from app.agents.crews.onboarding_crew import (
        run_onboarding_extraction,
        determine_onboarding_mode,
        get_questions_for_mode,
        process_interview_answer,
        convert_to_brand_data,
        OnboardingMode,
        ONBOARDING_QUESTIONS,
    )
    from app.agents.crews.trends_crew import run_trends_crew
    assert callable(run_content_crew)
    assert callable(run_onboarding_extraction)
    assert callable(run_trends_crew)
    assert callable(determine_onboarding_mode)
    assert callable(get_questions_for_mode)
    assert callable(process_interview_answer)
    assert callable(convert_to_brand_data)


def test_tasks_import():
    """Test importing task modules."""
    from app.agents.tasks.content_tasks import (
        create_research_task,
        create_writing_task,
        create_review_task,
    )
    from app.agents.tasks.trend_tasks import create_trend_analysis_task
    from app.agents.tasks.onboarding_tasks import create_brand_extraction_task
    assert callable(create_research_task)
    assert callable(create_writing_task)
    assert callable(create_review_task)
    assert callable(create_trend_analysis_task)
    assert callable(create_brand_extraction_task)


@pytest.mark.asyncio
async def test_agent_generate_endpoint():
    """Test the generate content endpoint."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/agents/generate-content",
            json={
                "brand_id": "00000000-0000-0000-0000-000000000001",
                "platforms": ["linkedin"],
                "num_posts": 1,
            },
        )
        # Should return 401 (auth required) since we don't send a token
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_agent_extract_endpoint():
    """Test the extract brand endpoint."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/agents/extract-brand",
            json={"website_url": "https://example.com"},
        )
        # This endpoint doesn't require auth
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_agent_task_not_found():
    """Test getting a non-existent task."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/agents/tasks/nonexistent-id")
        assert response.status_code == 404


# ── Onboarding Intelligent Tests ─────────────────────────────────────


def test_onboarding_mode_full_auto():
    """Test FULL_AUTO mode detection (website + socials)."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode
    mode = determine_onboarding_mode(
        website_url="https://example.com",
        social_profiles=["instagram", "linkedin"],
    )
    assert mode == OnboardingMode.FULL_AUTO


def test_onboarding_mode_semi_auto_website():
    """Test SEMI_AUTO mode detection (website only)."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode
    mode = determine_onboarding_mode(website_url="https://example.com")
    assert mode == OnboardingMode.SEMI_AUTO


def test_onboarding_mode_semi_auto_socials():
    """Test SEMI_AUTO mode detection (socials only)."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode
    mode = determine_onboarding_mode(social_profiles=["instagram"])
    assert mode == OnboardingMode.SEMI_AUTO


def test_onboarding_mode_interview():
    """Test INTERVIEW mode detection (nothing provided)."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode
    mode = determine_onboarding_mode()
    assert mode == OnboardingMode.INTERVIEW


def test_onboarding_mode_empty_strings():
    """Test INTERVIEW mode with empty/whitespace inputs."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode
    mode = determine_onboarding_mode(website_url="", social_profiles=[])
    assert mode == OnboardingMode.INTERVIEW


def test_questions_for_interview_mode():
    """Test question filtering for interview mode."""
    from app.agents.crews.onboarding_crew import get_questions_for_mode, OnboardingMode
    questions = get_questions_for_mode(OnboardingMode.INTERVIEW)
    assert len(questions) > 5
    keys = [q["key"] for q in questions]
    assert "business_name" in keys
    assert "description" in keys
    assert "target_audience" in keys


def test_questions_for_semi_auto_mode():
    """Test question filtering for semi_auto mode."""
    from app.agents.crews.onboarding_crew import get_questions_for_mode, OnboardingMode
    questions = get_questions_for_mode(OnboardingMode.SEMI_AUTO)
    # Semi-auto should have fewer questions than interview
    interview_questions = get_questions_for_mode(OnboardingMode.INTERVIEW)
    assert len(questions) < len(interview_questions)
    # Should still include identity questions
    keys = [q["key"] for q in questions]
    assert "business_name" in keys


def test_questions_upsell_hidden_by_default():
    """Test that upsell question is hidden when no_website is not flagged."""
    from app.agents.crews.onboarding_crew import get_questions_for_mode, OnboardingMode
    questions = get_questions_for_mode(OnboardingMode.INTERVIEW)
    keys = [q["key"] for q in questions]
    assert "upsell_website" not in keys


def test_questions_upsell_shown_when_no_website():
    """Test that upsell question appears when user has no website."""
    from app.agents.crews.onboarding_crew import get_questions_for_mode, OnboardingMode
    questions = get_questions_for_mode(
        OnboardingMode.INTERVIEW,
        context={"_no_website": True},
    )
    keys = [q["key"] for q in questions]
    assert "upsell_website" in keys


def test_process_interview_answer_basic():
    """Test basic answer processing."""
    from app.agents.crews.onboarding_crew import process_interview_answer
    result = process_interview_answer(
        question_key="business_name",
        answer="Mon Restaurant",
        collected_data={},
    )
    assert result["collected_data"]["business_name"] == "Mon Restaurant"
    assert result["next_question"] is not None
    assert "progress" in result


def test_process_interview_answer_insight():
    """Test contextual insight generation for known answer."""
    from app.agents.crews.onboarding_crew import process_interview_answer
    result = process_interview_answer(
        question_key="business_type",
        answer="restaurant",
        collected_data={"business_name": "Test"},
    )
    assert result["insight"] is not None
    assert "restaurant" in result["insight"].lower() or "visuel" in result["insight"].lower()


def test_process_interview_answer_no_website_upsell():
    """Test upsell trigger when user has no website."""
    from app.agents.crews.onboarding_crew import process_interview_answer
    result = process_interview_answer(
        question_key="website_url",
        answer="",
        collected_data={"business_name": "Test"},
    )
    assert result["upsell"] is not None
    assert result["upsell"]["type"] == "website_upsell"
    assert "79" in result["upsell"]["price"]
    assert result["collected_data"].get("_no_website") is True


def test_process_interview_answer_progress():
    """Test progress calculation."""
    from app.agents.crews.onboarding_crew import process_interview_answer
    result = process_interview_answer(
        question_key="business_name",
        answer="Test Corp",
        collected_data={},
    )
    progress = result["progress"]
    assert "answered" in progress
    assert "total" in progress
    assert "percentage" in progress
    assert progress["answered"] == 1
    assert progress["percentage"] > 0


def test_convert_to_brand_data():
    """Test conversion of collected data to brand model format."""
    from app.agents.crews.onboarding_crew import convert_to_brand_data
    collected = {
        "business_name": "Test Restaurant",
        "business_type": "restaurant",
        "description": "Un super restaurant",
        "website_url": "https://test.com",
        "tone_style": "friendly",
        "target_audience": "Familles 30-50 ans",
        "locations": "Paris, Lyon",
        "content_constraints": "pas de jargon, pas d'anglicisme",
        "languages": ["fr", "en"],
    }
    result = convert_to_brand_data(collected)

    assert result["brand"]["name"] == "Test Restaurant"
    assert result["brand"]["brand_type"] == "restaurant"
    assert result["brand"]["locations"] == ["Paris", "Lyon"]
    assert result["voice"]["tone_formal"] == 30  # friendly mapping
    assert result["voice"]["tone_playful"] == 70
    assert result["voice"]["primary_language"] == "fr"
    assert "pas de jargon" in result["voice"]["words_to_avoid"]


def test_convert_to_brand_data_defaults():
    """Test conversion with minimal/empty data uses sensible defaults."""
    from app.agents.crews.onboarding_crew import convert_to_brand_data
    result = convert_to_brand_data({})

    assert result["brand"]["name"] == ""
    assert result["brand"]["brand_type"] == "other"
    assert result["voice"]["tone_formal"] == 30  # friendly default
    assert result["voice"]["primary_language"] == "fr"


def test_competitor_analysis_with_urls():
    """Test competitor analysis extracts URLs."""
    from app.agents.crews.onboarding_crew import _run_competitor_analysis
    result = _run_competitor_analysis("https://example.com, Mon Concurrent")
    assert result is not None
    assert result["type"] == "competitor_analysis"
    assert result["count"] >= 1
    assert len(result["competitors"]) >= 1


def test_competitor_analysis_empty():
    """Test competitor analysis with empty input."""
    from app.agents.crews.onboarding_crew import _run_competitor_analysis
    result = _run_competitor_analysis("")
    assert result is None


def test_onboarding_questions_structure():
    """Test that all questions have required fields."""
    from app.agents.crews.onboarding_crew import ONBOARDING_QUESTIONS
    required_fields = {"key", "question", "type", "category", "modes"}
    for q in ONBOARDING_QUESTIONS:
        for field in required_fields:
            assert field in q, f"Question {q.get('key', 'unknown')} missing field: {field}"


@pytest.mark.asyncio
async def test_onboarding_start_endpoint():
    """Test the onboarding start endpoint."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/agents/onboarding/start",
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["mode"] == "interview"
        assert len(data["questions"]) > 0
        assert data["first_question"] is not None


@pytest.mark.asyncio
async def test_onboarding_start_with_website():
    """Test onboarding start with website URL."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/agents/onboarding/start",
            json={"website_url": "https://example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "semi_auto"


@pytest.mark.asyncio
async def test_onboarding_answer_endpoint():
    """Test the onboarding answer endpoint (start + answer flow)."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Start a session
        start_response = await client.post(
            "/api/v1/agents/onboarding/start",
            json={},
        )
        session_id = start_response.json()["session_id"]

        # Submit an answer
        answer_response = await client.post(
            "/api/v1/agents/onboarding/answer",
            json={
                "session_id": session_id,
                "question_key": "business_name",
                "answer": "Mon Restaurant Test",
            },
        )
        assert answer_response.status_code == 200
        data = answer_response.json()
        assert "next_question" in data
        assert "progress" in data
        assert data["is_complete"] is False


@pytest.mark.asyncio
async def test_onboarding_answer_invalid_session():
    """Test onboarding answer with invalid session."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/agents/onboarding/answer",
            json={
                "session_id": "nonexistent",
                "question_key": "business_name",
                "answer": "Test",
            },
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_onboarding_complete_endpoint():
    """Test the onboarding complete endpoint."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Start a session
        start_response = await client.post(
            "/api/v1/agents/onboarding/start",
            json={},
        )
        session_id = start_response.json()["session_id"]

        # Submit some answers
        await client.post(
            "/api/v1/agents/onboarding/answer",
            json={
                "session_id": session_id,
                "question_key": "business_name",
                "answer": "Test Brand",
            },
        )

        # Complete the onboarding
        complete_response = await client.post(
            f"/api/v1/agents/onboarding/complete?session_id={session_id}",
        )
        assert complete_response.status_code == 200
        data = complete_response.json()
        assert data["status"] == "completed"
        assert "brand_data" in data
        assert data["brand_data"]["brand"]["name"] == "Test Brand"


@pytest.mark.asyncio
async def test_onboarding_complete_invalid_session():
    """Test onboarding complete with invalid session."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/agents/onboarding/complete?session_id=nonexistent",
        )
        assert response.status_code == 404
