"""
PresenceOS - Brand Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession, get_brand, get_current_workspace
from app.models.brand import Brand, BrandVoice
from app.models.user import WorkspaceMember
from app.schemas.brand import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandVoiceUpdate,
    BrandVoiceResponse,
)

router = APIRouter()


@router.post("", response_model=BrandResponse)
async def create_brand(
    workspace_id: UUID,
    data: BrandCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Create a new brand in a workspace."""
    workspace = await get_current_workspace(workspace_id, current_user, db)

    # Check slug uniqueness within workspace
    result = await db.execute(
        select(Brand).where(
            Brand.workspace_id == workspace.id,
            Brand.slug == data.slug,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand slug already exists in this workspace",
        )

    # Extract voice data if provided
    voice_data = data.voice
    brand_data = data.model_dump(exclude={"voice"})

    brand = Brand(workspace_id=workspace.id, **brand_data)
    db.add(brand)
    await db.flush()

    # Create brand voice with defaults or provided data
    voice = BrandVoice(
        brand_id=brand.id,
        **(voice_data.model_dump() if voice_data else {}),
    )
    db.add(voice)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand.id)
    )
    brand = result.scalar_one()

    return BrandResponse.model_validate(brand)


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand_details(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get brand details."""
    brand = await get_brand(brand_id, current_user, db)
    return BrandResponse.model_validate(brand)


@router.patch("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    data: BrandUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update brand details."""
    brand = await get_brand(brand_id, current_user, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand.id)
    )
    brand = result.scalar_one()

    return BrandResponse.model_validate(brand)


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Delete a brand (soft delete by deactivating)."""
    brand = await get_brand(brand_id, current_user, db)
    brand.is_active = False
    await db.commit()

    return {"message": "Brand deactivated"}


@router.get("/{brand_id}/voice", response_model=BrandVoiceResponse)
async def get_brand_voice(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get brand voice configuration."""
    brand = await get_brand(brand_id, current_user, db)

    if not brand.voice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand voice not configured",
        )

    return BrandVoiceResponse.model_validate(brand.voice)


@router.patch("/{brand_id}/voice", response_model=BrandVoiceResponse)
async def update_brand_voice(
    brand_id: UUID,
    data: BrandVoiceUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update brand voice configuration."""
    brand = await get_brand(brand_id, current_user, db)

    if not brand.voice:
        # Create voice if it doesn't exist
        voice = BrandVoice(brand_id=brand.id, **data.model_dump(exclude_unset=True))
        db.add(voice)
    else:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(brand.voice, field, value)

    await db.commit()

    # Reload
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand.id)
    )
    brand = result.scalar_one()

    return BrandVoiceResponse.model_validate(brand.voice)
