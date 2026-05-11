"""
CRUD logic cho các API Admin:
  - A-01: Dashboard Stats & Charts
  - A-04/A-05: Quản lý & Duyệt Công Ty
  - A-06: Kiểm Duyệt Tin Tuyển Dụng
  - A-07: Giám Sát Hệ Thống AI
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func, cast, Date, Integer
from sqlalchemy.orm import Session, joinedload

from app.core.enum import (
    ApplicationStatusEnum,
    CompanyVerificationStatusEnum,
    JobStatusEnum,
    RoleEnum,
    VerificationLogStatusEnum,
)
from app.models.ai_logs import AiAlertConfig, AiLog
from app.models.ai_matching_scores import AiMatchingScore
from app.models.applications import Application
from app.models.companies import Company, CompanyMember, CompanyVerification, CompanyDocument
from app.models.job_posting import JobPosting
from app.models.job_reports import JobReport, JobReportStatusEnum
from app.models.user import User


# ─────────────────────────────────────────────────────────────────────────────
# A-01: Dashboard Stats
# ─────────────────────────────────────────────────────────────────────────────

def get_admin_dashboard_stats(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(User).count()
    total_companies = db.query(Company).count()
    total_jobs = db.query(JobPosting).count()
    total_applications = db.query(Application).count()

    active_users_today = db.query(User).filter(
        User.updated_at >= today_start
    ).count()

    pending_companies = db.query(Company).filter(
        Company.verification_status == CompanyVerificationStatusEnum.pending
    ).count()

    # Job bị "flag" = job đã bị pause hoặc có báo cáo chưa xử lý
    flagged_jobs = db.query(JobPosting).filter(
        JobPosting.status == JobStatusEnum.paused
    ).count()

    pending_reports = db.query(JobReport).filter(
        JobReport.status == JobReportStatusEnum.pending
    ).count()

    return {
        "total_users": total_users,
        "total_companies": total_companies,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "active_users_today": active_users_today,
        "pending_companies": pending_companies,
        "flagged_jobs": flagged_jobs,
        "pending_reports": pending_reports,
    }


def get_admin_dashboard_charts(db: Session, days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    date_from = now - timedelta(days=days)

    # Chart 1: New users by day
    rows = (
        db.query(
            cast(User.created_at, Date).label("date"),
            func.count(User.id).label("count"),
        )
        .filter(User.created_at >= date_from)
        .group_by(cast(User.created_at, Date))
        .order_by(cast(User.created_at, Date))
        .all()
    )
    new_users_by_day = [{"date": str(r.date), "count": r.count} for r in rows]

    # Chart 2: Role distribution
    candidate_count = db.query(User).filter(User.role == RoleEnum.candidate).count()
    hr_count = db.query(User).filter(User.role == RoleEnum.hr_manager).count()
    role_distribution = {"candidate": candidate_count, "hr_manager": hr_count}

    # Chart 3: Applications by status
    status_rows = (
        db.query(Application.status, func.count(Application.id).label("count"))
        .group_by(Application.status)
        .all()
    )
    applications_by_status = [
        {"status": r.status.value, "count": r.count} for r in status_rows
    ]

    return {
        "new_users_by_day": new_users_by_day,
        "role_distribution": role_distribution,
        "applications_by_status": applications_by_status,
    }


# ─────────────────────────────────────────────────────────────────────────────
# A-04/A-05: Companies
# ─────────────────────────────────────────────────────────────────────────────

def get_admin_companies(
    db: Session,
    status: Optional[CompanyVerificationStatusEnum] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple:
    query = db.query(Company)
    if status:
        query = query.filter(Company.verification_status == status)

    total = query.count()
    companies = (
        query.order_by(Company.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for c in companies:
        hr_count = db.query(CompanyMember).filter(CompanyMember.company_id == c.id).count()
        result.append({
            "id": c.id,
            "name": c.name,
            "logo_url": c.logo_url,
            "website": c.website,
            "description": c.description,
            "size": c.size,
            "verification_status": c.verification_status,
            "created_at": c.created_at,
            "hr_member_count": hr_count,
        })
    return result, total


def get_admin_company_detail(db: Session, company_id: int) -> dict:
    company = (
        db.query(Company)
        .options(
            joinedload(Company.verifications),
            joinedload(Company.documents),
        )
        .filter(Company.id == company_id)
        .first()
    )
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    return {
        "id": company.id,
        "name": company.name,
        "logo_url": company.logo_url,
        "website": company.website,
        "description": company.description,
        "size": company.size,
        "verification_status": company.verification_status,
        "created_at": company.created_at,
        "verification_history": [
            {
                "id": v.id,
                "status": v.status,
                "license_url": v.license_url,
                "reviewed_by": v.reviewed_by,
                "created_at": v.created_at,
            }
            for v in sorted(company.verifications, key=lambda x: x.created_at, reverse=True)
        ],
        "documents": [
            {
                "id": d.id,
                "file_url": d.file_url,
                "status": d.status,
                "created_at": d.created_at,
            }
            for d in company.documents
        ],
    }


def admin_update_company_status(
    db: Session,
    company_id: int,
    new_status: CompanyVerificationStatusEnum,
    admin_id: int,
    reason: Optional[str] = None,
) -> Company:
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    company.verification_status = new_status

    # Cập nhật verification record pending nếu có
    if new_status in (
        CompanyVerificationStatusEnum.approved,
        CompanyVerificationStatusEnum.rejected,
    ):
        pending_verification = (
            db.query(CompanyVerification)
            .filter(
                CompanyVerification.company_id == company_id,
                CompanyVerification.status == VerificationLogStatusEnum.pending,
            )
            .first()
        )
        if pending_verification:
            pending_verification.reviewed_by = admin_id
            pending_verification.status = (
                VerificationLogStatusEnum.approved
                if new_status == CompanyVerificationStatusEnum.approved
                else VerificationLogStatusEnum.rejected
            )

    db.commit()
    db.refresh(company)
    return company


# ─────────────────────────────────────────────────────────────────────────────
# A-06: Job Reports & Flagged Jobs
# ─────────────────────────────────────────────────────────────────────────────

def get_flagged_jobs(db: Session, page: int = 1, page_size: int = 20) -> tuple:
    """Job đang bị pause được xem là đã bị flag."""
    query = db.query(JobPosting).filter(JobPosting.status == JobStatusEnum.paused)
    total = query.count()
    jobs = (
        query.options(joinedload(JobPosting.company))
        .order_by(JobPosting.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = [
        {
            "id": j.id,
            "title": j.title,
            "company_name": j.company.name if j.company else "",
            "status": j.status.value,
            "flagged_reason": None,  # Placeholder — có thể thêm field sau
            "created_at": j.created_at,
        }
        for j in jobs
    ]
    return result, total


def admin_update_job_status(db: Session, job_id: int, action: str) -> JobPosting:
    """
    action: 'allow' → published, 'pause' → paused, 'close' → closed
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy job")

    action_map = {
        "allow": JobStatusEnum.published,
        "pause": JobStatusEnum.paused,
        "close": JobStatusEnum.closed,
    }
    if action not in action_map:
        raise HTTPException(status_code=400, detail=f"Hành động không hợp lệ: {action}")

    job.status = action_map[action]
    db.commit()
    db.refresh(job)
    return job


def get_job_reports(db: Session, page: int = 1, page_size: int = 20) -> tuple:
    query = db.query(JobReport).options(
        joinedload(JobReport.job).joinedload(JobPosting.company),
        joinedload(JobReport.reporter),
    )
    total = query.count()
    reports = (
        query.order_by(JobReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = [
        {
            "id": r.id,
            "job_id": r.job_id,
            "job_title": r.job.title if r.job else "",
            "company_name": r.job.company.name if r.job and r.job.company else "",
            "reporter_email": r.reporter.email if r.reporter else None,
            "reason": r.reason,
            "status": r.status.value,
            "created_at": r.created_at,
        }
        for r in reports
    ]
    return result, total


def resolve_job_report(db: Session, report_id: int, new_status: str) -> JobReport:
    report = db.query(JobReport).filter(JobReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo")

    if new_status not in ("resolved", "dismissed"):
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    report.status = JobReportStatusEnum(new_status)
    db.commit()
    db.refresh(report)
    return report

def get_ai_monitoring_stats(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    logs_today = db.query(AiLog).filter(AiLog.created_at >= today_start).all()

    total_calls = len(logs_today)
    total_tokens = sum(l.tokens_used or 0 for l in logs_today)
    error_count = sum(1 for l in logs_today if l.is_error)

    latencies = [l.processing_time_ms for l in logs_today if l.processing_time_ms is not None]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0
    error_rate = round((error_count / total_calls * 100), 2) if total_calls > 0 else 0.0

    return {
        "total_calls_today": total_calls,
        "total_tokens_today": total_tokens,
        "avg_latency_ms": avg_latency,
        "error_rate_percent": error_rate,
    }


def get_ai_logs(
    db: Session,
    service_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    is_error: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple:
    query = db.query(AiLog)
    if service_type:
        query = query.filter(AiLog.service_type == service_type)
    if date_from:
        query = query.filter(AiLog.created_at >= date_from)
    if date_to:
        query = query.filter(AiLog.created_at <= date_to)
    if is_error is not None:
        query = query.filter(AiLog.is_error == is_error)

    total = query.count()
    logs = (
        query.order_by(AiLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return logs, total


def get_ai_chart_data(db: Session, days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    date_from = now - timedelta(days=days)

    # Token usage by hour (24h cuối)
    last_24h = now - timedelta(hours=24)
    token_rows = (
        db.query(
            func.date_trunc("hour", AiLog.created_at).label("hour"),
            func.coalesce(func.sum(AiLog.tokens_used), 0).label("tokens"),
        )
        .filter(AiLog.created_at >= last_24h)
        .group_by(func.date_trunc("hour", AiLog.created_at))
        .order_by(func.date_trunc("hour", AiLog.created_at))
        .all()
    )
    token_usage_by_hour = [
        {"hour": r.hour.strftime("%H:00"), "tokens": int(r.tokens)} for r in token_rows
    ]

    # Error rate by day
    error_rows = (
        db.query(
            cast(AiLog.created_at, Date).label("date"),
            func.count(AiLog.id).label("total"),
            func.sum(
                func.cast(AiLog.is_error, Integer)
            ).label("errors"),
        )
        .filter(AiLog.created_at >= date_from)
        .group_by(cast(AiLog.created_at, Date))
        .order_by(cast(AiLog.created_at, Date))
        .all()
    )
    error_rate_by_day = [
        {
            "date": str(r.date),
            "error_rate": round((r.errors or 0) / r.total * 100, 2) if r.total > 0 else 0.0,
        }
        for r in error_rows
    ]

    return {
        "token_usage_by_hour": token_usage_by_hour,
        "error_rate_by_day": error_rate_by_day,
    }


def get_ai_alert_configs(db: Session) -> List[AiAlertConfig]:
    return db.query(AiAlertConfig).order_by(AiAlertConfig.id).all()


def update_ai_alert_config(
    db: Session,
    config_id: int,
    is_active: Optional[bool],
    threshold: Optional[int],
) -> AiAlertConfig:
    config = db.query(AiAlertConfig).filter(AiAlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình cảnh báo")
    if is_active is not None:
        config.is_active = is_active
    if threshold is not None:
        config.threshold = threshold
    db.commit()
    db.refresh(config)
    return config
