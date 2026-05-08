from sqlalchemy import DateTime
from sqlalchemy import BIGINT, Column, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class SaveJob(Base):
    __tablename__ = "saved_jobs"
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(BIGINT, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(BIGINT, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False )
    
    candidate = relationship("CandidateProfile", back_populates="saved_jobs")
    job_posting = relationship("JobPosting", back_populates="saved_jobs")
