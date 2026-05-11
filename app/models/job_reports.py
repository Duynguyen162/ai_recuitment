from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, String, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class JobReportStatusEnum(str, enum.Enum):
    pending = "pending"
    resolved = "resolved"
    dismissed = "dismissed"


class JobReport(Base):
    """Báo cáo tin tuyển dụng từ ứng viên."""
    __tablename__ = "job_reports"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    job_id = Column(BIGINT, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)
    reported_by = Column(BIGINT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(JobReportStatusEnum), nullable=False, default=JobReportStatusEnum.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job = relationship("JobPosting", backref="reports")
    reporter = relationship("User", backref="job_reports")
