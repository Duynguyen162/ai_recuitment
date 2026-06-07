"""add payment transactions table

Revision ID: 3f7c2d9e8a10
Revises: 2a6f9d3e4c11
Create Date: 2026-05-24 13:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f7c2d9e8a10"
down_revision: Union[str, Sequence[str], None] = "2a6f9d3e4c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("txn_ref", sa.String(length=64), nullable=False),
        sa.Column("plan", sa.String(length=32), nullable=False),
        sa.Column("cycle", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("amount_subunit", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("response_code", sa.String(length=8), nullable=True),
        sa.Column("bank_code", sa.String(length=32), nullable=True),
        sa.Column("pay_date", sa.String(length=32), nullable=True),
        sa.Column("raw_payload", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_transactions_company_id"), "payment_transactions", ["company_id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_created_by"), "payment_transactions", ["created_by"], unique=False)
    op.create_index(op.f("ix_payment_transactions_id"), "payment_transactions", ["id"], unique=False)
    op.create_index(op.f("ix_payment_transactions_status"), "payment_transactions", ["status"], unique=False)
    op.create_index(op.f("ix_payment_transactions_txn_ref"), "payment_transactions", ["txn_ref"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_transactions_txn_ref"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_status"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_created_by"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_company_id"), table_name="payment_transactions")
    op.drop_table("payment_transactions")
