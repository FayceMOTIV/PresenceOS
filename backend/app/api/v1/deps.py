"""
PresenceOS - API Dependencies

Includes resilient dependency injection:
- get_optional_db: yields None if DB is unavailable (never crashes)
- CurrentUser / DBSession: standard auth+DB dependencies
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
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
    except HTTPException:
        raise  # let HTTP errors propagate untouched
    except Exception as e:
        logger.warning(f"DB unavailable during request: {e}")
        yield None


OptionalDBSession = Annotated[Optional[AsyncSession], Depends(get_optional_db)]


# ── Auth Dependencies (unchanged) ───────────────────────────────

class _DevMockUser:
    """Lightweight mock that quacks like User for dev/degraded mode (no DB).
    We cannot instantiate the real SQLAlchemy User without a Session, so we
    use a plain object with the same attributes the upload endpoint needs.
    """
    def __init__(self):
        self.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        self.email = "dev@presenceos.local"
        self.full_name = "Dev User"
        self.is_active = True
        self.is_verified = True
        self.avatar_url = None
        self.hashed_password = None
        self.oauth_provider = None
        self.oauth_provider_id = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return "<DevMockUser dev@presenceos.local>"


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Optional[AsyncSession], Depends(get_optional_db)],
) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials

    # ── Dev bypass: skip JWT validation in development ONLY ──
    if (
        token == "dev-token-presenceos"
        and settings.app_env == "development"
        and not settings.is_production
    ):
        logger.debug("Dev token bypass — development mode only")
        # If DB is unavailable (degraded mode), return a mock user
        if db is None:
            logger.info("Dev bypass in degraded mode — returning mock user")
            return _DevMockUser()
        # Otherwise query for a real user
        result = await db.execute(
            select(User).where(User.is_active.is_(True)).limit(1)
        )
        user = result.scalar_one_or_none()
        if user:
            return user
        # No user in DB — raise a clear error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dev bypass: no active user in database. Create one via /auth/register first.",
        )

    # Normal JWT flow requires DB
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    # ── 1. Try JWT first (v1 native) ──
    user_id = verify_token(token)

    if user_id:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user

    # ── 2. Fallback: try Firebase ID token (mobile app sends these) ──
    try:
        from app.core.firebase_auth import verify_firebase_token, TokenExpiredError

        try:
            decoded = verify_firebase_token(token)
        except TokenExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firebase token expired",
                headers={"WWW-Authenticate": "Bearer", "X-Token-Expired": "true"},
            )

        if decoded:
            firebase_uid: str = decoded["uid"]
            firebase_email: str | None = decoded.get("email")

            # Lookup by Firebase UID
            result = await db.execute(
                select(User).where(
                    User.oauth_provider == "firebase",
                    User.oauth_provider_id == firebase_uid,
                )
            )
            user = result.scalar_one_or_none()
            if user and user.is_active:
                return user

            # Fallback: lookup by email and link Firebase UID
            if firebase_email:
                result = await db.execute(
                    select(User).where(User.email == firebase_email)
                )
                user = result.scalar_one_or_none()
                if user and user.is_active:
                    user.oauth_provider = "firebase"
                    user.oauth_provider_id = firebase_uid
                    await db.commit()
                    await db.refresh(user)
                    logger.info(
                        "V1 fallback: linked user to Firebase",
                        extra={"user_id": str(user.id), "firebase_uid": firebase_uid},
                    )
                    return user

            # Auto-create new user from Firebase
            if decoded:
                display_name = decoded.get("name") or firebase_email or "Utilisateur"
                new_user = User(
                    email=firebase_email or f"{firebase_uid}@firebase.local",
                    full_name=display_name,
                    hashed_password="",
                    is_active=True,
                    is_verified=True,
                    oauth_provider="firebase",
                    oauth_provider_id=firebase_uid,
                )
                db.add(new_user)
                await db.commit()
                await db.refresh(new_user)
                logger.info(
                    "V1 fallback: created user from Firebase",
                    extra={"user_id": str(new_user.id), "firebase_uid": firebase_uid},
                )
                return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Firebase fallback failed: %s", e)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


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
