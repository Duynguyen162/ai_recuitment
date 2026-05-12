from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class CompanyFollow(Base):
    """Ứng viên theo dõi công ty."""
    __tablename__ = "company_follows"

    id          = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(BIGINT, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    company_id   = Column(BIGINT, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    followed_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Mỗi ứng viên chỉ follow 1 lần mỗi công ty
    __table_args__ = (
        UniqueConstraint("candidate_id", "company_id", name="uq_candidate_company_follow"),
    )

    candidate = relationship("CandidateProfile", backref="company_follows")
    company   = relationship("Company", backref="followers")
