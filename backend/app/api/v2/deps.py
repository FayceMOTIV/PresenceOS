"""
PresenceOS - API v2 Dependencies

Firebase Auth for v2 endpoints.
v1 JWT auth stays untouched — this module replaces CurrentUser with FirebaseUser.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.firebase_auth import verify_firebase_token
from app.models.user import User, WorkspaceMember
from app.models.brand import Brand

# Re-export unchanged deps from v1 for convenience
from app.api.v1.deps import (
    get_optional_db,
    OptionalDBSession,
    get_brand,
)

logger = logging.getLogger(__name__)

security = HTTPBearer()


class _DevMockUser:
    """Lightweight mock for dev/degraded mode (same as v1)."""

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


async def get_firebase_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Optional[AsyncSession], Depends(get_optional_db)],
) -> User:
    """Authenticate via Firebase ID token (v2 endpoints).

    Flow:
    1. Dev bypass (same as v1) for development mode.
    2. Verify Firebase ID token.
    3. Lookup user by oauth_provider="firebase" + oauth_provider_id=firebase_uid.
    4. If not found, try matching by email (migration from JWT → Firebase).
    5. If still not found, create a new user.
    """
    token = credentials.credentials

    # ── Dev bypass: identical to v1 ──
    if (
        token == "dev-token-presenceos"
        and settings.app_env == "development"
        and not settings.is_production
    ):
        if db is None:
            return _DevMockUser()
        result = await db.execute(
            select(User).where(User.is_active.is_(True)).limit(1)
        )
        user = result.scalar_one_or_none()
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dev bypass: no active user in database.",
        )

    # ── Firebase ID token verification ──
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    decoded = verify_firebase_token(token)
    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    firebase_uid: str = decoded["uid"]
    firebase_email: str | None = decoded.get("email")

    # 1. Lookup by Firebase UID
    result = await db.execute(
        select(User).where(
            User.oauth_provider == "firebase",
            User.oauth_provider_id == firebase_uid,
        )
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    # 2. Migration: lookup by email and link Firebase UID
    if firebase_email:
        result = await db.execute(
            select(User).where(User.email == firebase_email)
        )
        user = result.scalar_one_or_none()
        if user:
            user.oauth_provider = "firebase"
            user.oauth_provider_id = firebase_uid
            await db.commit()
            await db.refresh(user)
            logger.info(
                "Linked existing user to Firebase",
                extra={"user_id": str(user.id), "firebase_uid": firebase_uid},
            )
            return user

    # 3. Auto-create new user
    display_name = decoded.get("name") or firebase_email or "Utilisateur"
    new_user = User(
        email=firebase_email or f"{firebase_uid}@firebase.local",
        full_name=display_name,
        hashed_password="",  # Firebase handles auth — no local password
        is_active=True,
        is_verified=True,
        oauth_provider="firebase",
        oauth_provider_id=firebase_uid,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logger.info(
        "Created new user from Firebase",
        extra={"user_id": str(new_user.id), "firebase_uid": firebase_uid},
    )
    return new_user


# Type aliases
FirebaseUser = Annotated[User, Depends(get_firebase_user)]
DBSession = Annotated[AsyncSession, Depends(get_db)]

__all__ = [
    "FirebaseUser",
    "DBSession",
    "get_brand",
    "get_optional_db",
    "OptionalDBSession",
]
