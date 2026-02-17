"""
PresenceOS - Authentication Endpoints
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from slowapi.util import get_remote_address
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DBSession, CurrentUser
from app.middleware.rate_limit import limiter
import logging
import secrets

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    generate_refresh_token,
    hash_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

logger = logging.getLogger(__name__)
from app.core.config import settings
from app.models.user import User, Workspace, WorkspaceMember, UserRole, RefreshToken, PasswordResetToken
from app.schemas.user import Token, TokenRefresh, UserResponse, WorkspaceResponse

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    workspace_name: str | None = None


class LoginResponse(BaseModel):
    user: UserResponse
    token: Token
    workspaces: list[WorkspaceResponse]


async def create_tokens_for_user(
    user: User,
    db: AsyncSession,
    request: Request | None = None,
) -> Token:
    """Create access and refresh tokens for a user."""
    # Create access token (short-lived)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Create refresh token (long-lived, stored in DB)
    raw_refresh_token = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh_token)
    family_id = uuid.uuid4()

    refresh_token_db = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        family_id=family_id,
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=get_remote_address(request) if request else None,
    )
    db.add(refresh_token_db)
    await db.flush()

    return Token(
        access_token=access_token,
        refresh_token=raw_refresh_token,
    )


@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, db: DBSession):
    """Register a new user and optionally create their first workspace."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    workspaces = []

    # Create default workspace if name provided
    if data.workspace_name:
        workspace = Workspace(
            name=data.workspace_name,
            slug=data.workspace_name.lower().replace(" ", "-"),
        )
        db.add(workspace)
        await db.flush()

        # Add user as owner
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role=UserRole.OWNER,
        )
        db.add(member)
        workspaces.append(workspace)

    # Generate tokens
    token = await create_tokens_for_user(user, db, request)

    await db.commit()
    await db.refresh(user)

    return LoginResponse(
        user=UserResponse.model_validate(user),
        token=token,
        workspaces=[WorkspaceResponse.model_validate(w) for w in workspaces],
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
):
    """Login with email and password."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Get user's workspaces
    memberships_result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.workspace))
        .where(WorkspaceMember.user_id == user.id)
    )
    memberships = memberships_result.scalars().all()
    workspaces = [m.workspace for m in memberships]

    # Generate tokens
    token = await create_tokens_for_user(user, db, request)

    await db.commit()

    return LoginResponse(
        user=UserResponse.model_validate(user),
        token=token,
        workspaces=[WorkspaceResponse.model_validate(w) for w in workspaces],
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh_token(request: Request, data: TokenRefresh, db: DBSession):
    """
    Refresh access token using a valid refresh token.
    Implements token rotation: old refresh token is revoked, new one is issued.
    """
    token_hash = hash_refresh_token(data.refresh_token)

    # Find the refresh token in DB
    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(RefreshToken.token_hash == token_hash)
    )
    refresh_token_db = result.scalar_one_or_none()

    if not refresh_token_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if token is revoked
    if refresh_token_db.is_revoked:
        # Potential token reuse attack - revoke all tokens in this family
        await db.execute(
            delete(RefreshToken).where(
                RefreshToken.family_id == refresh_token_db.family_id
            )
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked. Please login again.",
        )

    # Check if token is expired
    if refresh_token_db.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please login again.",
        )

    # Check if user is still active
    user = refresh_token_db.user
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Revoke the old refresh token
    refresh_token_db.is_revoked = True

    # Create new access token
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Create new refresh token (rotation) - same family
    raw_new_refresh = generate_refresh_token()
    new_token_hash = hash_refresh_token(raw_new_refresh)

    new_refresh_token_db = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        family_id=refresh_token_db.family_id,  # Same family for tracking
        user_agent=request.headers.get("user-agent"),
        ip_address=get_remote_address(request),
    )
    db.add(new_refresh_token_db)

    await db.commit()

    return Token(
        access_token=access_token,
        refresh_token=raw_new_refresh,
    )


@router.post("/logout")
async def logout(current_user: CurrentUser, data: TokenRefresh, db: DBSession):
    """Logout by revoking the refresh token."""
    token_hash = hash_refresh_token(data.refresh_token)

    # Revoke the refresh token
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user.id,
        )
    )
    refresh_token_db = result.scalar_one_or_none()

    if refresh_token_db:
        refresh_token_db.is_revoked = True
        await db.commit()

    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all_devices(current_user: CurrentUser, db: DBSession):
    """Logout from all devices by revoking all refresh tokens."""
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == current_user.id)
    )
    await db.commit()

    return {"message": "Successfully logged out from all devices"}


# Password reset token expiry (1 hour)
PASSWORD_RESET_EXPIRE_MINUTES = 60


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Hash the reset token for storage."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: DBSession):
    """
    Request a password reset link.

    In development, the reset link is logged to the console.
    In production, an email would be sent to the user.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    success_message = {
        "message": "If an account exists with this email, a reset link has been sent."
    }

    if not user:
        return success_message

    if not user.is_active:
        return success_message

    # Invalidate any existing reset tokens for this user
    await db.execute(
        delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )

    # Generate new reset token
    raw_token = generate_reset_token()
    token_hash = hash_reset_token(raw_token)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES),
    )
    db.add(reset_token)
    await db.commit()

    # Build reset URL
    frontend_url = settings.frontend_url or "http://localhost:3001"
    reset_url = f"{frontend_url}/auth/reset-password?token={raw_token}"

    # DEV: Log the reset link to console (no email service configured)
    logger.info("=" * 60)
    logger.info("PASSWORD RESET REQUEST")
    logger.info(f"Email: {user.email}")
    logger.info(f"Token: {raw_token}")
    logger.info(f"Reset URL: {reset_url}")
    logger.info(f"Expires: {reset_token.expires_at}")
    logger.info("=" * 60)

    # Also print to stdout for visibility in dev
    print("\n" + "=" * 60)
    print("PASSWORD RESET REQUEST")
    print(f"Email: {user.email}")
    print(f"Token: {raw_token}")
    print(f"Reset URL: {reset_url}")
    print(f"Expires: {reset_token.expires_at}")
    print("=" * 60 + "\n")

    return success_message


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: ResetPasswordRequest, db: DBSession):
    """
    Reset password using a valid reset token.
    """
    # Validate password strength
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Find the reset token
    token_hash = hash_reset_token(data.token)
    result = await db.execute(
        select(PasswordResetToken)
        .options(selectinload(PasswordResetToken.user))
        .where(PasswordResetToken.token_hash == token_hash)
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if token is already used
    if reset_token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used",
        )

    # Check if token is expired
    if reset_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one.",
        )

    # Update the user's password
    user = reset_token.user
    user.hashed_password = get_password_hash(data.new_password)

    # Mark token as used
    reset_token.is_used = True

    # Revoke all existing refresh tokens for security
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user.id)
    )

    await db.commit()

    logger.info(f"Password reset successful for user: {user.email}")

    return {"message": "Password reset successful. You can now login with your new password."}
