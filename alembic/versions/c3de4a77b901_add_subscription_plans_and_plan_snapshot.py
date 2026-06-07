"""add subscription plans and plan snapshot

Revision ID: c3de4a77b901
Revises: 9b12f0d4a6c1
Create Date: 2026-05-24 16:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3de4a77b901"
down_revision: Union[str, Sequence[str], None] = "9b12f0d4a6c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscription_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("cycle", sa.String(length=32), nullable=False),
        sa.Column("price_vnd", sa.Integer(), nullable=False),
        sa.Column("vip_duration_days", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_subscription_plans_code"), "subscription_plans", ["code"], unique=True)
    op.create_index(op.f("ix_subscription_plans_cycle"), "subscription_plans", ["cycle"], unique=False)
    op.create_index(op.f("ix_subscription_plans_id"), "subscription_plans", ["id"], unique=False)

    op.add_column("payment_transactions", sa.Column("plan_code", sa.String(length=64), nullable=True))
    op.add_column("payment_transactions", sa.Column("vip_duration_days", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_payment_transactions_plan_code"), "payment_transactions", ["plan_code"], unique=False)

    op.execute(
        """
        INSERT INTO subscription_plans (code, name, cycle, price_vnd, vip_duration_days, is_active)
        VALUES
            ('vip_monthly', 'VIP Monthly', 'monthly', 499000, 30, true),
            ('vip_yearly', 'VIP Yearly', 'yearly', 4800000, 365, true)
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_transactions_plan_code"), table_name="payment_transactions")
    op.drop_column("payment_transactions", "vip_duration_days")
    op.drop_column("payment_transactions", "plan_code")

    op.drop_index(op.f("ix_subscription_plans_id"), table_name="subscription_plans")
    op.drop_index(op.f("ix_subscription_plans_cycle"), table_name="subscription_plans")
    op.drop_index(op.f("ix_subscription_plans_code"), table_name="subscription_plans")
    op.drop_table("subscription_plans")
