"""update

Revision ID: 6d79a74f73be
Revises: 778660d65970
Create Date: 2026-05-06 15:43:20.588446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6d79a74f73be'
down_revision: Union[str, Sequence[str], None] = '778660d65970'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tạo bảng interviews (giữ nguyên)
    op.create_table('interviews',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.BigInteger(), nullable=False),
        sa.Column('interviewer_id', sa.BigInteger(), nullable=False),
        sa.Column('interview_time', sa.DateTime(), nullable=False),
        sa.Column('meeting_link', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['interviewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interviews_id'), 'interviews', ['id'], unique=False)

    # 2. 🔥 TẠO ENUM TRƯỚC
    document_status_enum = postgresql.ENUM(
        'processing', 'ready', 'failed',
        name='documentstatus'
    )
    document_status_enum.create(op.get_bind(), checkfirst=True)

    op.execute("ALTER TABLE company_documents ALTER COLUMN status DROP DEFAULT")

    # 2. ALTER TYPE
    op.alter_column(
        'company_documents',
        'status',
        existing_type=sa.VARCHAR(),
        type_=document_status_enum,
        existing_nullable=False,
        postgresql_using="status::documentstatus"
    )

    # 3. SET DEFAULT mới (ENUM)
    op.execute("ALTER TABLE company_documents ALTER COLUMN status SET DEFAULT 'processing'") 
    # 4. drop column
    op.drop_column('company_documents', 'error')

def downgrade() -> None:
    op.add_column('company_documents', sa.Column('error', sa.TEXT(), nullable=True))

    # 1. DROP default ENUM
    op.execute("ALTER TABLE company_documents ALTER COLUMN status DROP DEFAULT")

    # 2. convert về VARCHAR
    op.alter_column(
        'company_documents',
        'status',
        existing_type=postgresql.ENUM(
            'processing', 'ready', 'failed',
            name='documentstatus'
        ),
        type_=sa.VARCHAR(),
        existing_nullable=False
    )

    # 3. set lại default string
    op.execute("ALTER TABLE company_documents ALTER COLUMN status SET DEFAULT 'processing'")

    # 🔥 XÓA ENUM
    document_status_enum = postgresql.ENUM(
        'processing', 'ready', 'failed',
        name='documentstatus'
    )
    document_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index(op.f('ix_interviews_id'), table_name='interviews')
    op.drop_table('interviews')
