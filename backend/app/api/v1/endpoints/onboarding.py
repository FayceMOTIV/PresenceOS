"""Endpoints API dedies a l'onboarding intelligent (Phase 2)."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone

router = APIRouter()


# === Schemas ===

class OnboardingStartRequest(BaseModel):
    website_url: Optional[str] = None
    social_profiles: Optional[list[str]] = None


class OnboardingAnswerRequest(BaseModel):
    session_id: str
    question_key: str
    answer: str


class OnboardingStartResponse(BaseModel):
    session_id: str
    mode: str
    questions: list[dict]
    first_question: Optional[dict] = None
    extracted_data: Optional[dict] = None
    message: str


# === Stockage en memoire des sessions d'onboarding ===
_onboarding_sessions: dict[str, dict] = {}

# Stockage des taches d'extraction (partage avec agents si necessaire)
_extraction_tasks: dict[str, dict] = {}


# === Endpoints ===


@router.post("/start", response_model=OnboardingStartResponse)
async def start_onboarding(
    request: OnboardingStartRequest,
    background_tasks: BackgroundTasks,
):
    """
    Demarre une session d'onboarding intelligent.
    Determine le mode (full_auto, semi_auto, interview) et retourne les questions.
    Si un website_url est fourni, lance l'extraction en arriere-plan.
    """
    from app.agents.crews.onboarding_crew import (
        determine_onboarding_mode,
        get_questions_for_mode,
    )

    mode = determine_onboarding_mode(
        website_url=request.website_url,
        social_profiles=request.social_profiles,
    )

    session_id = str(uuid4())
    collected_data: dict = {}
    extracted_data: dict = {}

    if request.website_url:
        collected_data["website_url"] = request.website_url
    if request.social_profiles:
        collected_data["social_profiles"] = request.social_profiles

    # Si mode auto/semi-auto, lancer l'extraction en background
    extraction_task_id = None
    if request.website_url and mode.value in ("full_auto", "semi_auto"):
        extraction_task_id = str(uuid4())
        _extraction_tasks[extraction_task_id] = {
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        }
        background_tasks.add_task(
            _run_extraction_background,
            extraction_task_id,
            session_id,
            request.website_url,
        )

    questions = get_questions_for_mode(mode, context=collected_data, extracted_data=extracted_data)

    _onboarding_sessions[session_id] = {
        "mode": mode.value,
        "collected_data": collected_data,
        "extracted_data": extracted_data,
        "extraction_task_id": extraction_task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    first_question = questions[0] if questions else None

    return OnboardingStartResponse(
        session_id=session_id,
        mode=mode.value,
        questions=questions,
        first_question=first_question,
        extracted_data=None,
        message=_get_welcome_message(mode.value),
    )


@router.post("/answer")
async def submit_onboarding_answer(request: OnboardingAnswerRequest):
    """
    Soumet une reponse a une question d'onboarding.
    Retourne l'insight contextuel, l'upsell eventuel, et la question suivante.
    Utilise les donnees extraites pour le skip adaptatif.
    """
    from app.agents.crews.onboarding_crew import process_interview_answer

    session = _onboarding_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session d'onboarding non trouvee")

    collected_data = session.get("collected_data", {})
    extracted_data = session.get("extracted_data", {})

    result = process_interview_answer(
        question_key=request.question_key,
        answer=request.answer,
        collected_data=collected_data,
        extracted_data=extracted_data,
    )

    _onboarding_sessions[request.session_id]["collected_data"] = result["collected_data"]

    return {
        "insight": result.get("insight"),
        "upsell": result.get("upsell"),
        "competitor_analysis": result.get("competitor_analysis"),
        "next_question": result.get("next_question"),
        "progress": result.get("progress"),
        "is_complete": result.get("next_question") is None,
    }


@router.post("/complete")
async def complete_onboarding(session_id: str):
    """
    Finalise l'onboarding : convertit les donnees collectees en format Brand + BrandVoice.
    """
    from app.agents.crews.onboarding_crew import convert_to_brand_data

    session = _onboarding_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session d'onboarding non trouvee")

    collected_data = session.get("collected_data", {})
    brand_data = convert_to_brand_data(collected_data)

    del _onboarding_sessions[session_id]

    return {
        "status": "completed",
        "brand_data": brand_data,
        "message": "Onboarding termine avec succes ! Vos donnees sont pretes.",
    }


@router.get("/status/{session_id}")
async def get_onboarding_status(session_id: str):
    """
    Retourne le statut d'une session d'onboarding,
    y compris la progression de l'extraction si applicable.
    """
    session = _onboarding_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session d'onboarding non trouvee")

    extraction_status = None
    extraction_task_id = session.get("extraction_task_id")
    if extraction_task_id and extraction_task_id in _extraction_tasks:
        extraction_status = _extraction_tasks[extraction_task_id]

    from app.agents.crews.onboarding_crew import _calculate_progress

    collected_data = session.get("collected_data", {})
    extracted_data = session.get("extracted_data", {})

    return {
        "session_id": session_id,
        "mode": session.get("mode"),
        "progress": _calculate_progress(collected_data, extracted_data),
        "extraction_status": extraction_status.get("status") if extraction_status else None,
        "extracted_data": extracted_data if extracted_data else None,
    }


# === Fonctions background ===

def _run_extraction_background(
    task_id: str,
    session_id: str,
    website_url: str,
):
    """Execute l'extraction de marque en background et stocke dans la session."""
    _extraction_tasks[task_id]["status"] = "running"
    try:
        from app.agents.crews.onboarding_crew import run_onboarding_extraction

        result = run_onboarding_extraction(website_url)
        _extraction_tasks[task_id]["status"] = "completed"
        _extraction_tasks[task_id]["result"] = result

        # Mettre a jour la session avec les donnees extraites
        if session_id in _onboarding_sessions:
            _onboarding_sessions[session_id]["extracted_data"] = result
    except Exception as e:
        _extraction_tasks[task_id]["status"] = "failed"
        _extraction_tasks[task_id]["error"] = str(e)


def _get_welcome_message(mode: str) -> str:
    """Retourne le message de bienvenue selon le mode."""
    messages = {
        "full_auto": (
            "Parfait ! J'ai detecte votre site web et vos reseaux sociaux. "
            "Je vais analyser tout ca pour pre-remplir votre profil. "
            "Quelques questions complementaires pour affiner..."
        ),
        "semi_auto": (
            "Super ! J'ai une source d'informations pour demarrer. "
            "Je vais completer avec quelques questions ciblees."
        ),
        "interview": (
            "Bienvenue ! Je suis votre assistant PresenceOS. "
            "Je vais vous poser quelques questions pour configurer "
            "votre marque de maniere optimale. C'est parti !"
        ),
    }
    return messages.get(mode, messages["interview"])
