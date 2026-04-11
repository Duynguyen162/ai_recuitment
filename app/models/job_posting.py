from sqlalchemy import Column, String, BIGINT, Text, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import JSONB 
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enum import JobTypeEnum, JobStatusEnum

class JobPosting(Base):
    __tablename__ = "job_postings"
    
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    company_id = Column(BIGINT, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    
    # Trường JSON cốt lõi cho AI Matching
    tags = Column(JSONB, nullable=True, default=list) 
    
    salary_min = Column(BIGINT, nullable=True)
    salary_max = Column(BIGINT, nullable=True)
    
    job_type = Column(Enum(JobTypeEnum), nullable=False)
    status = Column(Enum(JobStatusEnum), default=JobStatusEnum.draft, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expired_at = Column(DateTime(timezone=True), nullable=False)

    # Quan hệ
    company = relationship("Company", back_populates="job_postings")
    creator = relationship("User", backref="created_jobs")
    applications = relationship("Application",back_populates="job_posting",cascade="all, delete-orphan")
