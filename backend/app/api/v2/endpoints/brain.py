"""
PresenceOS - Brain v2 Endpoints (Mem0 CRUD)

Direct CRUD on Mem0 conversational memory for a brand.
Convention: user_id = f"restaurant_{brand_id}"
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.services.ilyas.memory import Mem0Memory

logger = structlog.get_logger()
router = APIRouter()

# Singleton — lazy-initialized, thread-safe via Mem0Memory internals
_mem0 = Mem0Memory()


# ── Request / Response Models ──


class AddMemoryRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Memory text to store (e.g. 'Le chef deteste le poisson cru').",
    )
    metadata: dict | None = Field(
        default=None,
        description="Optional metadata tags (e.g. {'source': 'manual'}).",
    )


class MemoryItem(BaseModel):
    id: str
    memory: str
    metadata: dict | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MemoryListResponse(BaseModel):
    memories: list[MemoryItem]
    count: int
    user_id: str


class AddMemoryResponse(BaseModel):
    success: bool
    user_id: str
    result: dict | None = None


class DeleteMemoryResponse(BaseModel):
    success: bool
    memory_id: str


# ── Helpers ──


def _format_memory(raw: dict) -> MemoryItem:
    """Normalize a raw Mem0 memory dict into our response model."""
    return MemoryItem(
        id=raw.get("id", ""),
        memory=raw.get("memory", raw.get("text", "")),
        metadata=raw.get("metadata"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
    )


# ── Endpoints ──


@router.get("/{brand_id}/memories")
@limiter.limit("30/minute")
async def list_memories(
    request: Request,
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
) -> MemoryListResponse:
    """List all Mem0 memories for a brand."""
    await verify_brand_access(str(brand_id), current_user, db)
    user_id = f"restaurant_{brand_id}"

    try:
        raw_memories = await _mem0.get_all(user_id=user_id)
        memories = [_format_memory(m) for m in raw_memories]
    except Exception as exc:
        logger.error("Mem0 list failed", brand_id=str(brand_id), error=str(exc))
        # Graceful degradation: return empty list, never crash
        memories = []

    return MemoryListResponse(
        memories=memories,
        count=len(memories),
        user_id=user_id,
    )


@router.post("/{brand_id}/memories", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def add_memory(
    request: Request,
    brand_id: UUID,
    body: AddMemoryRequest,
    current_user: FirebaseUser,
    db: DBSession,
) -> AddMemoryResponse:
    """Add a manual memory for a brand."""
    await verify_brand_access(str(brand_id), current_user, db)
    user_id = f"restaurant_{brand_id}"

    try:
        result = await _mem0.add(
            messages=[{"role": "user", "content": body.content}],
            user_id=user_id,
            metadata={
                "source": "manual",
                "brand_id": str(brand_id),
                "added_by": str(current_user.id),
                **(body.metadata or {}),
            },
        )
        logger.info("Mem0 memory added", brand_id=str(brand_id), user_id=user_id)
        return AddMemoryResponse(success=True, user_id=user_id, result=result)
    except Exception as exc:
        logger.error("Mem0 add failed", brand_id=str(brand_id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store memory. Please try again.",
        )


@router.delete("/{brand_id}/memories/{memory_id}")
@limiter.limit("20/minute")
async def delete_memory(
    request: Request,
    brand_id: UUID,
    memory_id: str,
    current_user: FirebaseUser,
    db: DBSession,
) -> DeleteMemoryResponse:
    """Delete a specific Mem0 memory."""
    await verify_brand_access(str(brand_id), current_user, db)

    try:
        await _mem0.delete(memory_id=memory_id)
        logger.info(
            "Mem0 memory deleted",
            brand_id=str(brand_id),
            memory_id=memory_id,
        )
        return DeleteMemoryResponse(success=True, memory_id=memory_id)
    except Exception as exc:
        logger.error(
            "Mem0 delete failed",
            brand_id=str(brand_id),
            memory_id=memory_id,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory. Please try again.",
        )
