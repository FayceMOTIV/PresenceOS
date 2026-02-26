"""Repair: add all columns that may be missing after create_all skipped migrations

Revision ID: j7k8l9m0n1o2
Revises: i6d7e8f9g0h1
Create Date: 2026-02-26

This migration exists because Base.metadata.create_all() in init_db()
created the initial tables WITHOUT recording them in alembic_version.
A subsequent 'alembic upgrade head' then stamped the version to HEAD
without running intermediate ALTER TABLE migrations (they were already
"done" as far as Alembic was concerned).  This repair migration
unconditionally adds every column that might be missing.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "j7k8l9m0n1o2"
down_revision = "i6d7e8f9g0h1"
branch_labels = None
depends_on = None


def _col(conn, table: str, column: str) -> bool:
    """Return True if column already exists."""
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return r.fetchone() is not None


def _table(conn, name: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
    ), {"t": name})
    return r.fetchone() is not None


def _constraint(conn, name: str) -> bool:
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = :c"
    ), {"c": name})
    return r.fetchone() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # ── brands table ───────────────────────────────────────────
    if not _col(conn, "brands", "upload_post_username"):
        op.add_column("brands", sa.Column("upload_post_username", sa.String(255), nullable=True))

    if not _col(conn, "brands", "autopilot_enabled"):
        op.add_column("brands", sa.Column("autopilot_enabled", sa.Boolean, server_default="false"))

    if not _col(conn, "brands", "autopilot_config"):
        op.add_column("brands", sa.Column("autopilot_config", JSONB, nullable=True))

    if not _col(conn, "brands", "brand_dna"):
        op.add_column("brands", sa.Column("brand_dna", JSONB, nullable=True))

    if not _col(conn, "brands", "niche"):
        op.add_column("brands", sa.Column("niche", sa.String(50), nullable=True))

    if not _col(conn, "brands", "expo_push_token"):
        op.add_column("brands", sa.Column("expo_push_token", sa.String(255), nullable=True))

    if not _col(conn, "brands", "facebook_page_id"):
        op.add_column("brands", sa.Column("facebook_page_id", sa.String(255), nullable=True))

    if not _col(conn, "brands", "instagram_business_id"):
        op.add_column("brands", sa.Column("instagram_business_id", sa.String(255), nullable=True))

    if not _col(conn, "brands", "facebook_access_token"):
        op.add_column("brands", sa.Column("facebook_access_token", sa.Text, nullable=True))

    if not _col(conn, "brands", "auto_approve_enabled"):
        op.add_column("brands", sa.Column("auto_approve_enabled", sa.Boolean, server_default="false", nullable=False))

    # ── media_assets table ─────────────────────────────────────
    if _table(conn, "media_assets"):
        if not _col(conn, "media_assets", "improved_url"):
            op.add_column("media_assets", sa.Column("improved_url", sa.Text, nullable=True))
        if not _col(conn, "media_assets", "quality_score"):
            op.add_column("media_assets", sa.Column("quality_score", sa.Float, nullable=True))
        if not _col(conn, "media_assets", "processing_status"):
            op.add_column("media_assets", sa.Column("processing_status", sa.String(20), nullable=False, server_default="ready"))
        if not _col(conn, "media_assets", "linked_dish_id"):
            op.add_column("media_assets", sa.Column("linked_dish_id", UUID(as_uuid=True), nullable=True))
        if not _col(conn, "media_assets", "asset_label"):
            op.add_column("media_assets", sa.Column("asset_label", sa.String(255), nullable=True))
        if not _col(conn, "media_assets", "error_message"):
            op.add_column("media_assets", sa.Column("error_message", sa.Text, nullable=True))

    # ── ai_proposals table ─────────────────────────────────────
    if _table(conn, "ai_proposals"):
        if not _col(conn, "ai_proposals", "content_type"):
            op.add_column("ai_proposals", sa.Column("content_type", sa.String(30), nullable=True))
        if not _col(conn, "ai_proposals", "orchestrator_job_id"):
            op.add_column("ai_proposals", sa.Column("orchestrator_job_id", UUID(as_uuid=True), nullable=True))
        if not _col(conn, "ai_proposals", "brain_context"):
            op.add_column("ai_proposals", sa.Column("brain_context", JSONB, nullable=True))
        if not _col(conn, "ai_proposals", "confidence_score"):
            op.add_column("ai_proposals", sa.Column("confidence_score", sa.Float, server_default="0.0"))

    # ── scheduled_posts table ──────────────────────────────────
    if _table(conn, "scheduled_posts"):
        if not _col(conn, "scheduled_posts", "orchestrator_job_id"):
            op.add_column("scheduled_posts", sa.Column("orchestrator_job_id", UUID(as_uuid=True), nullable=True))
        if not _col(conn, "scheduled_posts", "brain_context"):
            op.add_column("scheduled_posts", sa.Column("brain_context", JSONB, nullable=True))

    # ── Foreign key: ai_proposals -> orchestrator_jobs ──────────
    if _table(conn, "orchestrator_jobs") and _table(conn, "ai_proposals"):
        if not _constraint(conn, "fk_ai_proposals_orchestrator_job"):
            op.create_foreign_key(
                "fk_ai_proposals_orchestrator_job",
                "ai_proposals",
                "orchestrator_jobs",
                ["orchestrator_job_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # ── Create tables that may be missing ──────────────────────
    # (create_all should have created them if models were imported,
    #  but just in case they're missing)

    if not _table(conn, "cm_interactions"):
        op.create_table(
            "cm_interactions",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("platform", sa.String(30), nullable=False),
            sa.Column("interaction_type", sa.String(30), nullable=False),
            sa.Column("external_id", sa.String(255), nullable=True),
            sa.Column("author_name", sa.String(255), nullable=True),
            sa.Column("content", sa.Text, nullable=True),
            sa.Column("ai_response", sa.Text, nullable=True),
            sa.Column("sentiment", sa.String(20), nullable=True),
            sa.Column("status", sa.String(20), server_default="pending"),
            sa.Column("metadata_json", JSONB, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not _table(conn, "video_credits"):
        op.create_table(
            "video_credits",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("brand_id", UUID(as_uuid=True), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
            sa.Column("plan", sa.String(20), nullable=False, server_default="trial"),
            sa.Column("credits_remaining", sa.Integer(), nullable=False, server_default="10"),
            sa.Column("credits_total", sa.Integer(), nullable=False, server_default="10"),
            sa.Column("reset_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.create_index("ix_video_credits_brand_id", "video_credits", ["brand_id"], unique=True)

    if not _table(conn, "brain_memories"):
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

    if not _table(conn, "visual_memories"):
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

    if not _table(conn, "visual_prompt_templates"):
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

    if not _table(conn, "orchestrator_jobs"):
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

    if not _table(conn, "instagram_stories"):
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

    if not _table(conn, "ugc_posts"):
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


def downgrade() -> None:
    # This is a repair migration — downgrade is a no-op since the
    # original migrations handle the real downgrade.
    pass
