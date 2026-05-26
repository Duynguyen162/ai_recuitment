from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    company_id = Column(BIGINT, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    txn_ref = Column(String(64), nullable=False, unique=True, index=True)
    plan = Column(String(32), nullable=False)
    plan_code = Column(String(64), nullable=True, index=True)
    cycle = Column(String(32), nullable=False)
    vip_duration_days = Column(Integer, nullable=True)
    amount = Column(Integer, nullable=False)  # VND
    amount_subunit = Column(Integer, nullable=False)  # VND * 100
    paid_amount = Column(Integer, nullable=True)  # VND received from webhook
    status = Column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    response_code = Column(String(8), nullable=True)
    bank_code = Column(String(32), nullable=True)
    pay_date = Column(String(32), nullable=True)
    vip_started_at = Column(DateTime(timezone=True), nullable=True)
    vip_expire_at = Column(DateTime(timezone=True), nullable=True)
    raw_payload = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
