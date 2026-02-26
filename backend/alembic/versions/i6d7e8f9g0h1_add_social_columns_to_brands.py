"""Add social platform columns to brands

Revision ID: i6d7e8f9g0h1
Revises: h5c6d7e8f9g0
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "i6d7e8f9g0h1"
down_revision = "h5c6d7e8f9g0"
branch_labels = None
depends_on = None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
    ), {"t": table_name, "c": column_name})
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # Social platform columns
    if not _column_exists(conn, "brands", "facebook_page_id"):
        op.add_column(
            "brands",
            sa.Column("facebook_page_id", sa.String(255), nullable=True),
        )
    if not _column_exists(conn, "brands", "instagram_business_id"):
        op.add_column(
            "brands",
            sa.Column("instagram_business_id", sa.String(255), nullable=True),
        )
    if not _column_exists(conn, "brands", "facebook_access_token"):
        op.add_column(
            "brands",
            sa.Column("facebook_access_token", sa.Text, nullable=True),
        )
    # Auto-approve for AutoPilot
    if not _column_exists(conn, "brands", "auto_approve_enabled"):
        op.add_column(
            "brands",
            sa.Column("auto_approve_enabled", sa.Boolean, server_default="false", nullable=False),
        )
    # Add confidence_score to ai_proposals if not present
    if not _column_exists(conn, "ai_proposals", "confidence_score"):
        op.add_column(
            "ai_proposals",
            sa.Column("confidence_score", sa.Float, server_default="0.0"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "ai_proposals", "confidence_score"):
        op.drop_column("ai_proposals", "confidence_score")
    op.drop_column("brands", "auto_approve_enabled")
    op.drop_column("brands", "facebook_access_token")
    op.drop_column("brands", "instagram_business_id")
    op.drop_column("brands", "facebook_page_id")
