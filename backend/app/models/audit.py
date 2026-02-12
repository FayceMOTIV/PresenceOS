"""
PresenceOS - Audit Log Model
"""
import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuditAction(str, enum.Enum):
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_REGISTER = "user.register"
    USER_UPDATE = "user.update"

    # Workspace actions
    WORKSPACE_CREATE = "workspace.create"
    WORKSPACE_UPDATE = "workspace.update"
    WORKSPACE_DELETE = "workspace.delete"
    WORKSPACE_MEMBER_ADD = "workspace.member.add"
    WORKSPACE_MEMBER_REMOVE = "workspace.member.remove"

    # Brand actions
    BRAND_CREATE = "brand.create"
    BRAND_UPDATE = "brand.update"
    BRAND_DELETE = "brand.delete"
    BRAND_VOICE_UPDATE = "brand.voice.update"

    # Knowledge actions
    KNOWLEDGE_CREATE = "knowledge.create"
    KNOWLEDGE_UPDATE = "knowledge.update"
    KNOWLEDGE_DELETE = "knowledge.delete"
    KNOWLEDGE_IMPORT = "knowledge.import"

    # Content actions
    IDEA_CREATE = "idea.create"
    IDEA_UPDATE = "idea.update"
    IDEA_DELETE = "idea.delete"
    DRAFT_CREATE = "draft.create"
    DRAFT_UPDATE = "draft.update"
    DRAFT_DELETE = "draft.delete"

    # Publishing actions
    CONNECTOR_CONNECT = "connector.connect"
    CONNECTOR_DISCONNECT = "connector.disconnect"
    CONNECTOR_REFRESH = "connector.refresh"
    POST_SCHEDULE = "post.schedule"
    POST_PUBLISH = "post.publish"
    POST_CANCEL = "post.cancel"
    POST_FAIL = "post.fail"

    # AI actions
    AI_GENERATE = "ai.generate"
    AI_ANALYZE = "ai.analyze"


class AuditLog(BaseModel):
    """Audit log for tracking user and system actions."""

    __tablename__ = "audit_logs"

    # Actor
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Action
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)

    # Target resource
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Details
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Example: {"old_value": {...}, "new_value": {...}}

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id}>"
