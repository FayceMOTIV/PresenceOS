"""add video_assets table

Revision ID: v2_003_video_assets
Revises: v2_002_onboarding
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v2_003_video_assets"
down_revision = "v2_002_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'video_assets'"
        )
    )
    if result.fetchone() is not None:
        return

    op.create_table(
        "video_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("public_url", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("aspect_ratio", sa.String(10), nullable=False, server_default="9:16"),
        sa.Column("style", sa.String(30), nullable=False, server_default="cinematic"),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("fal_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="saved"),
        sa.Column("platform", sa.String(30), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("post_id", sa.String(255), nullable=True),
        sa.Column("post_url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("publish_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_video_assets_brand_id", "video_assets", ["brand_id"])
    op.create_index("ix_video_assets_status", "video_assets", ["status"])


def downgrade() -> None:
    op.drop_index("ix_video_assets_status")
    op.drop_index("ix_video_assets_brand_id")
    op.drop_table("video_assets")
