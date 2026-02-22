"""
PresenceOS - Daily Brief Model (Content Library)

Daily brief questions sent to restaurateurs at 8am.
Their quick response feeds the Knowledge Base for that day's content generation.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BriefStatus(str, enum.Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    IGNORED = "ignored"


class DailyBrief(BaseModel):
    """A daily brief for a brand — one per brand per day."""

    __tablename__ = "daily_briefs"
    __table_args__ = (
        UniqueConstraint("brand_id", "date", name="uq_daily_brief_brand_date"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    date: Mapped[date] = mapped_column(Date, nullable=False)

    # User response
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BriefStatus.PENDING.value
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Link to generated proposal
    generated_proposal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_proposals.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Notification tracking
    notif_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="daily_briefs")
    generated_proposal: Mapped["AIProposal | None"] = relationship(
        "AIProposal", foreign_keys=[generated_proposal_id]
    )

    def __repr__(self) -> str:
        return f"<DailyBrief {self.date} status={self.status} brand={self.brand_id}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.ai_proposal import AIProposal
