"""RS3 AutoPilot -- Brain tables

Revision ID: h5c6d7e8f9g0
Revises: g4b5c6d7e8f9
Create Date: 2026-02-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "h5c6d7e8f9g0"
down_revision = "g4b5c6d7e8f9"
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
    ), {"t": table_name})
    return result.fetchone() is not None


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns WHERE table_name = :t AND column_name = :c"
    ), {"t": table_name, "c": column_name})
    return result.fetchone() is not None


def _constraint_exists(conn, constraint_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = :c"
    ), {"c": constraint_name})
    return result.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ── brain_memories ─────────────────────────────────────────
    if not _table_exists(conn, "brain_memories"):
        op.create_table(
            "brain_memories",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("memory_type", sa.String(50), nullable=False),
            sa.Column("content", sa.Text, nullable=False),
            sa.Column("source", sa.String(100), nullable=True),
            sa.Column("confidence", sa.Float, default=0.5),
            sa.Column("access_count", sa.Integer, default=0),
            sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("embedding", JSONB, nullable=True),
            sa.Column("metadata_json", JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_brain_memories_brand_type", "brain_memories", ["brand_id", "memory_type"])

    # ── visual_memories ────────────────────────────────────────
    if not _table_exists(conn, "visual_memories"):
        op.create_table(
            "visual_memories",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("template_key", sa.String(100), nullable=False),
            sa.Column("prompt_used", sa.Text, nullable=False),
            sa.Column("image_url", sa.Text, nullable=True),
            sa.Column("engagement_score", sa.Float, nullable=True),
            sa.Column("impressions", sa.Integer, nullable=True),
            sa.Column("likes", sa.Integer, nullable=True),
            sa.Column("saves", sa.Integer, nullable=True),
            sa.Column("style_tags", JSONB, nullable=True),
            sa.Column("metadata_json", JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_visual_memories_brand_template", "visual_memories", ["brand_id", "template_key"])

    # ── visual_prompt_templates ─────────────────────────────────
    if not _table_exists(conn, "visual_prompt_templates"):
        op.create_table(
            "visual_prompt_templates",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("template_key", sa.String(100), nullable=False),
            sa.Column("prompt_template", sa.Text, nullable=False),
            sa.Column("style_params", JSONB, nullable=True),
            sa.Column("avg_engagement", sa.Float, default=0.0),
            sa.Column("use_count", sa.Integer, default=0),
            sa.Column("is_active", sa.Boolean, default=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_visual_prompt_templates_brand_key", "visual_prompt_templates", ["brand_id", "template_key"], unique=True)

    # ── orchestrator_jobs ──────────────────────────────────────
    if not _table_exists(conn, "orchestrator_jobs"):
        op.create_table(
            "orchestrator_jobs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("job_type", sa.String(50), nullable=False),
            sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
            sa.Column("config", JSONB, nullable=True),
            sa.Column("result", JSONB, nullable=True),
            sa.Column("posts_planned", sa.Integer, default=0),
            sa.Column("posts_generated", sa.Integer, default=0),
            sa.Column("stories_planned", sa.Integer, default=0),
            sa.Column("stories_generated", sa.Integer, default=0),
            sa.Column("error_log", sa.Text, nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    # ── instagram_stories ──────────────────────────────────────
    if not _table_exists(conn, "instagram_stories"):
        op.create_table(
            "instagram_stories",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("orchestrator_job_id", UUID(as_uuid=True), sa.ForeignKey("orchestrator_jobs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("story_type", sa.String(50), nullable=False),
            sa.Column("image_url", sa.Text, nullable=True),
            sa.Column("text_overlay", sa.Text, nullable=True),
            sa.Column("interactive_data", JSONB, nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(30), server_default="draft"),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    # ── ugc_posts ──────────────────────────────────────────────
    if not _table_exists(conn, "ugc_posts"):
        op.create_table(
            "ugc_posts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("source_platform", sa.String(50), nullable=False),
            sa.Column("source_url", sa.Text, nullable=True),
            sa.Column("author_username", sa.String(255), nullable=True),
            sa.Column("media_url", sa.Text, nullable=True),
            sa.Column("caption", sa.Text, nullable=True),
            sa.Column("permission_status", sa.String(30), server_default="pending"),
            sa.Column("permission_requested_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reposted", sa.Boolean, default=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    # ── ALTER scheduled_posts: add orchestrator_job_id ──────────
    if not _column_exists(conn, "scheduled_posts", "orchestrator_job_id"):
        op.add_column("scheduled_posts", sa.Column("orchestrator_job_id", UUID(as_uuid=True), nullable=True))
    if not _column_exists(conn, "scheduled_posts", "brain_context"):
        op.add_column("scheduled_posts", sa.Column("brain_context", JSONB, nullable=True))

    # ── ALTER ai_proposals: add orchestrator columns ──────────
    if not _column_exists(conn, "ai_proposals", "content_type"):
        op.add_column("ai_proposals", sa.Column("content_type", sa.String(30), nullable=True))
    if not _column_exists(conn, "ai_proposals", "orchestrator_job_id"):
        op.add_column("ai_proposals", sa.Column("orchestrator_job_id", UUID(as_uuid=True), nullable=True))
    if not _constraint_exists(conn, "fk_ai_proposals_orchestrator_job"):
        op.create_foreign_key(
            "fk_ai_proposals_orchestrator_job",
            "ai_proposals",
            "orchestrator_jobs",
            ["orchestrator_job_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not _column_exists(conn, "ai_proposals", "brain_context"):
        op.add_column("ai_proposals", sa.Column("brain_context", JSONB, nullable=True))

    # ── ALTER brands: add autopilot config columns ──────────────
    if not _column_exists(conn, "brands", "autopilot_enabled"):
        op.add_column("brands", sa.Column("autopilot_enabled", sa.Boolean, server_default="false"))
    if not _column_exists(conn, "brands", "autopilot_config"):
        op.add_column("brands", sa.Column("autopilot_config", JSONB, nullable=True))
    if not _column_exists(conn, "brands", "brand_dna"):
        op.add_column("brands", sa.Column("brand_dna", JSONB, nullable=True))
    if not _column_exists(conn, "brands", "niche"):
        op.add_column("brands", sa.Column("niche", sa.String(50), nullable=True))
    if not _column_exists(conn, "brands", "expo_push_token"):
        op.add_column("brands", sa.Column("expo_push_token", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("brands", "expo_push_token")
    op.drop_column("brands", "niche")
    op.drop_column("brands", "brand_dna")
    op.drop_column("brands", "autopilot_config")
    op.drop_column("brands", "autopilot_enabled")
    op.drop_column("ai_proposals", "brain_context")
    op.drop_constraint("fk_ai_proposals_orchestrator_job", "ai_proposals", type_="foreignkey")
    op.drop_column("ai_proposals", "orchestrator_job_id")
    op.drop_column("ai_proposals", "content_type")
    op.drop_column("scheduled_posts", "brain_context")
    op.drop_column("scheduled_posts", "orchestrator_job_id")
    op.drop_table("ugc_posts")
    op.drop_table("instagram_stories")
    op.drop_table("orchestrator_jobs")
    op.drop_index("ix_visual_prompt_templates_brand_key", "visual_prompt_templates")
    op.drop_table("visual_prompt_templates")
    op.drop_index("ix_visual_memories_brand_template", "visual_memories")
    op.drop_table("visual_memories")
    op.drop_index("ix_brain_memories_brand_type", "brain_memories")
    op.drop_table("brain_memories")
