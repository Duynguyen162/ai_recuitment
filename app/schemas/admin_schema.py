from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.enum import (
    CompanyVerificationStatusEnum,
    VerificationLogStatusEnum,
    DocumentStatus,
    JobReportStatusEnum,
    AdminJobActionEnum,
    ReportAdminActionEnum,
    StatusEnum,
)


# ─── A-01: Dashboard Stats ───────────────────────────────────────────────────

class AdminDashboardStats(BaseModel):
    # Row 1
    total_users: int
    total_companies: int
    total_jobs: int
    total_applications: int
    # Row 2
    active_users_today: int
    pending_companies: int
    flagged_jobs: int
    pending_reports: int


class NewUserByDay(BaseModel):
    date: str
    count: int


class RoleDistribution(BaseModel):
    candidate: int
    hr_manager: int


class ApplicationByStatus(BaseModel):
    status: str
    count: int


class AdminDashboardChartsResponse(BaseModel):
    new_users_by_day: List[NewUserByDay]
    role_distribution: RoleDistribution
    applications_by_status: List[ApplicationByStatus]


# ─── A-04/A-05: Companies ────────────────────────────────────────────────────

class CompanyVerificationHistoryItem(BaseModel):
    id: int
    status: VerificationLogStatusEnum
    license_url: str
    reviewed_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminCompanyListItem(BaseModel):
    id: int
    name: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    size: Optional[str] = None
    verification_status: CompanyVerificationStatusEnum
    created_at: datetime
    hr_member_count: int

    class Config:
        from_attributes = True


class AdminCompanyDetailResponse(BaseModel):
    id: int
    name: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    size: Optional[str] = None
    verification_status: CompanyVerificationStatusEnum
    created_at: datetime
    verification_history: List[CompanyVerificationHistoryItem]
    documents: List[dict]

    class Config:
        from_attributes = True


class AdminVerifyRequest(BaseModel):
    status: CompanyVerificationStatusEnum
    reason: Optional[str] = None  # Dùng khi từ chối


# ─── A-06: Job Reports ───────────────────────────────────────────────────────

class AdminJobFlaggedItem(BaseModel):
    id: int
    title: str
    company_name: str
    status: str
    locked_by_admin: bool
    flagged_reason: Optional[str] = None
    created_at: datetime


class AdminJobReportItem(BaseModel):
    id: int
    job_id: int
    job_title: str
    company_name: str
    reporter_email: Optional[str] = None
    reason: str
    status: JobReportStatusEnum
    # Chi tiết xử lý (chỉ có sau khi Admin đã xử lý)
    admin_action: Optional[ReportAdminActionEnum] = None
    admin_note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class ResolveReportRequest(BaseModel):
    """
    Chỉ cho phép chuyển sang resolved | dismissed.
    bắt buộc truyền admin_action để Frontend hiển thị đú́ng hành động đã thực hiện.
    """
    status: JobReportStatusEnum
    admin_action: ReportAdminActionEnum    # Bắt buộc — phải chọn admin đã làm gì
    admin_note: Optional[str] = None       # Ghi chú nội bộ (tùy chọn)

    class Config:
        use_enum_values = True


class JobActionRequest(BaseModel):
    """
    Hành động của Admin lên Job.
    - allow  → published  + gỡ lock (HR có thể kiểm soát lại)
    - pause  → paused     (tạm khóa để xem xét, chưa lock vĩnh viễn)
    - close  → closed     + bật locked_by_admin (HR không mở lại được)
    """
    action: AdminJobActionEnum

    class Config:
        use_enum_values = True


# ─── A-08: Candidates (mới) ──────────────────────────────────────────────────

class AdminCandidateListItem(BaseModel):
    """Thông tin tóm tắt ứng viên trong danh sách Admin."""
    id: int                          # user.id
    email: str
    status: StatusEnum
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    years_of_experience: Optional[int] = None
    total_applications: int
    created_at: datetime

    class Config:
        from_attributes = True


class AdminCandidateDetailResponse(BaseModel):
    """Chi tiết ứng viên — dành cho trang xem xét của Admin."""
    id: int
    email: str
    status: StatusEnum
    created_at: datetime
    # Profile
    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    skill_tags: Optional[List[str]] = None
    years_of_experience: Optional[int] = None
    # Thống kê
    total_applications: int
    total_reports_filed: int         # Số lần ứng viên này đã báo cáo job

    class Config:
        from_attributes = True


class LockCandidateRequest(BaseModel):
    """
    Khóa hoặc mở tài khoản ứng viên.
    - lock=true  → user.status = banned
    - lock=false → user.status = active
    """
    lock: bool
    reason: Optional[str] = None     # Ghi chú nội bộ (tùy chọn)


# ─── A-07: AI Monitoring ─────────────────────────────────────────────────────

class AiMonitoringStats(BaseModel):
    total_calls_today: int
    total_tokens_today: int
    avg_latency_ms: int
    error_rate_percent: float


class AiLogItem(BaseModel):
    id: int
    service_type: str
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    is_error: bool
    error_message: Optional[str] = None
    application_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AiAlertConfigItem(BaseModel):
    id: int
    name: str
    metric: str
    threshold: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AiAlertConfigUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    threshold: Optional[int] = None


class TokenUsageByHour(BaseModel):
    hour: str
    tokens: int


class ErrorRateByDay(BaseModel):
    date: str
    error_rate: float
