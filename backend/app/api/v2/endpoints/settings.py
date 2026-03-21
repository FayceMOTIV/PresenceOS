"""
PresenceOS - Settings v2 Endpoints (Sprint 8)

Brand settings management (timezone, language, notifications, autopilot prefs).
Endpoints:
  GET   /brands/{brand_id}/settings  — Get brand settings
  PATCH /brands/{brand_id}/settings  — Partial update brand settings
"""
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.v2.deps import FirebaseUser, DBSession, verify_brand_access
from app.middleware.rate_limit import limiter
from app.models.brand import Brand

logger = structlog.get_logger()
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────


class BrandSettingsResponse(BaseModel):
    """Brand settings response. Uses getattr for safe access to optional fields."""

    brand_id: UUID
    name: str

    # Core settings
    brand_type: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    niche: Optional[str] = None

    # AutoPilot
    autopilot_enabled: bool = False
    auto_approve_enabled: bool = False
    autopilot_config: Optional[dict] = None

    # Content
    content_pillars: Optional[dict] = None
    brand_dna: Optional[dict] = None

    # Social
    upload_post_username: Optional[str] = None

    # Notifications
    expo_push_token: Optional[str] = None

    # Geography
    locations: Optional[list[str]] = None

    # Target
    target_persona: Optional[dict] = None

    # Constraints
    constraints: Optional[dict] = None

    # Status
    is_active: bool = True

    model_config = {"from_attributes": True}


class BrandSettingsUpdate(BaseModel):
    """Partial update schema. Only provided fields are applied (exclude_none)."""

    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    website_url: Optional[str] = Field(default=None, max_length=500)
    logo_url: Optional[str] = None
    niche: Optional[str] = Field(default=None, max_length=50)

    # AutoPilot
    autopilot_enabled: Optional[bool] = None
    auto_approve_enabled: Optional[bool] = None
    autopilot_config: Optional[dict] = None

    # Content
    content_pillars: Optional[dict] = None

    # Social
    upload_post_username: Optional[str] = Field(default=None, max_length=255)

    # Notifications
    expo_push_token: Optional[str] = Field(default=None, max_length=255)

    # Geography
    locations: Optional[list[str]] = None

    # Target
    target_persona: Optional[dict] = None

    # Constraints
    constraints: Optional[dict] = None

    # Status
    is_active: Optional[bool] = None


# ── Allowed fields for setattr (whitelist) ─────────────────────────

_UPDATABLE_FIELDS = {
    "name",
    "description",
    "website_url",
    "logo_url",
    "niche",
    "autopilot_enabled",
    "auto_approve_enabled",
    "autopilot_config",
    "content_pillars",
    "upload_post_username",
    "expo_push_token",
    "locations",
    "target_persona",
    "constraints",
    "is_active",
}


# ── Helpers ────────────────────────────────────────────────────────


def _brand_to_settings(brand: Brand) -> dict:
    """Convert Brand ORM to settings response dict, using getattr for safety."""
    return {
        "brand_id": brand.id,
        "name": brand.name,
        "brand_type": getattr(brand, "brand_type", None),
        "description": getattr(brand, "description", None),
        "website_url": getattr(brand, "website_url", None),
        "logo_url": getattr(brand, "logo_url", None),
        "niche": getattr(brand, "niche", None),
        "autopilot_enabled": getattr(brand, "autopilot_enabled", False),
        "auto_approve_enabled": getattr(brand, "auto_approve_enabled", False),
        "autopilot_config": getattr(brand, "autopilot_config", None),
        "content_pillars": getattr(brand, "content_pillars", None),
        "brand_dna": getattr(brand, "brand_dna", None),
        "upload_post_username": getattr(brand, "upload_post_username", None),
        "expo_push_token": getattr(brand, "expo_push_token", None),
        "locations": getattr(brand, "locations", None),
        "target_persona": getattr(brand, "target_persona", None),
        "constraints": getattr(brand, "constraints", None),
        "is_active": getattr(brand, "is_active", True),
    }


# ── Endpoints ──────────────────────────────────────────────────────


@router.get(
    "/brands/{brand_id}/settings",
    response_model=BrandSettingsResponse,
)
@limiter.limit("60/minute")
async def get_settings(
    request: Request,
    brand_id: UUID,
    current_user: FirebaseUser,
    db: DBSession,
):
    """Get brand settings and configuration."""
    brand = await verify_brand_access(str(brand_id), current_user, db)

    return _brand_to_settings(brand)


@router.patch(
    "/brands/{brand_id}/settings",
    response_model=BrandSettingsResponse,
)
@limiter.limit("30/minute")
async def update_settings(
    request: Request,
    brand_id: UUID,
    body: BrandSettingsUpdate,
    current_user: FirebaseUser,
    db: DBSession,
):
    """Partial update of brand settings. Only provided fields are updated."""
    brand = await verify_brand_access(str(brand_id), current_user, db)

    # Get only the fields that were explicitly set (not None)
    update_data = body.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    updated_fields = []
    for field, value in update_data.items():
        # Security: only allow whitelisted fields
        if field not in _UPDATABLE_FIELDS:
            logger.warning(
                "Settings update blocked: field not updatable",
                field=field,
                brand_id=str(brand.id),
            )
            continue

        # Verify the field actually exists on the Brand model
        if not hasattr(brand, field):
            logger.warning(
                "Settings update skipped: field not on model",
                field=field,
                brand_id=str(brand.id),
            )
            continue

        setattr(brand, field, value)
        updated_fields.append(field)

    if not updated_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update",
        )

    await db.commit()
    await db.refresh(brand)

    logger.info(
        "Brand settings updated via v2",
        brand_id=str(brand.id),
        updated_fields=updated_fields,
    )

    return _brand_to_settings(brand)
