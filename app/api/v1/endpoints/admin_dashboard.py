from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.enum import CompanyVerificationStatusEnum, JobReportStatusEnum, ReportAdminActionEnum, RoleEnum, StatusEnum
from app.crud import crud_admin_dashboard as crud
from app.db.database import get_db
from app.models.user import User
from app.schemas.admin_schema import (
    AdminCandidateDetailResponse,
    AdminCandidateListItem,
    AdminCompanyDetailResponse,
    AdminCompanyListItem,
    AdminDashboardChartsResponse,
    AdminDashboardStats,
    AdminJobFlaggedItem,
    AdminJobReportItem,
    AdminVerifyRequest,
    AiAlertConfigItem,
    AiAlertConfigCreate,
    AiAlertConfigUpdateRequest,
    AiLogItem,
    AiMonitoringStats,
    JobActionRequest,
    LockCandidateRequest,
    ResolveReportRequest,
    RoleAiQuotaItem,
    RoleAiQuotaUpdateRequest,
    TopAiUserUsageItem,
)
from app.schemas.base_schema import ResponseSchema

router = APIRouter(tags=["Admin Dashboard"])


def _require_admin(current_user: User):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")

@router.get(
    "/dashboard/stats",
    response_model=ResponseSchema[AdminDashboardStats],
    summary="Thống kê tổng quan Admin Dashboard",
)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    stats = crud.get_admin_dashboard_stats(db)
    return ResponseSchema(success=True, data=stats, error=None, meta=None)


@router.get(
    "/dashboard/charts",
    response_model=ResponseSchema[AdminDashboardChartsResponse],
    summary="Dữ liệu chart Admin Dashboard",
)
def get_dashboard_charts(
    days: int = Query(7, description="Số ngày lấy dữ liệu: 7 | 30 | 90"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    charts = crud.get_admin_dashboard_charts(db, days=days)
    return ResponseSchema(success=True, data=charts, error=None, meta=None)

@router.get(
    "/companies",
    response_model=ResponseSchema[List[AdminCompanyListItem]],
    summary="Danh sách công ty (có filter theo status)",
)
def list_companies(
    status: Optional[CompanyVerificationStatusEnum] = Query(None, description="Lọc theo trạng thái"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    companies, total = crud.get_admin_companies(db, status=status, page=page, page_size=page_size)
    return ResponseSchema(
        success=True,
        data=companies,
        error=None,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    )


@router.get(
    "/companies/{company_id}",
    response_model=ResponseSchema[AdminCompanyDetailResponse],
    summary="Chi tiết công ty + lịch sử xác minh",
)
def get_company_detail(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    detail = crud.get_admin_company_detail(db, company_id)
    return ResponseSchema(success=True, data=detail, error=None, meta=None)


@router.put(
    "/companies/{company_id}/verify",
    response_model=ResponseSchema[dict],
    summary="Duyệt / Từ chối / Khóa công ty",
)
def verify_company(
    company_id: int,
    body: AdminVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    company = crud.admin_update_company_status(
        db,
        company_id=company_id,
        new_status=body.status,
        admin_id=current_user.id,
        reason=body.reason,
    )
    return ResponseSchema(
        success=True,
        data={"id": company.id, "verification_status": company.verification_status.value},
        error=None,
        meta=None,
    )

@router.get(
    "/jobs/flagged",
    response_model=ResponseSchema[List[AdminJobFlaggedItem]],
    summary="Danh sách job bị flag (paused hoặc bị Admin lock)",
)
def get_flagged_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    jobs, total = crud.get_flagged_jobs(db, page=page, page_size=page_size)
    return ResponseSchema(
        success=True,
        data=jobs,
        error=None,
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.post(
    "/jobs/{job_id}/action",
    response_model=ResponseSchema[dict],
    summary="Hành động Admin lên Job (close)",
)
def job_action(
    job_id: int,
    body: JobActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    - close: Đóng vĩnh viễn → closed + locked_by_admin=True, HR không tự mở lại được.
    """
    _require_admin(current_user)
    job = crud.admin_update_job_status(db, job_id=job_id, action=body.action)
    return ResponseSchema(
        success=True,
        data={
            "id": job.id,
            "status": job.status.value,
            "locked_by_admin": job.locked_by_admin,
        },
        error=None,
        meta=None,
    )


@router.get(
    "/job-reports",
    response_model=ResponseSchema[List[AdminJobReportItem]],
    summary="Danh sách báo cáo job từ ứng viên",
)
def get_job_reports(
    status: Optional[JobReportStatusEnum] = Query(
        None,
        description="Lọc theo trạng thái: pending | resolved | dismissed",
    ),
    admin_action: Optional[ReportAdminActionEnum] = Query(
        None,
        description="Lọc theo hành động đã xử lý: paused_job | closed_job | warned | no_action",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    reports, total = crud.get_job_reports(
        db,
        status=status,
        admin_action=admin_action,
        page=page,
        page_size=page_size,
    )
    return ResponseSchema(
        success=True,
        data=reports,
        error=None,
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.put(
    "/job-reports/{job_id}/resolve",
    response_model=ResponseSchema[dict],
    summary="Xử lý / Bỏ qua tất cả báo cáo của một job",
)
def resolve_report(
    job_id: int,
    body: ResolveReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Đánh dấu tất cả báo cáo của một job là đã xử lý (resolved / dismissed).
    Bắt buộc truyền `admin_action` để ghi lại admin đã làm gì:
    - `closed_job`  — Đóng vĩnh viễn + khóa tin
    - `no_action`   — Bỏ qua, không có hành động
    """
    _require_admin(current_user)
    report_result = crud.resolve_job_report(
        db,
        job_id=job_id,
        new_status=body.status,
        admin_action=body.admin_action,
        admin_note=body.admin_note,
    )
    return ResponseSchema(
        success=True,
        data={
            "job_id": report_result["job_id"],
            "status": report_result["status"].value,
            "admin_action": report_result["admin_action"].value if report_result["admin_action"] else None,
            "admin_note": report_result["admin_note"],
            "resolved_at": report_result["resolved_at"].isoformat() if report_result["resolved_at"] else None,
        },
        error=None,
        meta=None,
    )

@router.get(
    "/candidates",
    response_model=ResponseSchema[List[AdminCandidateListItem]],
    summary="Danh sách ứng viên (filter + search)",
    tags=["Admin Dashboard", "Admin Candidates"],
)
def list_candidates(
    keyword: Optional[str] = Query(None, description="Tìm theo email hoặc tên"),
    status: Optional[StatusEnum] = Query(None, description="Lọc theo trạng thái: active | banned"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    candidates, total = crud.get_admin_candidates(
        db,
        keyword=keyword,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ResponseSchema(
        success=True,
        data=candidates,
        error=None,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    )


@router.get(
    "/candidates/{candidate_id}",
    response_model=ResponseSchema[AdminCandidateDetailResponse],
    summary="Chi tiết ứng viên",
    tags=["Admin Dashboard", "Admin Candidates"],
)
def get_candidate_detail(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    detail = crud.get_admin_candidate_detail(db, candidate_id)
    return ResponseSchema(success=True, data=detail, error=None, meta=None)


@router.put(
    "/candidates/{candidate_id}/lock",
    response_model=ResponseSchema[dict],
    summary="Khóa / Mở tài khoản ứng viên",
    tags=["Admin Dashboard", "Admin Candidates"],
)
def lock_candidate(
    candidate_id: int,
    body: LockCandidateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    - **lock=true**:  Khóa tài khoản → user.status = `banned`.
      Ứng viên sẽ không thể đăng nhập.
    - **lock=false**: Mở khóa → user.status = `active`.
    """
    _require_admin(current_user)
    user = crud.admin_lock_candidate(db, candidate_id=candidate_id, lock=body.lock)
    return ResponseSchema(
        success=True,
        data={
            "id": user.id,
            "email": user.email,
            "status": user.status.value,
        },
        error=None,
        meta=None,
    )

@router.get(
    "/ai-monitoring/stats",
    response_model=ResponseSchema[AiMonitoringStats],
    summary="Thống kê AI hôm nay (calls, tokens, latency, error rate)",
)
def get_ai_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    stats = crud.get_ai_monitoring_stats(db)
    return ResponseSchema(success=True, data=stats, error=None, meta=None)


@router.get(
    "/ai-monitoring/charts",
    response_model=ResponseSchema[dict],
    summary="Chart token usage theo giờ & error rate theo ngày",
)
def get_ai_charts(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    data = crud.get_ai_chart_data(db, days=days)
    return ResponseSchema(success=True, data=data, error=None, meta=None)


@router.get(
    "/ai-logs",
    response_model=ResponseSchema[List[AiLogItem]],
    summary="DataTable log từng lần gọi AI",
)
def get_ai_logs(
    service_type: Optional[str] = Query(None, description="matching | chatbot | jd_moderation"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    is_error: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    logs, total = crud.get_ai_logs(
        db,
        service_type=service_type,
        date_from=date_from,
        date_to=date_to,
        is_error=is_error,
        page=page,
        page_size=page_size,
    )
    return ResponseSchema(
        success=True,
        data=logs,
        error=None,
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.get(
    "/ai-alert-configs",
    response_model=ResponseSchema[List[AiAlertConfigItem]],
    summary="Danh sách cấu hình cảnh báo AI",
)
def get_alert_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    configs = crud.get_ai_alert_configs(db)
    return ResponseSchema(success=True, data=configs, error=None, meta=None)


@router.post(
    "/ai-alert-configs",
    response_model=ResponseSchema[AiAlertConfigItem],
    summary="Tạo mới cấu hình cảnh báo AI",
)
def create_alert_config(
    body: AiAlertConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    config = crud.create_ai_alert_config(
        db,
        name=body.name,
        metric=body.metric,
        threshold=body.threshold,
        is_active=body.is_active
    )
    return ResponseSchema(success=True, data=config, error=None, meta=None)


@router.put(
    "/ai-alert-configs/{config_id}",
    response_model=ResponseSchema[AiAlertConfigItem],
    summary="Bật/tắt hoặc chỉnh threshold cảnh báo AI",
)
def update_alert_config(
    config_id: int,
    body: AiAlertConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    config = crud.update_ai_alert_config(
        db,
        config_id=config_id,
        is_active=body.is_active,
        threshold=body.threshold,
    )
    return ResponseSchema(success=True, data=config, error=None, meta=None)


@router.get(
    "/dashboard/ai-quotas/candidate",
    response_model=ResponseSchema[RoleAiQuotaItem],
    summary="Lấy hạn mức AI của Ứng viên",
)
def get_candidate_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    # Tìm quota của candidate, nếu chưa có thì trả về mặc định
    quota = crud.get_role_ai_quotas(db)
    cand_quota = next((q for q in quota if q.role == "candidate"), None)
    if not cand_quota:
        cand_quota = RoleAiQuotaItem(role="candidate", daily_token_limit=5000)
    return ResponseSchema(success=True, data=cand_quota, error=None, meta=None)


@router.put(
    "/dashboard/ai-quotas/candidate",
    response_model=ResponseSchema[RoleAiQuotaItem],
    summary="Cập nhật hạn mức AI cho Ứng viên",
)
def update_candidate_quota(
    body: RoleAiQuotaUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    quota = crud.update_role_ai_quota(db, role="candidate", daily_token_limit=body.daily_token_limit)
    return ResponseSchema(success=True, data=quota, error=None, meta=None)


@router.get(
    "/dashboard/ai-quotas/top-users",
    response_model=ResponseSchema[List[TopAiUserUsageItem]],
    summary="Hiển thị Top user sử dụng nhiều AI token nhất",
)
def get_top_ai_users(
    limit: int = Query(10, description="Số lượng user tối đa cần hiển thị"),
    role: Optional[str] = Query(None, description="Lọc theo role (ví dụ: candidate, hr_manager)"),
    timeframe: Optional[str] = Query("today", description="Lọc theo thời gian: today, month"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    users = crud.get_top_ai_users(db, limit=limit, role=role, timeframe=timeframe)
    return ResponseSchema(success=True, data=users, error=None, meta=None)
