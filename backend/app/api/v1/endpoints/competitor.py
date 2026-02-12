"""
PresenceOS — Competitor Intelligence API (Feature 5)
"""
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.competitor_intel import CompetitorIntelService

logger = structlog.get_logger()
router = APIRouter()

_service: CompetitorIntelService | None = None


def _get_service() -> CompetitorIntelService:
    global _service
    if _service is None:
        _service = CompetitorIntelService()
    return _service


class AddCompetitorRequest(BaseModel):
    name: str
    handle: str
    platform: str = "instagram"


@router.get("/list/{brand_id}")
async def get_competitors(brand_id: str):
    """List tracked competitors for a brand."""
    service = _get_service()
    return service.get_competitors(brand_id)


@router.post("/track/{brand_id}")
async def add_competitor(brand_id: str, request: AddCompetitorRequest):
    """Add a competitor to track."""
    service = _get_service()
    return service.add_competitor(brand_id, request.name, request.handle, request.platform)


@router.delete("/untrack/{brand_id}/{competitor_id}")
async def remove_competitor(brand_id: str, competitor_id: str):
    """Stop tracking a competitor."""
    service = _get_service()
    if not service.remove_competitor(brand_id, competitor_id):
        raise HTTPException(status_code=404, detail="Concurrent non trouve")
    return {"status": "removed", "competitor_id": competitor_id}


@router.get("/benchmark/{brand_id}")
async def get_benchmark(brand_id: str):
    """Compare your brand against tracked competitors."""
    service = _get_service()
    return service.get_benchmark(brand_id)
