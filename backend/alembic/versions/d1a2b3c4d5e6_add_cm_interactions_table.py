"""Add cm_interactions table

Revision ID: d1a2b3c4d5e6
Revises: c039371b2cf1
Create Date: 2026-02-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1a2b3c4d5e6"
down_revision: Union[str, None] = "c039371b2cf1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cm_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("interaction_type", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("commenter_name", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("classification", sa.String(20), nullable=False, server_default="neutral"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("ai_response_draft", sa.Text(), nullable=True),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column("final_response", sa.Text(), nullable=True),
        sa.Column("response_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("human_rating", sa.SmallInteger(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("platform_response_id", sa.String(255), nullable=True),
        sa.Column("extra_metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["brand_id"],
            ["brands.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_cm_interactions_brand_id", "cm_interactions", ["brand_id"])
    op.create_index("ix_cm_interactions_platform", "cm_interactions", ["platform"])
    op.create_index(
        "ix_cm_interactions_status_created",
        "cm_interactions",
        ["response_status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_cm_interactions_status_created", table_name="cm_interactions")
    op.drop_index("ix_cm_interactions_platform", table_name="cm_interactions")
    op.drop_index("ix_cm_interactions_brand_id", table_name="cm_interactions")
    op.drop_table("cm_interactions")
