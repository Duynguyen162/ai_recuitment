# app/crud/crud_job.py
from app.models.job_reports import JobReport
from fastapi import HTTPException
from sqlalchemy import String, and_, or_
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.enum import JobStatusEnum
from app.models.applications import Application
from app.models.candidate_profiles import CandidateProfile
from app.models.companies import CompanyMember
from app.models.job_posting import JobPosting
from app.models.saved_jobs import SaveJob
from app.schemas.job_schema import (
    JobPostingCreate,
    JobPostingUpdate,
    JobStatusActionEnum,
)


JOB_STATUS_TRANSITIONS: dict[JobStatusEnum, dict[JobStatusActionEnum, JobStatusEnum]] = {
    JobStatusEnum.draft: {
        JobStatusActionEnum.publish: JobStatusEnum.published,
    },
    JobStatusEnum.published: {
        JobStatusActionEnum.pause: JobStatusEnum.paused,
        JobStatusActionEnum.close: JobStatusEnum.closed,
    },
    JobStatusEnum.paused: {
        JobStatusActionEnum.publish: JobStatusEnum.published,
        JobStatusActionEnum.close: JobStatusEnum.closed,
    },
    JobStatusEnum.closed: {},
}


def get_list_job(
    db: Session,
    user_id: int,
    limit: int = 5,
    offset: int = 0,
):
    """Danh sách các job do HR tạo."""

    query = db.query(JobPosting).filter(JobPosting.created_by == user_id)
    total = query.count()

    jobs = (
        query
        .order_by(JobPosting.created_at.desc())
        .offset(max(0, offset))
        .limit(min(limit, 100))
        .all()
    )

    return jobs, total


def get_public_jobs(
    db: Session,
    keyword: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    tag: str | None = None,
    candidate_exp: int | None = None,
    limit: int = 20,
    offset: int = 0,
):
    """Tìm kiếm các job public với nhiều tiêu chí."""

    query = db.query(JobPosting).filter(JobPosting.status == JobStatusEnum.published)

    def escape_pattern(value: str) -> str:
        return value.replace("%", r"\%").replace("_", r"\_") if value else ""

    if keyword and keyword.strip():
        keywords = [word.strip() for word in keyword.split() if word.strip()]
        conditions = []

        for word in keywords:
            pattern = f"%{escape_pattern(word)}%"
            title_cond = func.unaccent(JobPosting.title).ilike(
                func.unaccent(pattern), escape="\\"
            )
            desc_cond = func.unaccent(JobPosting.description).ilike(
                func.unaccent(pattern), escape="\\"
            )
            tag_cond = func.unaccent(func.cast(JobPosting.tags, String)).ilike(
                func.unaccent(pattern), escape="\\"
            )
            conditions.append(or_(title_cond, desc_cond, tag_cond))

        query = query.filter(and_(*conditions))

    if tag and tag.strip() and not keyword:
        pattern = f"%{escape_pattern(tag.strip())}%"
        query = query.filter(
            func.unaccent(func.cast(JobPosting.tags, String)).ilike(
                func.unaccent(pattern), escape="\\"
            )
        )

    if candidate_exp is not None:
        query = query.filter(JobPosting.years_of_experience <= candidate_exp)

    if job_type:
        query = query.filter(JobPosting.job_type == job_type)

    if location and location.strip():
        pattern = f"%{escape_pattern(location.strip())}%"
        query = query.filter(
            func.unaccent(JobPosting.location).ilike(
                func.unaccent(pattern), escape="\\"
            )
        )

    total = query.count()
    jobs = (
        query.order_by(JobPosting.created_at.desc())
        .offset(max(0, offset))
        .limit(min(limit, 100))
        .all()
    )

    return jobs, total


def update_job_status(
    db: Session,
    job_id: int,
    company_id: int,
    action: JobStatusActionEnum,
):
    """Đổi trạng thái job theo state transition đã định nghĩa.

    Lưu ý: nếu job đang bị Admin khóa (locked_by_admin=True),
    HR không thể thay đổi trạng thái — chỉ Admin mới gỡ được.
    """
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.company_id == company_id,
    ).first()

    if not job:
        return None

    # ── Kiểm tra Admin lock ───────────────────────────────────────────
    if job.locked_by_admin:
        raise HTTPException(
            status_code=403,
            detail="Job đã bị Admin khóa. Vui lòng liên hệ quản trị viên để được hỗ trợ.",
        )

    next_status = JOB_STATUS_TRANSITIONS.get(job.status, {}).get(action)
    if not next_status:
        raise HTTPException(
            status_code=400,
            detail=f"Không thể '{action.value}' khi job đang ở trạng thái '{job.status.value}'",
        )

    job.status = next_status
    db.commit()
    db.refresh(job)
    return job


def create_job_posting(db: Session, company_id: int, user_id: int, job_in: JobPostingCreate):
    """Lưu job mới vào CSDL, mặc định tạo ở trạng thái draft."""
    data = job_in.model_dump()
    if isinstance(data.get("tags"), str):
        import json

        data["tags"] = json.loads(data["tags"])

    data.pop("status", None)

    try:
        db_job = JobPosting(
            **data,
            company_id=company_id,
            created_by=user_id,
            status=JobStatusEnum.draft,
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception:
        db.rollback()
        raise


def update_job_crud(db: Session, job_id: int, job: JobPostingUpdate, user_id: int):
    """Chỉ cho phép cập nhật nội dung khi job còn draft."""
    company_member = db.query(CompanyMember).filter(CompanyMember.user_id == user_id).first()
    if not company_member:
        raise HTTPException(status_code=404, detail="Bạn chưa thuộc công ty nào")

    job_db = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.company_id == company_member.company_id,
    ).first()

    if not job_db:
        raise HTTPException(status_code=404, detail="Không tìm thấy job hoặc bạn không có quyền")

    if job_db.status != JobStatusEnum.draft:
        raise HTTPException(
            status_code=400,
            detail="Chỉ job ở trạng thái draft mới được sửa nội dung",
        )

    update_data = job.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(job_db, key, value)

    db.commit()
    db.refresh(job_db)
    return job_db


def get_proposed_jobs(db: Session, offset: int = 0, limit: int = 20):
    """Lấy danh sách job mới nhất để hiển thị."""
    query = db.query(JobPosting).filter(JobPosting.status == JobStatusEnum.published)
    total = query.count()

    jobs = (
        query
        .order_by(JobPosting.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return jobs, total


def is_save(db: Session, job_id: int, user_id: int):
    """Kiểm tra ứng viên đã lưu job hay chưa."""
    job = db.query(SaveJob).join(CandidateProfile).filter(
        SaveJob.job_id == job_id,
        CandidateProfile.user_id == user_id,
    ).first()
    return job is not None


def get_job_by_id(db: Session, job_id: int, user_id: int | None):
    """Lấy thông tin chi tiết của một job."""
    job = (
        db.query(JobPosting)
        .options(joinedload(JobPosting.company))
        .filter(JobPosting.id == job_id)
        .first()
    )

    if not job:
        return None

    applied = False
    save = False

    if user_id:
        applied = has_applied(db, user_id, job_id)
        save = is_save(db, job_id, user_id)

    return job, applied, save


def delete_job(db: Session, job_id: int):
    """Xóa job đã đăng."""
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy job này")

    db.delete(job)
    db.commit()
    return None


def has_applied(db: Session, user_id: int, job_id: int):
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not profile:
        return False

    application = db.query(Application).filter(
        Application.candidate_id == profile.id,
        Application.job_id == job_id,
    ).first()

    return application is not None


def list_save_job(db: Session, user_id: int):
    result = db.query(JobPosting).join(SaveJob).join(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).all()

    return result


def save_job(db: Session, job_id: int, user_id: int):
    """Lưu job yêu thích hoặc đang chú ý."""
    candidate = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not candidate:
        raise HTTPException(status_code=404, detail="Chưa có profile")

    existing = db.query(SaveJob).filter(
        SaveJob.candidate_id == candidate.id,
        SaveJob.job_id == job_id,
    ).first()
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()

    if existing:
        raise HTTPException(status_code=400, detail="Job đã được lưu trước đó")

    try:
        save = SaveJob(candidate_id=candidate.id, job_id=job_id)
        db.add(save)
        db.commit()
        db.refresh(save)
        return save, job
    except Exception:
        db.rollback()
        raise


def delete_saved_job(db: Session, user_id: int, job_id: int):
    save_job = db.query(SaveJob).join(CandidateProfile).filter(
        CandidateProfile.user_id == user_id,
        SaveJob.job_id == job_id,
    ).first()
    db.delete(save_job)
    db.commit()
    return None

def report_job(db: Session, job_id: int, user_id: int, reason: str | None = None):
    try:
        report = JobReport(job_id=job_id, reported_by=user_id, reason=reason)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    except Exception:
        db.rollback()
        raise
    
