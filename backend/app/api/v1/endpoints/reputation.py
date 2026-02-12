"""
PresenceOS — Reputation Manager API (Feature 3)
"""
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.reputation_manager import ReputationManagerService

logger = structlog.get_logger()
router = APIRouter()

_service: ReputationManagerService | None = None


def _get_service() -> ReputationManagerService:
    global _service
    if _service is None:
        _service = ReputationManagerService()
    return _service


class RespondRequest(BaseModel):
    response_text: str


@router.get("/reviews/{brand_id}")
async def get_reviews(
    brand_id: str,
    platform: Optional[str] = Query(default=None),
    sentiment: Optional[str] = Query(default=None),
    responded: Optional[bool] = Query(default=None),
):
    """Get reviews for a brand with optional filters."""
    service = _get_service()
    return service.get_reviews(brand_id, platform, sentiment, responded)


@router.get("/review/{review_id}")
async def get_review(review_id: str):
    """Get a single review."""
    service = _get_service()
    result = service.get_review(review_id)
    if not result:
        raise HTTPException(status_code=404, detail="Avis non trouve")
    return result


@router.post("/review/{review_id}/suggest")
async def suggest_response(review_id: str):
    """Generate an AI response suggestion for a review."""
    service = _get_service()
    result = service.suggest_response(review_id)
    if not result:
        raise HTTPException(status_code=404, detail="Avis non trouve")
    return result


@router.post("/review/{review_id}/respond")
async def respond_to_review(review_id: str, request: RespondRequest):
    """Submit a response to a review."""
    service = _get_service()
    result = service.respond_to_review(review_id, request.response_text)
    if not result:
        raise HTTPException(status_code=404, detail="Avis non trouve")
    return result


@router.get("/stats/{brand_id}")
async def get_stats(brand_id: str):
    """Get reputation statistics for a brand."""
    service = _get_service()
    return service.get_stats(brand_id)
