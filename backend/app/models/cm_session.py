"""
PresenceOS - CM Chat Session & Message Models

Conversational Community Manager AI — iMessage-style chat sessions
where the restaurateur can discuss strategy, request content, etc.
"""
import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class CmSession(BaseModel):
    """A CM Chat conversation session tied to a brand."""

    __tablename__ = "cm_sessions"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Nouvelle conversation"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SessionStatus.ACTIVE.value
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="cm_chat", server_default="cm_chat"
    )

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="cm_sessions")
    messages: Mapped[list["CmMessage"]] = relationship(
        "CmMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CmMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<CmSession {self.title} brand={self.brand_id}>"


class CmMessage(BaseModel):
    """A single message within a CM Chat session."""

    __tablename__ = "cm_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cm_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional structured proposals embedded in assistant messages
    proposals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Token usage tracking
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    session: Mapped["CmSession"] = relationship("CmSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<CmMessage {self.role} session={self.session_id}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
