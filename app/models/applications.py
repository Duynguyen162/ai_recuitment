from sqlalchemy import Enum as SQLEnum
from sqlalchemy import BIGINT, CheckConstraint, Column, Integer, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.enum import ApplicationStatusEnum, CvTypeEnum
from app.db.base import Base
from sqlalchemy import DateTime

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint(
            "(cv_type = 'uploaded_cv' AND cv_upload_id IS NOT NULL) OR "
            "(cv_type = 'profile' AND cv_upload_id IS NULL)",
            name="ck_application_cv_type_upload_match",
        ),
    )
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    job_id = Column(BIGINT, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(BIGINT, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(ApplicationStatusEnum), nullable=False, default=ApplicationStatusEnum.pending)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    cv_upload_id = Column(Integer, ForeignKey("cv_uploads.id"), nullable=True)
    cv_type = Column(SQLEnum(CvTypeEnum), nullable=False, default=CvTypeEnum.profile)
    
    job_posting = relationship("JobPosting", back_populates="applications")
    candidate_profile = relationship("CandidateProfile", back_populates="applications")
    ai_analysis = relationship("AiMatchingScore", back_populates="application", uselist=False, cascade="all, delete-orphan")
    parsed_cv_data = relationship("ParsedCVData", back_populates="application", uselist=False, cascade="all, delete-orphan")
    
    cv_uploads = relationship("CVUpload", back_populates="applications")
    interviews = relationship("Interview",back_populates="application",cascade="all, delete-orphan")
