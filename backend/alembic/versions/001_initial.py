"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("avatar_url", sa.Text),
        sa.Column("auth_provider", sa.String(50), server_default="email"),
        sa.Column("auth_provider_id", sa.Text),
        sa.Column("password_hash", sa.Text),
        sa.Column("timezone", sa.String(100), server_default="America/Vancouver"),
        sa.Column("email_verified", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "subscription_tiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("stripe_price_id", sa.Text),
        sa.Column("monthly_price_cents", sa.Integer),
        sa.Column("credits_per_month", sa.Integer),
        sa.Column("features", postgresql.JSONB),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("tier_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscription_tiers.id")),
        sa.Column("stripe_subscription_id", sa.Text),
        sa.Column("stripe_customer_id", sa.Text),
        sa.Column("status", sa.String(50), server_default="active"),
        sa.Column("current_period_start", sa.DateTime(timezone=True)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("cancel_at_period_end", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), server_default="Untitled Resume"),
        sa.Column("original_file_path", sa.Text),
        sa.Column("parsed_text", sa.Text),
        sa.Column("structured_data", postgresql.JSONB),
        sa.Column("file_type", sa.String(10)),
        sa.Column("embedding", Vector(768)),
        sa.Column("is_archived", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("company", sa.String(500)),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("extracted_keywords", postgresql.JSONB),
        sa.Column("embedding", Vector(768)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "optimizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resumes.id"), nullable=False),
        sa.Column("jd_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("pre_score", sa.Float),
        sa.Column("post_score", sa.Float),
        sa.Column("original_bullets", postgresql.JSONB),
        sa.Column("optimized_bullets", postgresql.JSONB),
        sa.Column("cover_letter_text", sa.Text),
        sa.Column("output_file_path", sa.Text),
        sa.Column("processing_time_ms", sa.Integer),
        sa.Column("model_used", sa.String(100)),
        sa.Column("error_message", sa.Text),
        sa.Column("fabrication_flags", postgresql.JSONB),
        sa.Column("credit_cost", sa.Integer, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "credit_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("month_start", sa.Date, nullable=False),
        sa.Column("credits_used", sa.Integer, server_default="0"),
        sa.UniqueConstraint("user_id", "month_start"),
    )

    op.create_table(
        "blog_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(500), unique=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content_md", sa.Text),
        sa.Column("meta_description", sa.Text),
        sa.Column("keywords", postgresql.JSONB),
        sa.Column("category", sa.String(100)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("is_published", sa.Boolean, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="running"),
        sa.Column("output_path", sa.Text),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("agent_runs")
    op.drop_table("blog_posts")
    op.drop_table("credit_usage")
    op.drop_table("optimizations")
    op.drop_table("job_descriptions")
    op.drop_table("resumes")
    op.drop_table("subscriptions")
    op.drop_table("subscription_tiers")
    op.drop_table("users")
