"""
PresenceOS - Phase 2 Tests: Onboarding Intelligent Adaptatif.
"""
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient


# ── Mode detection ───────────────────────────────────────────────────


def test_determine_mode_full_auto():
    """FULL_AUTO quand website + social profiles fournis."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode

    mode = determine_onboarding_mode(
        website_url="https://example.com",
        social_profiles=["instagram", "linkedin"],
    )
    assert mode == OnboardingMode.FULL_AUTO


def test_determine_mode_semi_auto_website_only():
    """SEMI_AUTO quand seulement website fourni."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode

    mode = determine_onboarding_mode(
        website_url="https://example.com",
        social_profiles=None,
    )
    assert mode == OnboardingMode.SEMI_AUTO


def test_determine_mode_semi_auto_socials_only():
    """SEMI_AUTO quand seulement social profiles fournis."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode

    mode = determine_onboarding_mode(
        website_url=None,
        social_profiles=["instagram"],
    )
    assert mode == OnboardingMode.SEMI_AUTO


def test_determine_mode_interview():
    """INTERVIEW quand rien n'est fourni."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode

    mode = determine_onboarding_mode(
        website_url=None,
        social_profiles=None,
    )
    assert mode == OnboardingMode.INTERVIEW


def test_determine_mode_interview_empty_strings():
    """INTERVIEW quand des chaines vides sont fournies."""
    from app.agents.crews.onboarding_crew import determine_onboarding_mode, OnboardingMode

    mode = determine_onboarding_mode(
        website_url="",
        social_profiles=[],
    )
    assert mode == OnboardingMode.INTERVIEW


# ── Adaptive question skipping ───────────────────────────────────────


def test_adaptive_skip_with_extracted_data():
    """Les questions avec maps_to sont sautees si la donnee est extraite."""
    from app.agents.crews.onboarding_crew import get_questions_for_mode, OnboardingMode

    extracted = {
        "business_name": "Test Corp",
        "description": "A test company",
    }

    questions = get_questions_for_mode(
        OnboardingMode.INTERVIEW,
        context={},
        extracted_data=extracted,
    )

    # business_name et description ne doivent pas etre dans les questions
    question_keys = [q["key"] for q in questions]
    assert "business_name" not in question_keys
    assert "description" not in question_keys


def test_no_skip_without_extracted_data():
    """Sans donnees extraites, toutes les questions interview sont presentes."""
    from app.agents.crews.onboarding_crew import get_questions_for_mode, OnboardingMode

    questions = get_questions_for_mode(
        OnboardingMode.INTERVIEW,
        context={},
        extracted_data={},
    )

    question_keys = [q["key"] for q in questions]
    assert "business_name" in question_keys
    assert "description" in question_keys


# ── Questions count and categories ───────────────────────────────────


def test_questions_count_at_least_25():
    """On a au moins 25 questions au total."""
    from app.agents.crews.onboarding_crew import ONBOARDING_QUESTIONS

    assert len(ONBOARDING_QUESTIONS) >= 25


def test_questions_have_required_categories():
    """Les questions couvrent les categories identity, product, audience, voice, goals."""
    from app.agents.crews.onboarding_crew import ONBOARDING_QUESTIONS

    categories = set(q["category"] for q in ONBOARDING_QUESTIONS)
    for cat in ["identity", "product", "audience", "voice", "goals"]:
        assert cat in categories, f"Categorie manquante: {cat}"


def test_questions_have_required_keys():
    """Chaque question a les champs requis."""
    from app.agents.crews.onboarding_crew import ONBOARDING_QUESTIONS

    for q in ONBOARDING_QUESTIONS:
        assert "key" in q
        assert "question" in q
        assert "type" in q
        assert "category" in q
        assert "modes" in q


# ── Progress calculation ─────────────────────────────────────────────


def test_progress_calculation_empty():
    """Progress a 0% sans reponses."""
    from app.agents.crews.onboarding_crew import _calculate_progress

    progress = _calculate_progress({}, {})
    assert progress["answered"] == 0
    assert progress["percentage"] == 0


def test_progress_calculation_with_answers():
    """Progress augmente avec les reponses."""
    from app.agents.crews.onboarding_crew import _calculate_progress

    collected = {
        "business_name": "Test",
        "business_type": "saas",
        "description": "A SaaS product",
    }
    progress = _calculate_progress(collected, {})
    assert progress["answered"] == 3
    assert progress["percentage"] > 0


def test_progress_ignores_internal_keys():
    """Les cles internes (_no_website) ne comptent pas dans la progression."""
    from app.agents.crews.onboarding_crew import _calculate_progress

    collected = {
        "business_name": "Test",
        "_no_website": True,
    }
    progress = _calculate_progress(collected, {})
    assert progress["answered"] == 1


# ── Process interview answer ─────────────────────────────────────────


def test_process_answer_returns_insight():
    """Un insight est genere pour business_type=restaurant."""
    from app.agents.crews.onboarding_crew import process_interview_answer

    result = process_interview_answer(
        question_key="business_type",
        answer="restaurant",
        collected_data={},
    )
    assert result["insight"] is not None
    assert "restaurant" in result["insight"].lower() or "visuel" in result["insight"].lower()


def test_process_answer_returns_next_question():
    """La prochaine question est retournee apres une reponse."""
    from app.agents.crews.onboarding_crew import process_interview_answer

    result = process_interview_answer(
        question_key="business_name",
        answer="Test Brand",
        collected_data={},
    )
    assert result["next_question"] is not None
    assert result["next_question"]["key"] != "business_name"


def test_process_answer_upsell_on_no_website():
    """Un upsell est genere quand l'utilisateur n'a pas de site."""
    from app.agents.crews.onboarding_crew import process_interview_answer

    result = process_interview_answer(
        question_key="website_url",
        answer="",
        collected_data={},
    )
    assert result["upsell"] is not None
    assert result["upsell"]["type"] == "website_upsell"


# ── Convert to brand data ────────────────────────────────────────────


def test_convert_to_brand_data_basic():
    """convert_to_brand_data retourne les champs brand, voice, metadata."""
    from app.agents.crews.onboarding_crew import convert_to_brand_data

    data = convert_to_brand_data({
        "business_name": "Test Restaurant",
        "business_type": "restaurant",
        "description": "Un restaurant de test",
        "tone_style": "friendly",
    })

    assert "brand" in data
    assert "voice" in data
    assert "metadata" in data
    assert data["brand"]["name"] == "Test Restaurant"
    assert data["brand"]["brand_type"] == "restaurant"
    assert data["voice"]["tone_playful"] == 70  # friendly tone


def test_convert_to_brand_data_locations():
    """Les locations sont parsees correctement."""
    from app.agents.crews.onboarding_crew import convert_to_brand_data

    data = convert_to_brand_data({
        "locations": "Paris, Lyon, Marseille",
    })
    assert data["brand"]["locations"] == ["Paris", "Lyon", "Marseille"]


# ── API endpoints ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_onboarding_start_endpoint_exists(client: AsyncClient):
    """POST /onboarding/start retourne 200."""
    response = await client.post(
        "/api/v1/onboarding/start",
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "mode" in data
    assert data["mode"] == "interview"


@pytest.mark.asyncio
async def test_onboarding_start_with_website(client: AsyncClient):
    """POST /onboarding/start avec website_url retourne semi_auto."""
    response = await client.post(
        "/api/v1/onboarding/start",
        json={"website_url": "https://example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "semi_auto"


@pytest.mark.asyncio
async def test_onboarding_start_full_auto(client: AsyncClient):
    """POST /onboarding/start avec website + socials retourne full_auto."""
    response = await client.post(
        "/api/v1/onboarding/start",
        json={
            "website_url": "https://example.com",
            "social_profiles": ["instagram"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "full_auto"


@pytest.mark.asyncio
async def test_onboarding_answer_endpoint(client: AsyncClient):
    """POST /onboarding/answer retourne une reponse valide."""
    # Start a session first
    start = await client.post(
        "/api/v1/onboarding/start",
        json={},
    )
    session_id = start.json()["session_id"]
    first_key = start.json()["first_question"]["key"]

    # Submit an answer
    response = await client.post(
        "/api/v1/onboarding/answer",
        json={
            "session_id": session_id,
            "question_key": first_key,
            "answer": "Test Brand",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "progress" in data
    assert "next_question" in data


@pytest.mark.asyncio
async def test_onboarding_answer_invalid_session(client: AsyncClient):
    """POST /onboarding/answer avec session invalide retourne 404."""
    response = await client.post(
        "/api/v1/onboarding/answer",
        json={
            "session_id": "nonexistent",
            "question_key": "business_name",
            "answer": "Test",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_onboarding_complete_endpoint(client: AsyncClient):
    """POST /onboarding/complete retourne les brand_data."""
    # Start a session
    start = await client.post(
        "/api/v1/onboarding/start",
        json={},
    )
    session_id = start.json()["session_id"]

    # Complete immediately
    response = await client.post(
        f"/api/v1/onboarding/complete?session_id={session_id}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "brand_data" in data


@pytest.mark.asyncio
async def test_onboarding_complete_invalid_session(client: AsyncClient):
    """POST /onboarding/complete avec session invalide retourne 404."""
    response = await client.post(
        "/api/v1/onboarding/complete?session_id=nonexistent",
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_onboarding_status_endpoint(client: AsyncClient):
    """GET /onboarding/status/{session_id} retourne le statut."""
    # Start a session
    start = await client.post(
        "/api/v1/onboarding/start",
        json={},
    )
    session_id = start.json()["session_id"]

    response = await client.get(f"/api/v1/onboarding/status/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert "progress" in data


@pytest.mark.asyncio
async def test_onboarding_status_invalid_session(client: AsyncClient):
    """GET /onboarding/status/{session_id} retourne 404 pour session inconnue."""
    response = await client.get("/api/v1/onboarding/status/nonexistent")
    assert response.status_code == 404


# ── Legacy agents onboarding endpoints still work ────────────────────


@pytest.mark.asyncio
async def test_legacy_agents_onboarding_start(client: AsyncClient):
    """POST /agents/onboarding/start fonctionne toujours (backward compat)."""
    response = await client.post(
        "/api/v1/agents/onboarding/start",
        json={},
    )
    assert response.status_code == 200
