"""add upload_post_username to brands

Revision ID: f3a4b5c6d7e8
Revises: e2f3g4h5i6j7
Create Date: 2026-02-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f3a4b5c6d7e8"
down_revision = "e2f3g4h5i6j7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'brands' AND column_name = 'upload_post_username'"
    ))
    if not result.fetchone():
        op.add_column(
            "brands",
            sa.Column("upload_post_username", sa.String(255), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("brands", "upload_post_username")
