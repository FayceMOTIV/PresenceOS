"""
PresenceOS - Compiled Knowledge Base Model (Content Library)

Cached compilation of all brand data used for AI prompt generation.
One active KB per brand, rebuilt automatically when underlying data changes.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CompiledKB(BaseModel):
    """Compiled Knowledge Base — one active record per brand."""

    __tablename__ = "compiled_kbs"
    __table_args__ = (
        UniqueConstraint("brand_id", name="uq_compiled_kb_brand"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    kb_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Compiled sections (JSONB for flexibility)
    identity: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    menu: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    media: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    today: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    posting_history: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    performance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Quality metrics
    completeness_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compiled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="compiled_kb")

    def __repr__(self) -> str:
        return f"<CompiledKB v{self.kb_version} score={self.completeness_score}% brand={self.brand_id}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
