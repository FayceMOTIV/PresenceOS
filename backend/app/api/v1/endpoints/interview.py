"""
PresenceOS - Brand Interview Endpoints

AI-powered conversational interview to learn about a brand.
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.services.brand_interview import BrandInterviewService

router = APIRouter()
interview_service = BrandInterviewService()


# ── Schemas ─────────────────────────────────────────────────────────

class InterviewStartResponse(BaseModel):
    messages: list[dict]
    completeness: dict
    is_new: bool


class InterviewMessageRequest(BaseModel):
    message: str


class InterviewMessageResponse(BaseModel):
    ai_message: str
    extracted_items: list[dict]
    completeness: dict
    is_complete: bool


class InterviewStatusResponse(BaseModel):
    completeness: dict
    knowledge_count: int
    has_active_session: bool


# ── Endpoints ───────────────────────────────────────────────────────

@router.post("/brands/{brand_id}/start", response_model=InterviewStartResponse)
async def start_interview(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Start or resume a brand interview session."""
    await get_brand(brand_id, current_user, db)

    try:
        result = await interview_service.start_or_resume(str(brand_id), db)
        return InterviewStartResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur interview: {str(e)}")


@router.post("/brands/{brand_id}/message", response_model=InterviewMessageResponse)
async def send_message(
    brand_id: UUID,
    body: InterviewMessageRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Send a message in the interview and get AI response."""
    await get_brand(brand_id, current_user, db)

    if not body.message.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Message vide")

    try:
        result = await interview_service.process_message(str(brand_id), body.message, db)
        return InterviewMessageResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur interview: {str(e)}")


@router.get("/brands/{brand_id}/status", response_model=InterviewStatusResponse)
async def get_interview_status(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get interview completeness status for a brand."""
    await get_brand(brand_id, current_user, db)

    try:
        result = await interview_service.get_status(str(brand_id), db)
        return InterviewStatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur status: {str(e)}")
