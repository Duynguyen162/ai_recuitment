from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    cycle = Column(String(32), nullable=False, index=True)  # monthly/yearly
    price_vnd = Column(Integer, nullable=False)
    vip_duration_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true", default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
