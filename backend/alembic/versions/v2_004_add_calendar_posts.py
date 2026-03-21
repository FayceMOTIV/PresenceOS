"""add calendar_posts table

Revision ID: v2_004_calendar_posts
Revises: v2_003_video_assets
Create Date: 2026-03-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v2_004_calendar_posts"
down_revision = "v2_003_video_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendar_posts')")
    )
    if result.scalar():
        return

    op.create_table(
        "calendar_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("hashtags", postgresql.ARRAY(sa.String), nullable=True),
        sa.Column("visual_description", sa.Text, nullable=True),
        sa.Column("visual_url", sa.String(500), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("cta", sa.String(200), nullable=True),
        sa.Column("scheduled_date", sa.String(10), nullable=True),
        sa.Column("scheduled_time", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, default="pending_approval", index=True),
        sa.Column("postiz_post_id", sa.String(100), nullable=True),
        sa.Column("estimated_engagement", sa.String(20), nullable=True, default="medium"),
        sa.Column("pillar", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("calendar_posts")
