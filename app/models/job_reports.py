from sqlalchemy import BIGINT, Column, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.core.enum import JobReportStatusEnum, ReportAdminActionEnum


class JobReport(Base):
    """Báo cáo tin tuyển dụng từ ứng viên."""
    __tablename__ = "job_reports"

    id          = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    job_id      = Column(BIGINT, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)
    reported_by = Column(BIGINT, ForeignKey("users.id",        ondelete="SET NULL"), nullable=True)
    reason      = Column(Text, nullable=False)
    status      = Column(SQLEnum(JobReportStatusEnum), nullable=False, default=JobReportStatusEnum.pending)

    # Trường ghi lại CÁCH Admin đã xử lý
    # Chỉ được ghi khi status chuyển sang resolved / dismissed
    admin_action = Column(
        SQLEnum(ReportAdminActionEnum),
        nullable=True,
        default=None,
        comment="Hành động Admin đã làm khi xử lý báo cáo này",
    )
    admin_note = Column(
        Text,
        nullable=True,
        default=None,
        comment="Ghi chú nội bộ của Admin (tùy chọn)",
    )
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Thời điểm Admin xử lý xong báo cáo",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job      = relationship("JobPosting", backref="reports")
    reporter = relationship("User", backref="job_reports")
