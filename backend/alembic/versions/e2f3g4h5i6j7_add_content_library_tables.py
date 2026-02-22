"""Add content library tables (dishes, ai_proposals, daily_briefs, compiled_kbs) + extend media_assets

Revision ID: e2f3g4h5i6j7
Revises: d1a2b3c4d5e6
Create Date: 2026-02-19 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e2f3g4h5i6j7"
down_revision: Union[str, None] = "d1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── dishes ──────────────────────────────────────────────────────────
    op.create_table(
        "dishes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(20), nullable=False, server_default="plats"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("cover_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_post_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cover_asset_id"], ["media_assets.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_dishes_brand_id", "dishes", ["brand_id"])

    # ── ai_proposals ────────────────────────────────────────────────────
    op.create_table(
        "ai_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("proposal_type", sa.String(20), nullable=False, server_default="post"),
        sa.Column("platform", sa.String(50), nullable=False, server_default="instagram"),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("hashtags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("improved_image_url", sa.Text(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="request"),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("kb_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ai_proposals_brand_id", "ai_proposals", ["brand_id"])
    op.create_index("ix_ai_proposals_status", "ai_proposals", ["status"])

    # ── daily_briefs ────────────────────────────────────────────────────
    op.create_table(
        "daily_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_proposal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notif_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generated_proposal_id"], ["ai_proposals.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("brand_id", "date", name="uq_daily_brief_brand_date"),
    )
    op.create_index("ix_daily_briefs_brand_id", "daily_briefs", ["brand_id"])

    # ── compiled_kbs ────────────────────────────────────────────────────
    op.create_table(
        "compiled_kbs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kb_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("identity", postgresql.JSONB(), nullable=True),
        sa.Column("menu", postgresql.JSONB(), nullable=True),
        sa.Column("media", postgresql.JSONB(), nullable=True),
        sa.Column("today", postgresql.JSONB(), nullable=True),
        sa.Column("posting_history", postgresql.JSONB(), nullable=True),
        sa.Column("performance", postgresql.JSONB(), nullable=True),
        sa.Column("completeness_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("compiled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("brand_id", name="uq_compiled_kb_brand"),
    )
    op.create_index("ix_compiled_kbs_brand_id", "compiled_kbs", ["brand_id"])

    # ── Extend media_assets with content library fields ─────────────────
    op.add_column("media_assets", sa.Column("improved_url", sa.Text(), nullable=True))
    op.add_column("media_assets", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column(
        "media_assets",
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="ready"),
    )
    op.add_column(
        "media_assets",
        sa.Column("linked_dish_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("media_assets", sa.Column("asset_label", sa.String(255), nullable=True))
    op.add_column("media_assets", sa.Column("error_message", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_media_assets_linked_dish_id",
        "media_assets",
        "dishes",
        ["linked_dish_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # ── Remove media_assets extensions ──────────────────────────────────
    op.drop_constraint("fk_media_assets_linked_dish_id", "media_assets", type_="foreignkey")
    op.drop_column("media_assets", "error_message")
    op.drop_column("media_assets", "asset_label")
    op.drop_column("media_assets", "linked_dish_id")
    op.drop_column("media_assets", "processing_status")
    op.drop_column("media_assets", "quality_score")
    op.drop_column("media_assets", "improved_url")

    # ── Drop tables in reverse order ────────────────────────────────────
    op.drop_index("ix_compiled_kbs_brand_id", table_name="compiled_kbs")
    op.drop_table("compiled_kbs")

    op.drop_index("ix_daily_briefs_brand_id", table_name="daily_briefs")
    op.drop_table("daily_briefs")

    op.drop_index("ix_ai_proposals_status", table_name="ai_proposals")
    op.drop_index("ix_ai_proposals_brand_id", table_name="ai_proposals")
    op.drop_table("ai_proposals")

    op.drop_index("ix_dishes_brand_id", table_name="dishes")
    op.drop_table("dishes")
