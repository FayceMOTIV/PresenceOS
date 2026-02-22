"""
PresenceOS - Dish Model (Content Library)

Individual menu items for a brand's restaurant/business.
Used by the Knowledge Base for AI-powered content generation.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DishCategory(str, enum.Enum):
    ENTREES = "entrees"
    PLATS = "plats"
    DESSERTS = "desserts"
    BOISSONS = "boissons"
    AUTRES = "autres"


class Dish(BaseModel):
    """A menu item belonging to a brand."""

    __tablename__ = "dishes"

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DishCategory.PLATS.value
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Link to cover photo
    cover_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("media_assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # AI content tracking — rotation to avoid repeating the same dishes
    ai_post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Ordering
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", backref="dishes")
    cover_asset: Mapped["MediaAsset | None"] = relationship(
        "MediaAsset", foreign_keys=[cover_asset_id]
    )

    def __repr__(self) -> str:
        return f"<Dish {self.name} ({self.category}) brand={self.brand_id}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.media import MediaAsset
