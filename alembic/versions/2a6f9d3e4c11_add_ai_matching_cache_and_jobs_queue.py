"""add ai matching cache and jobs queue

Revision ID: 2a6f9d3e4c11
Revises: 1059ca35dba2
Create Date: 2026-05-19 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2a6f9d3e4c11"
down_revision: Union[str, Sequence[str], None] = "1059ca35dba2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    job_status_enum = postgresql.ENUM(
    "queued",
    "processing",
    "done",
    "failed",
    "dead",
    name="aimatchingjobstatusenum",
    create_type=False,   # 🔥 QUAN TRỌNG
    )
    if bind.dialect.name == "postgresql":
        job_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "ai_matching_cache",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.BIGINT(), nullable=False),
        sa.Column("candidate_id", sa.BIGINT(), nullable=False),
        sa.Column("cv_fingerprint", sa.Text(), nullable=False),
        sa.Column("score", sa.DECIMAL(precision=5, scale=2), nullable=False),
        sa.Column(
            "strengths",
            postgresql.JSONB(astext_type=sa.Text()) if bind.dialect.name == "postgresql" else sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "weaknesses",
            postgresql.JSONB(astext_type=sa.Text()) if bind.dialect.name == "postgresql" else sa.JSON(),
            nullable=True,
        ),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "candidate_id", "cv_fingerprint", name="uq_ai_matching_cache_job_candidate_fingerprint"),
    )
    op.create_index(op.f("ix_ai_matching_cache_candidate_id"), "ai_matching_cache", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_ai_matching_cache_cv_fingerprint"), "ai_matching_cache", ["cv_fingerprint"], unique=False)
    op.create_index(op.f("ix_ai_matching_cache_id"), "ai_matching_cache", ["id"], unique=False)
    op.create_index(op.f("ix_ai_matching_cache_job_id"), "ai_matching_cache", ["job_id"], unique=False)

    op.create_table(
        "ai_matching_jobs",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.BIGINT(), nullable=False),
        sa.Column("job_id", sa.BIGINT(), nullable=False),
        sa.Column("candidate_id", sa.BIGINT(), nullable=False),
        sa.Column("cv_fingerprint", sa.Text(), nullable=False),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("locked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("worker_id", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["job_postings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(op.f("ix_ai_matching_jobs_candidate_id"), "ai_matching_jobs", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_ai_matching_jobs_cv_fingerprint"), "ai_matching_jobs", ["cv_fingerprint"], unique=False)
    op.create_index(op.f("ix_ai_matching_jobs_id"), "ai_matching_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_ai_matching_jobs_job_id"), "ai_matching_jobs", ["job_id"], unique=False)

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE UNIQUE INDEX uq_ai_matching_jobs_active_fingerprint
            ON ai_matching_jobs (job_id, candidate_id, cv_fingerprint)
            WHERE status IN ('queued', 'processing')
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS uq_ai_matching_jobs_active_fingerprint")
    op.drop_index(op.f("ix_ai_matching_jobs_job_id"), table_name="ai_matching_jobs")
    op.drop_index(op.f("ix_ai_matching_jobs_id"), table_name="ai_matching_jobs")
    op.drop_index(op.f("ix_ai_matching_jobs_cv_fingerprint"), table_name="ai_matching_jobs")
    op.drop_index(op.f("ix_ai_matching_jobs_candidate_id"), table_name="ai_matching_jobs")
    op.drop_table("ai_matching_jobs")

    op.drop_index(op.f("ix_ai_matching_cache_job_id"), table_name="ai_matching_cache")
    op.drop_index(op.f("ix_ai_matching_cache_id"), table_name="ai_matching_cache")
    op.drop_index(op.f("ix_ai_matching_cache_cv_fingerprint"), table_name="ai_matching_cache")
    op.drop_index(op.f("ix_ai_matching_cache_candidate_id"), table_name="ai_matching_cache")
    op.drop_table("ai_matching_cache")

    if bind.dialect.name == "postgresql":
        sa.Enum(name="aimatchingjobstatusenum").drop(bind, checkfirst=True)
