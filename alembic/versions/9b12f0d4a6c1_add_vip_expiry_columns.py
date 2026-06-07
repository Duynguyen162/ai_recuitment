"""add vip expiry columns

Revision ID: 9b12f0d4a6c1
Revises: 3f7c2d9e8a10
Create Date: 2026-05-24 15:25:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b12f0d4a6c1"
down_revision: Union[str, Sequence[str], None] = "3f7c2d9e8a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("vip_expire_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("payment_transactions", sa.Column("paid_amount", sa.Integer(), nullable=True))
    op.add_column("payment_transactions", sa.Column("vip_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("payment_transactions", sa.Column("vip_expire_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("payment_transactions", "vip_expire_at")
    op.drop_column("payment_transactions", "vip_started_at")
    op.drop_column("payment_transactions", "paid_amount")
    op.drop_column("companies", "vip_expire_at")
