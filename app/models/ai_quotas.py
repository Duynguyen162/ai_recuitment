from sqlalchemy import BIGINT, Column, Date, Integer, String, ForeignKey, UniqueConstraint
from app.db.base import Base

class UserAiQuota(Base):
    """Theo dõi số lượng token AI mà user đã sử dụng trong một ngày cụ thể."""
    __tablename__ = "user_ai_quotas"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    tokens_used = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_ai_quota_date"),
    )


class RoleAiQuota(Base):
    """Cấu hình hạn mức AI cho các Role không dùng chung SubscriptionPlan (như Candidate)."""
    __tablename__ = "role_ai_quotas"

    # role name is the PK since it's unique per role
    role = Column(String(50), primary_key=True, index=True)
    daily_token_limit = Column(Integer, nullable=False, default=5000)
