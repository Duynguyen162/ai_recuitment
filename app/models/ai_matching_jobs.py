from sqlalchemy import BIGINT, TIMESTAMP, Column, Enum as SQLEnum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

from app.core.enum import AiMatchingJobStatusEnum
from app.db.base import Base


class AiMatchingJob(Base):
    __tablename__ = "ai_matching_jobs"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    application_id = Column(BIGINT, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    job_id = Column(BIGINT, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(BIGINT, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    cv_fingerprint = Column(Text, nullable=False, index=True)
    status = Column(SQLEnum(AiMatchingJobStatusEnum), nullable=False, default=AiMatchingJobStatusEnum.queued)
    attempt_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    locked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    worker_id = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    application = relationship("Application")
    job_posting = relationship("JobPosting")
    candidate_profile = relationship("CandidateProfile")
