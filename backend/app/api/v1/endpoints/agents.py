"""Endpoints API pour les agents IA."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.api.v1.deps import CurrentUser, DBSession

router = APIRouter()

# === Schemas ===


class ContentGenerationRequest(BaseModel):
    brand_id: UUID
    platforms: list[str] = Field(default=["linkedin", "instagram"])
    num_posts: int = Field(default=3, ge=1, le=10)
    topic: Optional[str] = None
    industry: Optional[str] = None
    tone: Optional[str] = None


class TrendScanRequest(BaseModel):
    brand_id: UUID
    industry: str
    platforms: list[str] = Field(default=["instagram", "linkedin"])


class AnalyzeBrandRequest(BaseModel):
    brand_id: UUID
    website_url: str


class OnboardingExtractionRequest(BaseModel):
    website_url: str


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


class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


# === Stockage en memoire des taches (remplacer par Redis/DB en production) ===
_agent_tasks: dict[str, dict] = {}

# === Stockage des sessions d'onboarding ===
_onboarding_sessions: dict[str, dict] = {}


# === Endpoints ===


@router.post("/generate-content", response_model=AgentTaskResponse)
async def generate_content(
    request: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DBSession,
):
    """Lance le Crew de generation de contenu en arriere-plan."""
    task_id = str(uuid4())
    _agent_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_content_generation,
        task_id,
        str(request.brand_id),
        request.platforms,
        request.num_posts,
        request.topic,
        request.industry,
        request.tone,
    )

    return AgentTaskResponse(
        task_id=task_id,
        status="pending",
        message="Crew de generation de contenu lance. Utilisez GET /agents/tasks/{task_id} pour suivre.",
    )


@router.post("/scan-trends", response_model=AgentTaskResponse)
async def scan_trends(
    request: TrendScanRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DBSession,
):
    """Lance le Crew d'analyse de tendances en arriere-plan."""
    task_id = str(uuid4())
    _agent_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_trends_scan,
        task_id,
        str(request.brand_id),
        request.industry,
        request.platforms,
    )

    return AgentTaskResponse(
        task_id=task_id,
        status="pending",
        message="Crew de scan de tendances lance.",
    )


@router.post("/analyze-brand", response_model=AgentTaskResponse)
async def analyze_brand(
    request: AnalyzeBrandRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DBSession,
):
    """Lance le Crew d'onboarding pour analyser un site web et extraire l'identite de marque."""
    task_id = str(uuid4())
    _agent_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_onboarding_extraction,
        task_id,
        request.website_url,
    )

    return AgentTaskResponse(
        task_id=task_id,
        status="pending",
        message="Analyse de marque en cours...",
    )


@router.post("/extract-brand", response_model=AgentTaskResponse)
async def extract_brand_from_website(
    request: OnboardingExtractionRequest,
    background_tasks: BackgroundTasks,
):
    """Extrait les infos de marque d'un site web via l'agent d'onboarding."""
    task_id = str(uuid4())
    _agent_tasks[task_id] = {
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_onboarding_extraction,
        task_id,
        request.website_url,
    )

    return AgentTaskResponse(
        task_id=task_id,
        status="pending",
        message="Extraction en cours...",
    )


@router.get("/status/{task_id}")
async def get_agent_task_status(task_id: str):
    """Recupere le statut et le resultat d'une tache agent."""
    task = _agent_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tache non trouvee")
    return task


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Recupere le statut et le resultat d'une tache agent (alias)."""
    task = _agent_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tache non trouvee")
    return task


@router.post("/onboarding/start", response_model=OnboardingStartResponse)
async def start_onboarding(request: OnboardingStartRequest):
    """
    Demarre une session d'onboarding intelligent.
    Determine le mode (full_auto, semi_auto, interview) et retourne les questions.
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

    if request.website_url:
        collected_data["website_url"] = request.website_url
    if request.social_profiles:
        collected_data["social_profiles"] = request.social_profiles

    questions = get_questions_for_mode(mode, context=collected_data)

    _onboarding_sessions[session_id] = {
        "mode": mode.value,
        "collected_data": collected_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    extracted_data = None
    if request.website_url and mode.value in ("full_auto", "semi_auto"):
        task_id = str(uuid4())
        _agent_tasks[task_id] = {
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "result": None,
            "error": None,
        }
        _onboarding_sessions[session_id]["extraction_task_id"] = task_id

    first_question = questions[0] if questions else None

    return OnboardingStartResponse(
        session_id=session_id,
        mode=mode.value,
        questions=questions,
        first_question=first_question,
        extracted_data=extracted_data,
        message=_get_welcome_message(mode.value),
    )


@router.post("/onboarding/answer")
async def submit_onboarding_answer(request: OnboardingAnswerRequest):
    """
    Soumet une reponse a une question d'onboarding.
    Retourne l'insight contextuel, l'upsell eventuel, et la question suivante.
    """
    from app.agents.crews.onboarding_crew import process_interview_answer

    session = _onboarding_sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session d'onboarding non trouvee")

    collected_data = session.get("collected_data", {})

    result = process_interview_answer(
        question_key=request.question_key,
        answer=request.answer,
        collected_data=collected_data,
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


@router.post("/onboarding/complete")
async def complete_onboarding(session_id: str):
    """
    Finalise l'onboarding : convertit les donnees collectees en Brand + BrandVoice + KnowledgeItems.
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


# === Fonctions background ===


def _run_content_generation(
    task_id: str,
    brand_id: str,
    platforms: list[str],
    num_posts: int,
    topic: str | None,
    industry: str | None,
    tone: str | None = None,
):
    """Execute le Content Crew en background."""
    _agent_tasks[task_id]["status"] = "running"
    try:
        from app.agents.crews.content_crew import run_content_crew

        result = run_content_crew(
            brand_id=brand_id,
            platforms=platforms,
            num_posts=num_posts,
            topic=topic,
            industry=industry,
            tone=tone,
        )
        _agent_tasks[task_id]["status"] = "completed"
        _agent_tasks[task_id]["result"] = result
    except Exception as e:
        _agent_tasks[task_id]["status"] = "failed"
        _agent_tasks[task_id]["error"] = str(e)


def _run_trends_scan(
    task_id: str,
    brand_id: str,
    industry: str,
    platforms: list[str],
):
    """Execute le Trends Crew en background."""
    _agent_tasks[task_id]["status"] = "running"
    try:
        from app.agents.crews.trends_crew import run_trends_crew

        result = run_trends_crew(
            brand_id=brand_id,
            industry=industry,
            platforms=platforms,
        )
        _agent_tasks[task_id]["status"] = "completed"
        _agent_tasks[task_id]["result"] = result
    except Exception as e:
        _agent_tasks[task_id]["status"] = "failed"
        _agent_tasks[task_id]["error"] = str(e)


def _run_onboarding_extraction(task_id: str, website_url: str):
    """Execute l'Onboarding Crew en background."""
    _agent_tasks[task_id]["status"] = "running"
    try:
        from app.agents.crews.onboarding_crew import run_onboarding_extraction

        result = run_onboarding_extraction(website_url)
        _agent_tasks[task_id]["status"] = "completed"
        _agent_tasks[task_id]["result"] = result
    except Exception as e:
        _agent_tasks[task_id]["status"] = "failed"
        _agent_tasks[task_id]["error"] = str(e)
