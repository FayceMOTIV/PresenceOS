"""add onboarding_states table

Revision ID: v2_002_onboarding
Revises: v2_001_source
Create Date: 2026-03-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "v2_002_onboarding"
down_revision = "v2_001_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name = 'onboarding_states'"
        )
    )
    if result.fetchone() is not None:
        return

    op.create_table(
        "onboarding_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_steps", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("is_complete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dna_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("raw_answers", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("scrape_status", sa.String(20), nullable=True),
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
    op.create_index("ix_onboarding_states_brand_id", "onboarding_states", ["brand_id"])


def downgrade() -> None:
    op.drop_index("ix_onboarding_states_brand_id")
    op.drop_table("onboarding_states")
