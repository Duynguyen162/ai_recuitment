from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.enum import CompanyVerificationStatusEnum, VerificationLogStatusEnum, DocumentStatus


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
    flagged_reason: Optional[str] = None
    created_at: datetime


class AdminJobReportItem(BaseModel):
    id: int
    job_id: int
    job_title: str
    company_name: str
    reporter_email: Optional[str] = None
    reason: str
    status: str
    created_at: datetime


class ResolveReportRequest(BaseModel):
    status: str  # "resolved" | "dismissed"


class JobActionRequest(BaseModel):
    action: str  # "allow" | "pause" | "close"


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
