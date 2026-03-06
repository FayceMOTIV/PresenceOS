"""
PresenceOS — Breakout API v2

Architecture async obligatoire (pipeline 60-120s) :
  POST /{brand_id}/generate → Celery task → retourne job_id
  GET  /{brand_id}/status/{job_id} → poll statut (PENDING/PROCESSING/SUCCESS/FAILURE)
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.workers.celery_app import celery_app

router = APIRouter()


# ── Request / Response models ────────────────────────────────────────────


class BreakoutGenerateRequest(BaseModel):
    source_type: str = Field(
        description="'ai_prompt' | 'image' | 'video'",
    )
    source_url: Optional[str] = None
    ai_prompt: Optional[str] = None


class BreakoutGenerateResponse(BaseModel):
    job_id: str
    status: str


class BreakoutStatusResponse(BaseModel):
    job_id: str
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None
    progress: int = 0


# ── Endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/{brand_id}/generate",
    response_model=BreakoutGenerateResponse,
    summary="Lance la génération Breakout en tâche Celery",
)
@limiter.limit("5/minute")
async def generate_breakout(
    request: Request,
    brand_id: str,
    body: BreakoutGenerateRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Lance le pipeline Breakout en arrière-plan via Celery."""
    await verify_brand_access(brand_id, user, db)

    if body.source_type not in ("ai_prompt", "image", "video"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_type must be 'ai_prompt', 'image', or 'video'",
        )

    if body.source_type == "ai_prompt" and not body.ai_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ai_prompt is required when source_type is 'ai_prompt'",
        )

    if body.source_type in ("image", "video") and not body.source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_url is required when source_type is 'image' or 'video'",
        )

    import uuid
    job_id = str(uuid.uuid4())

    # Lancer la tâche Celery (importée dynamiquement pour éviter circular)
    celery_app.send_task(
        "breakout.generate",
        args=[job_id, brand_id, body.source_type, body.source_url, body.ai_prompt],
        task_id=job_id,
    )

    return BreakoutGenerateResponse(job_id=job_id, status="queued")


@router.get(
    "/{brand_id}/status/{job_id}",
    response_model=BreakoutStatusResponse,
    summary="Poll le statut de la génération Breakout",
)
@limiter.limit("60/minute")
async def get_breakout_status(
    request: Request,
    brand_id: str,
    job_id: str,
    user: FirebaseUser,
    db: DBSession,
):
    """Le mobile appelle cet endpoint toutes les 3 secondes."""
    await verify_brand_access(brand_id, user, db)
    result = celery_app.AsyncResult(job_id)

    if result.state == "PENDING":
        return BreakoutStatusResponse(job_id=job_id, status="PENDING", progress=0)
    elif result.state == "PROGRESS":
        meta = result.info or {}
        return BreakoutStatusResponse(
            job_id=job_id,
            status="PROCESSING",
            progress=meta.get("progress", 10),
        )
    elif result.state == "SUCCESS":
        data = result.result or {}
        return BreakoutStatusResponse(
            job_id=job_id,
            status="SUCCESS",
            video_url=data.get("video_url"),
            progress=100,
        )
    elif result.state == "FAILURE":
        return BreakoutStatusResponse(
            job_id=job_id,
            status="FAILURE",
            error=str(result.info) if result.info else "Unknown error",
        )
    else:
        return BreakoutStatusResponse(
            job_id=job_id,
            status=result.state,
            progress=5,
        )
