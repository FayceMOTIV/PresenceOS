"""add source column to cm_sessions

Revision ID: v2_001_source
Revises: k8l9m0n1o2p3
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = "v2_001_source"
down_revision = "k8l9m0n1o2p3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent: check if column exists before adding
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'cm_sessions' AND column_name = 'source'"
        )
    )
    if result.fetchone() is None:
        op.add_column(
            "cm_sessions",
            sa.Column("source", sa.String(20), nullable=False, server_default="cm_chat"),
        )


def downgrade() -> None:
    op.drop_column("cm_sessions", "source")
