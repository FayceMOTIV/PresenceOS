"""
PresenceOS — Breakout API v2

Architecture async (pipeline 60-120s) :
  POST /{brand_id}/generate → asyncio background task → retourne job_id
  GET  /{brand_id}/status/{job_id} → poll statut (PENDING/PROCESSING/SUCCESS/FAILURE)

Uses in-process asyncio tasks instead of Celery to avoid broker dependency.
Job state is tracked in-memory (sufficient for user-initiated one-off jobs).
"""

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

# ── In-memory job store (process-local, sufficient for breakout) ─────────

_jobs: dict[str, dict] = {}


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


# ── Background runner ───────────────────────────────────────────────────


async def _run_breakout(
    job_id: str,
    brand_id: str,
    source_type: str,
    source_url: str | None,
    ai_prompt: str | None,
) -> None:
    """Run breakout pipeline as an asyncio task with progress tracking."""
    try:
        _jobs[job_id] = {"status": "PROCESSING", "progress": 5}

        from app.services.breakout.breakout_engine import BreakoutEngine

        engine = BreakoutEngine()
        result = await engine.generate(
            source_type=source_type,
            source_url=source_url,
            ai_prompt=ai_prompt,
            brand_id=brand_id,
        )

        _jobs[job_id] = {
            "status": "SUCCESS",
            "progress": 100,
            "video_url": result.get("video_url"),
        }
        logger.info("Breakout complete", extra={"job_id": job_id, "brand_id": brand_id})

    except Exception as exc:
        logger.error("Breakout failed", extra={"job_id": job_id, "error": str(exc)})
        _jobs[job_id] = {
            "status": "FAILURE",
            "progress": 0,
            "error": str(exc),
        }


# ── Endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/{brand_id}/generate",
    response_model=BreakoutGenerateResponse,
    summary="Lance la génération Breakout en tâche async",
)
@limiter.limit("5/minute")
async def generate_breakout(
    request: Request,
    brand_id: str,
    body: BreakoutGenerateRequest,
    user: FirebaseUser,
    db: DBSession,
):
    """Lance le pipeline Breakout en arrière-plan via asyncio."""
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

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "PENDING", "progress": 0}

    # Launch as asyncio background task (runs in the same event loop)
    asyncio.create_task(
        _run_breakout(job_id, brand_id, body.source_type, body.source_url, body.ai_prompt)
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

    job = _jobs.get(job_id)
    if not job:
        return BreakoutStatusResponse(job_id=job_id, status="NOT_FOUND", progress=0)

    return BreakoutStatusResponse(
        job_id=job_id,
        status=job.get("status", "PENDING"),
        progress=job.get("progress", 0),
        video_url=job.get("video_url"),
        error=job.get("error"),
    )
