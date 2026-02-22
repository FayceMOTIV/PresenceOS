"""
PresenceOS - Knowledge Base API

Endpoints for reading, rebuilding, and checking completeness of
the compiled Knowledge Base.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.services.knowledge_base_service import KnowledgeBaseService

logger = structlog.get_logger()
router = APIRouter()


# ── Response Models ──────────────────────────────────────────────────────


class KBResponse(BaseModel):
    brand_id: str
    kb_version: int
    identity: dict | None
    menu: dict | None
    media: dict | None
    today: dict | None
    posting_history: dict | None
    performance: dict | None
    completeness_score: int
    compiled_at: str | None

    @classmethod
    def from_orm(cls, obj) -> "KBResponse":
        return cls(
            brand_id=str(obj.brand_id),
            kb_version=obj.kb_version,
            identity=obj.identity,
            menu=obj.menu,
            media=obj.media,
            today=obj.today,
            posting_history=obj.posting_history,
            performance=obj.performance,
            completeness_score=obj.completeness_score,
            compiled_at=obj.compiled_at.isoformat() if obj.compiled_at else None,
        )


class CompletenessResponse(BaseModel):
    brand_id: str
    score: int


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/{brand_id}")
async def get_kb(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> KBResponse | dict:
    """Read the compiled Knowledge Base for a brand."""
    await get_brand(brand_id, current_user, db)

    service = KnowledgeBaseService(db)
    kb = await service.get_kb(str(brand_id))

    if not kb:
        return {
            "brand_id": str(brand_id),
            "kb_version": 0,
            "completeness_score": 0,
            "compiled_at": None,
            "message": "Knowledge Base not yet compiled. Add dishes and assets, then rebuild.",
        }

    return KBResponse.from_orm(kb)


@router.post("/{brand_id}/rebuild")
async def rebuild_kb(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> KBResponse:
    """Force rebuild the Knowledge Base for a brand."""
    await get_brand(brand_id, current_user, db)

    service = KnowledgeBaseService(db)
    try:
        kb = await service.rebuild(str(brand_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("KB rebuild failed", brand_id=str(brand_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KB rebuild failed: {str(e)}",
        )

    logger.info("KB rebuilt via API", brand_id=str(brand_id), version=kb.kb_version)
    return KBResponse.from_orm(kb)


@router.get("/{brand_id}/completeness")
async def get_completeness(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> CompletenessResponse:
    """Get the completeness score for a brand's Knowledge Base."""
    await get_brand(brand_id, current_user, db)

    service = KnowledgeBaseService(db)
    try:
        score = await service.calculate_completeness(str(brand_id))
    except Exception as e:
        logger.error("KB completeness calculation failed", brand_id=str(brand_id), error=str(e))
        score = 0

    return CompletenessResponse(brand_id=str(brand_id), score=score)
