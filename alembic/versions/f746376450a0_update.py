"""update

Revision ID: f746376450a0
Revises: 1c5da9f8859d
Create Date: 2026-04-10 11:21:20.249377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f746376450a0'
down_revision: Union[str, Sequence[str], None] = '1c5da9f8859d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    application_status_enum = sa.Enum(
        'applied',
        'interviewing',
        'hired',
        'rejected',
        name='applicationstatusenum'
    )

    # tạo enum type
    application_status_enum.create(op.get_bind())

    op.alter_column(
        'applications',
        'candidate_id',
        existing_type=sa.INTEGER(),
        type_=sa.BIGINT(),
        existing_nullable=False
    )

    op.alter_column(
        'applications',
        'status',
        existing_type=sa.VARCHAR(length=255),
        type_=application_status_enum,
        existing_nullable=False,
        postgresql_using="status::applicationstatusenum"
    )
    # ### end Alembic commands ###


def downgrade() -> None:

    application_status_enum = sa.Enum(
        'applied',
        'interviewing',
        'hired',
        'rejected',
        name='applicationstatusenum'
    )

    op.alter_column(
        'applications',
        'status',
        existing_type=application_status_enum,
        type_=sa.VARCHAR(length=255),
        existing_nullable=False
    )

    op.alter_column(
        'applications',
        'candidate_id',
        existing_type=sa.BIGINT(),
        type_=sa.INTEGER(),
        existing_nullable=False
    )

    application_status_enum.drop(op.get_bind())
    # ### end Alembic commands ###
