"""
PresenceOS — OnboardingState Model (Sprint B2)

Tracks onboarding progress per brand in PostgreSQL.
Replaces Firestore-only storage for reliability and joins.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class OnboardingState(BaseModel):
    __tablename__ = "onboarding_states"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    current_step: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
    )
    total_steps: Mapped[int] = mapped_column(
        Integer, default=8, nullable=False,
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )
    dna_snapshot: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )
    raw_answers: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False,
    )
    website_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )
    scrape_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
    )
