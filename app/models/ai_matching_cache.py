from sqlalchemy import BIGINT, DECIMAL, TIMESTAMP, Column, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class AiMatchingCache(Base):
    __tablename__ = "ai_matching_cache"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "candidate_id",
            "cv_fingerprint",
            name="uq_ai_matching_cache_job_candidate_fingerprint",
        ),
    )

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    job_id = Column(BIGINT, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(BIGINT, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    cv_fingerprint = Column(Text, nullable=False, index=True)
    score = Column(DECIMAL(5, 2), nullable=False)
    strengths = Column(JSONB, nullable=True)
    weaknesses = Column(JSONB, nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    job_posting = relationship("JobPosting")
    candidate_profile = relationship("CandidateProfile")
