"""
Endpoints Admin:
  GET  /admin/dashboard/stats
  GET  /admin/dashboard/charts?days=7|30|90

  GET  /admin/companies?status=&page=&page_size=
  GET  /admin/companies/{company_id}
  PUT  /admin/companies/{company_id}/verify

  GET  /admin/jobs/flagged?page=&page_size=
  POST /admin/jobs/{job_id}/action
  GET  /admin/job-reports?page=&page_size=
  PUT  /admin/job-reports/{report_id}/resolve

  GET  /admin/ai-logs?service_type=&date_from=&date_to=&is_error=&page=&page_size=
  GET  /admin/ai-monitoring/stats
  GET  /admin/ai-monitoring/charts?days=7
  GET  /admin/ai-alert-configs
  PUT  /admin/ai-alert-configs/{config_id}
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.enum import CompanyVerificationStatusEnum, RoleEnum
from app.crud import crud_admin_dashboard as crud
from app.db.database import get_db
from app.models.user import User
from app.schemas.admin_schema import (
    AdminCompanyDetailResponse,
    AdminCompanyListItem,
    AdminDashboardChartsResponse,
    AdminDashboardStats,
    AdminJobFlaggedItem,
    AdminJobReportItem,
    AdminVerifyRequest,
    AiAlertConfigItem,
    AiAlertConfigUpdateRequest,
    AiLogItem,
    AiMonitoringStats,
    JobActionRequest,
    ResolveReportRequest,
)
from app.schemas.base_schema import ResponseSchema

router = APIRouter(tags=["Admin Dashboard"])


def _require_admin(current_user: User):
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")

@router.get(
    "/dashboard/stats",
    response_model=ResponseSchema[AdminDashboardStats],
    summary="A-01: Thống kê tổng quan Admin Dashboard",
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
    summary="A-01: Dữ liệu chart Admin Dashboard",
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
    summary="A-04: Danh sách công ty (có filter theo status)",
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
    summary="A-05: Chi tiết công ty + lịch sử xác minh",
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
    summary="A-05: Duyệt / Từ chối / Khóa công ty",
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
    summary="A-06: Danh sách job bị flag (đang bị paused)",
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
    summary="A-06: Hành động lên Job (allow / pause / close)",
)
def job_action(
    job_id: int,
    body: JobActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    job = crud.admin_update_job_status(db, job_id=job_id, action=body.action)
    return ResponseSchema(
        success=True,
        data={"id": job.id, "status": job.status.value},
        error=None,
        meta=None,
    )


@router.get(
    "/job-reports",
    response_model=ResponseSchema[List[AdminJobReportItem]],
    summary="A-06: Danh sách báo cáo job từ ứng viên",
)
def get_job_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    reports, total = crud.get_job_reports(db, page=page, page_size=page_size)
    return ResponseSchema(
        success=True,
        data=reports,
        error=None,
        meta={"page": page, "page_size": page_size, "total": total},
    )


@router.put(
    "/job-reports/{report_id}/resolve",
    response_model=ResponseSchema[dict],
    summary="A-06: Xử lý / Bỏ qua báo cáo job",
)
def resolve_report(
    report_id: int,
    body: ResolveReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    report = crud.resolve_job_report(db, report_id=report_id, new_status=body.status)
    return ResponseSchema(
        success=True,
        data={"id": report.id, "status": report.status.value},
        error=None,
        meta=None,
    )

@router.get(
    "/ai-monitoring/stats",
    response_model=ResponseSchema[AiMonitoringStats],
    summary="A-07: Thống kê AI hôm nay (calls, tokens, latency, error rate)",
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
    summary="A-07: Chart token usage theo giờ & error rate theo ngày",
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
    summary="A-07: DataTable log từng lần gọi AI",
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
    summary="A-07: Danh sách cấu hình cảnh báo AI",
)
def get_alert_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    configs = crud.get_ai_alert_configs(db)
    return ResponseSchema(success=True, data=configs, error=None, meta=None)


@router.put(
    "/ai-alert-configs/{config_id}",
    response_model=ResponseSchema[AiAlertConfigItem],
    summary="A-07: Bật/tắt hoặc chỉnh threshold cảnh báo AI",
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
