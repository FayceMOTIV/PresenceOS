"""
PresenceOS - Me v2 Endpoints

Current user info + brands from PostgreSQL.
Bridges Firebase Auth with PostgreSQL brand management.
"""
import re
import uuid as uuid_mod

import structlog
from fastapi import APIRouter, Request
from pydantic import BaseModel

from sqlalchemy import select

from app.api.v2.deps import FirebaseUser, DBSession
from app.middleware.rate_limit import limiter
from app.models.user import Workspace, WorkspaceMember, UserRole
from app.models.brand import Brand, BrandType

logger = structlog.get_logger()
router = APIRouter()


class BrandResponse(BaseModel):
    id: str
    name: str
    slug: str
    brand_type: str
    description: str | None = None
    logo_url: str | None = None
    niche: str | None = None


class MeBrandsResponse(BaseModel):
    brands: list[BrandResponse]


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "mon-restaurant"


@router.get("/brands")
@limiter.limit("60/minute")
async def my_brands(
    request: Request,
    current_user: FirebaseUser,
    db: DBSession,
) -> MeBrandsResponse:
    """Get current user's brands from PostgreSQL.

    Auto-creates a workspace + brand if the user has none.
    This is the single source of truth for brand IDs used in all API calls.
    """
    # Find brands via workspace membership
    result = await db.execute(
        select(Brand)
        .join(Workspace, Workspace.id == Brand.workspace_id)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == current_user.id,
            Brand.is_active.is_(True),
        )
    )
    brands = list(result.scalars().all())

    # Auto-create workspace + brand for new users
    if not brands:
        display_name = current_user.full_name or "Mon Restaurant"
        slug = _slugify(display_name) + "-" + str(uuid_mod.uuid4())[:8]

        workspace = Workspace(
            name=f"{display_name}",
            slug=slug,
            timezone="Europe/Paris",
            default_language="fr",
        )
        db.add(workspace)
        await db.flush()

        membership = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role=UserRole.OWNER,
        )
        db.add(membership)

        brand = Brand(
            workspace_id=workspace.id,
            name=display_name,
            slug=slug,
            brand_type=BrandType.RESTAURANT,
            niche="restaurant",
            is_active=True,
        )
        db.add(brand)
        await db.commit()
        await db.refresh(brand)

        brands = [brand]
        logger.info(
            "Auto-created workspace + brand for new user",
            extra={
                "user_id": str(current_user.id),
                "brand_id": str(brand.id),
            },
        )

    return MeBrandsResponse(
        brands=[
            BrandResponse(
                id=str(b.id),
                name=b.name,
                slug=b.slug,
                brand_type=b.brand_type.value if hasattr(b.brand_type, 'value') else str(b.brand_type),
                description=b.description,
                logo_url=b.logo_url,
                niche=b.niche,
            )
            for b in brands
        ]
    )
