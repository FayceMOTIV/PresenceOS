"""
PresenceOS - Content Library API

Endpoints for managing dishes (menu items) and generating content from free-text requests.
"""
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.services.content_library import ContentLibraryService

logger = structlog.get_logger()
router = APIRouter()


# ── Request/Response Models ──────────────────────────────────────────────


class DishCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="plats")
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    is_featured: bool = False
    cover_asset_id: str | None = None


class DishUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    category: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    is_available: bool | None = None
    is_featured: bool | None = None
    cover_asset_id: str | None = None
    display_order: int | None = None


class DishResponse(BaseModel):
    id: str
    brand_id: str
    name: str
    category: str
    description: str | None
    price: float | None
    is_available: bool
    is_featured: bool
    cover_asset_id: str | None
    ai_post_count: int
    last_posted_at: str | None
    display_order: int
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, obj) -> "DishResponse":
        return cls(
            id=str(obj.id),
            brand_id=str(obj.brand_id),
            name=obj.name,
            category=obj.category,
            description=obj.description,
            price=float(obj.price) if obj.price else None,
            is_available=obj.is_available,
            is_featured=obj.is_featured,
            cover_asset_id=str(obj.cover_asset_id) if obj.cover_asset_id else None,
            ai_post_count=obj.ai_post_count,
            last_posted_at=obj.last_posted_at.isoformat() if obj.last_posted_at else None,
            display_order=obj.display_order,
            created_at=obj.created_at.isoformat(),
            updated_at=obj.updated_at.isoformat(),
        )


class ContentRequestBody(BaseModel):
    text: str = Field(..., min_length=5, max_length=2000)
    content_type: str = Field(default="post")
    platform: str = Field(default="instagram")


class ProposalBriefResponse(BaseModel):
    id: str
    status: str
    source: str

    @classmethod
    def from_orm(cls, obj) -> "ProposalBriefResponse":
        return cls(
            id=str(obj.id),
            status=obj.status,
            source=obj.source,
        )


# ── Endpoints ────────────────────────────────────────────────────────────


@router.post("/{brand_id}/dishes", status_code=status.HTTP_201_CREATED)
async def create_dish(
    brand_id: UUID,
    body: DishCreateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> DishResponse:
    """Create a new dish for a brand."""
    await get_brand(brand_id, current_user, db)

    service = ContentLibraryService(db)
    dish = await service.create_dish(
        brand_id=str(brand_id),
        name=body.name,
        category=body.category,
        description=body.description,
        price=body.price,
        is_featured=body.is_featured,
        cover_asset_id=body.cover_asset_id,
    )
    return DishResponse.from_orm(dish)


@router.get("/{brand_id}/dishes")
async def list_dishes(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
    category: str | None = None,
    featured: bool = False,
    available: bool = True,
) -> dict:
    """List dishes for a brand with optional filters."""
    await get_brand(brand_id, current_user, db)

    service = ContentLibraryService(db)
    dishes = await service.list_dishes(
        brand_id=str(brand_id),
        category=category,
        featured_only=featured,
        available_only=available,
    )
    return {
        "dishes": [DishResponse.from_orm(d) for d in dishes],
        "total": len(dishes),
    }


@router.put("/{brand_id}/dishes/{dish_id}")
async def update_dish(
    brand_id: UUID,
    dish_id: UUID,
    body: DishUpdateRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> DishResponse:
    """Update a dish."""
    await get_brand(brand_id, current_user, db)

    service = ContentLibraryService(db)
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    try:
        dish = await service.update_dish(str(dish_id), **updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return DishResponse.from_orm(dish)


@router.delete("/{brand_id}/dishes/{dish_id}")
async def delete_dish(
    brand_id: UUID,
    dish_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Delete a dish."""
    await get_brand(brand_id, current_user, db)

    service = ContentLibraryService(db)
    deleted = await service.delete_dish(str(dish_id))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dish not found",
        )
    return {"success": True}


class AssetProposalRequest(BaseModel):
    asset_id: str = Field(..., min_length=1)


@router.post("/{brand_id}/asset-proposal", status_code=status.HTTP_201_CREATED)
async def create_asset_proposal(
    brand_id: UUID,
    body: AssetProposalRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ProposalBriefResponse:
    """Generate a content proposal from an existing media asset."""
    await get_brand(brand_id, current_user, db)

    service = ContentLibraryService(db)
    proposal = await service.create_request_proposal(
        brand_id=str(brand_id),
        request_text=f"Crée un post Instagram à partir de l'asset {body.asset_id}",
        content_type="post",
        platform="instagram",
    )
    return ProposalBriefResponse.from_orm(proposal)


@router.post("/{brand_id}/request", status_code=status.HTTP_201_CREATED)
async def create_content_request(
    brand_id: UUID,
    body: ContentRequestBody,
    current_user: CurrentUser,
    db: DBSession,
) -> ProposalBriefResponse:
    """Create a content proposal from a free-text request."""
    await get_brand(brand_id, current_user, db)

    service = ContentLibraryService(db)
    proposal = await service.create_request_proposal(
        brand_id=str(brand_id),
        request_text=body.text,
        content_type=body.content_type,
        platform=body.platform,
    )
    return ProposalBriefResponse.from_orm(proposal)
