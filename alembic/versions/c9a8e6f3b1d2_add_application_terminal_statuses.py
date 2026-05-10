"""add application terminal statuses

Revision ID: c9a8e6f3b1d2
Revises: a1b2c3d4e5f6
Create Date: 2026-05-10 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9a8e6f3b1d2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TYPE applicationstatusenum ADD VALUE IF NOT EXISTS 'withdrawn'"
        )
        op.execute(
            "ALTER TYPE applicationstatusenum ADD VALUE IF NOT EXISTS 'left_company'"
        )


def downgrade() -> None:
    bind = op.get_bind()

    if bind.dialect.name != "postgresql":
        return

    op.execute(
        "UPDATE applications SET status = 'rejected' "
        "WHERE status IN ('withdrawn', 'left_company')"
    )

    op.execute("ALTER TABLE applications ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE applicationstatusenum RENAME TO applicationstatusenum_old")

    new_enum = sa.Enum(
        "applied",
        "interviewing",
        "hired",
        "rejected",
        "pending",
        "review",
        name="applicationstatusenum",
    )
    new_enum.create(bind, checkfirst=False)

    op.execute(
        "ALTER TABLE applications ALTER COLUMN status TYPE applicationstatusenum "
        "USING status::text::applicationstatusenum"
    )
    op.execute("DROP TYPE applicationstatusenum_old")
