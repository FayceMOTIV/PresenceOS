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
    BrandOnboardingRequest,
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


@router.post("/{brand_id}/onboard", response_model=BrandResponse)
async def onboard_brand(
    brand_id: UUID,
    data: BrandOnboardingRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Simplified onboarding endpoint that updates brand and voice in one call."""
    brand = await get_brand(brand_id, current_user, db)

    # Tone voice mapping
    tone_mappings = {
        "chaleureux": {
            "tone_formal": 30,
            "tone_playful": 60,
            "tone_bold": 40,
            "tone_emotional": 80,
        },
        "premium": {
            "tone_formal": 80,
            "tone_playful": 20,
            "tone_bold": 60,
            "tone_emotional": 40,
        },
        "fun": {
            "tone_formal": 10,
            "tone_playful": 90,
            "tone_bold": 70,
            "tone_emotional": 60,
        },
        "professionnel": {
            "tone_formal": 80,
            "tone_playful": 30,
            "tone_bold": 50,
            "tone_emotional": 30,
        },
        "inspirant": {
            "tone_formal": 40,
            "tone_playful": 50,
            "tone_bold": 70,
            "tone_emotional": 80,
        },
    }

    # Update brand fields
    brand.name = data.name
    brand.brand_type = data.business_type
    brand.description = f"{data.name} - {data.business_type.value}"
    if data.website_url:
        brand.website_url = data.website_url

    # Update or create brand voice
    tone_values = tone_mappings.get(data.tone_voice, tone_mappings["professionnel"])

    if not brand.voice:
        voice = BrandVoice(
            brand_id=brand.id,
            tone_formal=tone_values["tone_formal"],
            tone_playful=tone_values["tone_playful"],
            tone_bold=tone_values["tone_bold"],
            tone_emotional=tone_values["tone_emotional"],
            custom_instructions=f"Cible: {data.target_audience}",
        )
        db.add(voice)
    else:
        brand.voice.tone_formal = tone_values["tone_formal"]
        brand.voice.tone_playful = tone_values["tone_playful"]
        brand.voice.tone_bold = tone_values["tone_bold"]
        brand.voice.tone_emotional = tone_values["tone_emotional"]
        brand.voice.custom_instructions = f"Cible: {data.target_audience}"

    # Set target_persona from target_audience string
    brand.target_persona = {
        "name": data.target_audience,
        "age_range": None,
        "interests": [],
        "pain_points": [],
        "goals": [],
    }

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand.id)
    )
    brand = result.scalar_one()

    return BrandResponse.model_validate(brand)
