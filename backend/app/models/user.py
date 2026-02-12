"""
PresenceOS - User & Workspace Models
"""
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.brand import Brand


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class User(BaseModel):
    """User account."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OAuth provider info (for social login)
    oauth_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    oauth_provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Workspace(BaseModel):
    """Workspace (organization) that contains brands."""

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Settings
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    default_language: Mapped[str] = mapped_column(
        String(10), default="fr", nullable=False
    )

    # Billing (placeholder)
    billing_plan: Mapped[str] = mapped_column(
        String(50), default="free", nullable=False
    )
    billing_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    members: Mapped[list["WorkspaceMember"]] = relationship(
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )
    brands: Mapped[list["Brand"]] = relationship(
        "Brand", back_populates="workspace", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Workspace {self.slug}>"


class WorkspaceMember(BaseModel):
    """Many-to-many relationship between users and workspaces with role."""

    __tablename__ = "workspace_members"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.MEMBER, nullable=False
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="members"
    )
    user: Mapped["User"] = relationship("User", back_populates="workspace_memberships")

    def __repr__(self) -> str:
        return f"<WorkspaceMember {self.user_id} in {self.workspace_id}>"


class RefreshToken(BaseModel):
    """Refresh token for JWT rotation."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # For token family tracking (detect reuse attacks)
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Device info for audit
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<RefreshToken user={self.user_id} revoked={self.is_revoked}>"


class PasswordResetToken(BaseModel):
    """Token for password reset requests."""

    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<PasswordResetToken user={self.user_id} used={self.is_used}>"
