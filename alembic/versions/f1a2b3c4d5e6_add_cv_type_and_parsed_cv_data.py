"""add cv type enum constraints and parsed cv data

Revision ID: f1a2b3c4d5e6
Revises: c9a8e6f3b1d2
Create Date: 2026-05-19 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c9a8e6f3b1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    cv_type_enum = postgresql.ENUM(
    "profile", "uploaded_cv",
    name="cvtypeenum",
    create_type=False
)

    parse_status_enum = postgresql.ENUM(
        "pending", "success", "failed",
        name="parsestatusenum",
        create_type=False
    )

    if bind.dialect.name == "postgresql":
        cv_type_enum.create(bind, checkfirst=True)
        parse_status_enum.create(bind, checkfirst=True)

    op.execute(
        "UPDATE applications SET cv_type = 'uploaded_cv' "
        "WHERE cv_type IS NOT NULL AND lower(cv_type) IN ('uploaded', 'upload', 'uploaded_cv')"
    )
    op.execute(
        "UPDATE applications SET cv_type = 'profile' "
        "WHERE cv_type IS NULL OR lower(cv_type) NOT IN ('profile', 'uploaded_cv')"
    )
    op.execute(
        "UPDATE applications SET cv_upload_id = NULL WHERE cv_type = 'profile'"
    )

    op.alter_column(
        "applications",
        "cv_type",
        existing_type=sa.String(length=20),
        type_=cv_type_enum,
        postgresql_using="cv_type::cvtypeenum",
        nullable=False,
    )

    op.alter_column(
        "applications",
        "cv_upload_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.create_check_constraint(
        "ck_application_cv_type_upload_match",
        "applications",
        "(cv_type = 'uploaded_cv' AND cv_upload_id IS NOT NULL) OR "
        "(cv_type = 'profile' AND cv_upload_id IS NULL)",
    )

    op.create_table(
        "parsed_cv_data",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.BIGINT(), nullable=False),
        sa.Column("candidate_id", sa.BIGINT(), nullable=False),
        sa.Column("source_type", cv_type_enum, nullable=False),
        sa.Column("parse_status", parse_status_enum, nullable=False),
        sa.Column(
            "parsed_json",
            postgresql.JSONB(astext_type=sa.Text()) if bind.dialect.name == "postgresql" else sa.JSON(),
            nullable=True,
        ),
        sa.Column("raw_text_snapshot", sa.Text(), nullable=True),
        sa.Column("parser_version", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(op.f("ix_parsed_cv_data_candidate_id"), "parsed_cv_data", ["candidate_id"], unique=False)
    op.create_index(op.f("ix_parsed_cv_data_id"), "parsed_cv_data", ["id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index(op.f("ix_parsed_cv_data_id"), table_name="parsed_cv_data")
    op.drop_index(op.f("ix_parsed_cv_data_candidate_id"), table_name="parsed_cv_data")
    op.drop_table("parsed_cv_data")

    op.drop_constraint("ck_application_cv_type_upload_match", "applications", type_="check")

    op.alter_column(
        "applications",
        "cv_type",
        existing_type=sa.Enum("profile", "uploaded_cv", name="cvtypeenum"),
        type_=sa.String(length=20),
        nullable=False,
    )

    if bind.dialect.name == "postgresql":
        sa.Enum(name="parsestatusenum").drop(bind, checkfirst=True)
        sa.Enum(name="cvtypeenum").drop(bind, checkfirst=True)
