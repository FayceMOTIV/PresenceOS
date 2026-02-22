"""add video_credits table

Revision ID: g4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-02-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "g4b5c6d7e8f9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "video_credits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False, server_default="trial"),
        sa.Column("credits_remaining", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("credits_total", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("reset_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_video_credits_brand_id", "video_credits", ["brand_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_video_credits_brand_id", table_name="video_credits")
    op.drop_table("video_credits")
