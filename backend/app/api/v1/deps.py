"""
PresenceOS - API Dependencies

Includes resilient dependency injection:
- get_optional_db: yields None if DB is unavailable (never crashes)
- CurrentUser / DBSession: standard auth+DB dependencies
"""
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, Workspace, WorkspaceMember, UserRole
from app.models.brand import Brand

logger = logging.getLogger(__name__)

security = HTTPBearer()


# ── Resilient DB Dependency ──────────────────────────────────────

async def get_optional_db(request: Request):
    """
    Resilient dependency injection for database sessions.
    Returns None if the DB is unavailable instead of crashing.
    FastAPI caches this per-request (no duplicate calls).
    """
    if getattr(request.app.state, "degraded", True):
        yield None
        return
    try:
        async for session in get_db():
            yield session
            return
    except Exception as e:
        logger.warning(f"DB unavailable during request: {e}")
        yield None


OptionalDBSession = Annotated[Optional[AsyncSession], Depends(get_optional_db)]


# ── Auth Dependencies (unchanged) ───────────────────────────────

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_workspace(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Workspace:
    """Get and validate workspace access for current user."""
    result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.workspace))
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace",
        )

    return membership.workspace


async def get_workspace_admin(
    workspace_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Workspace:
    """Get workspace and verify user has admin/owner role."""
    result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.workspace))
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace",
        )

    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return membership.workspace


async def get_brand(
    brand_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Brand:
    """Get and validate brand access for current user."""
    result = await db.execute(
        select(Brand)
        .options(selectinload(Brand.voice))
        .where(Brand.id == brand_id)
    )
    brand = result.scalar_one_or_none()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found",
        )

    # Verify user has access to the brand's workspace
    membership_result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == brand.workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    if not membership_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this brand",
        )

    return brand


# Type aliases for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentWorkspace = Annotated[Workspace, Depends(get_current_workspace)]
AdminWorkspace = Annotated[Workspace, Depends(get_workspace_admin)]
CurrentBrand = Annotated[Brand, Depends(get_brand)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
