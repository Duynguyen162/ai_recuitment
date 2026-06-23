# app/crud/crud_job.py
from app.api.v1.endpoints import admin_dashboard
from app.core.enum import RoleEnum
from app.models.user import User
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
    status: JobStatusEnum | None = None,
    search: str | None = None,
    limit: int = 5,
    offset: int = 0,
):
    """Danh sách các job do HR tạo."""

    member = db.query(CompanyMember).filter(CompanyMember.user_id == user_id).first()
    if member:
        query = db.query(JobPosting).filter(
            or_(
                JobPosting.created_by == user_id,
                JobPosting.company_id == member.company_id,
            )
        )
    else:
        query = db.query(JobPosting).filter(JobPosting.created_by == user_id)

    if status:
        query = query.filter(JobPosting.status == status)

    if search and search.strip():
        search_str = search.strip()
        pattern = f"%{search_str.replace('%', r'\%').replace('_', r'\_')}%"
        query = query.filter(
            or_(
                func.unaccent(JobPosting.title).ilike(func.unaccent(pattern), escape="\\"),
                func.unaccent(JobPosting.location).ilike(func.unaccent(pattern), escape="\\"),
                func.unaccent(func.cast(JobPosting.tags, String)).ilike(func.unaccent(pattern), escape="\\"),
                func.unaccent(JobPosting.requirements).ilike(func.unaccent(pattern), escape="\\"),
            )
        )

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
    user_id: int | None = None,
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

    if user_id and jobs:
        saved_job_ids = db.query(SaveJob.job_id).join(CandidateProfile).filter(
            CandidateProfile.user_id == user_id,
            SaveJob.job_id.in_([j.id for j in jobs])
        ).all()
        saved_ids_set = {r[0] for r in saved_job_ids}
        for job in jobs:
            job.is_save = job.id in saved_ids_set

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

    if job.locked_by_admin:
        raise HTTPException(
            status_code=403,
            detail="Job đã bị Admin khóa. Vui lòng liên hệ quản trị viên để được hỗ trợ.",
        )

    # 1. Lấy danh sách các action hợp lệ cho trạng thái hiện tại
    current_status = job.status
    allowed_transitions = JOB_STATUS_TRANSITIONS.get(current_status, {})
    print(allowed_transitions)
    # 2. Kiểm tra action request có nằm trong danh sách cho phép không
    if action not in allowed_transitions:
        valid_actions = [a.value for a in allowed_transitions.keys()]
        raise HTTPException(
            status_code=400,
            detail=(
                f"Không thể thực hiện '{action.value}' khi job đang ở trạng thái '{current_status.value}'. "
                f"Các thao tác hợp lệ lúc này: {valid_actions if valid_actions else 'Không có'}"
            ),
        )

    # 3. Thực hiện chuyển đổi trạng thái
    next_status = allowed_transitions[action]
    job.status = next_status

    db.commit()
    db.refresh(job)
    return job


def create_job_posting(db: Session, company_id: int, user_id: int, job_in: JobPostingCreate):
    """Lưu job mới vào CSDL, mặc định tạo ở trạng thái published nếu không truyền status."""
    data = job_in.model_dump()
    if isinstance(data.get("tags"), str):
        import json

        data["tags"] = json.loads(data["tags"])

    status = data.pop("status", JobStatusEnum.published)
    if status is None:
        status = JobStatusEnum.published

    try:
        db_job = JobPosting(
            **data,
            company_id=company_id,
            created_by=user_id,
            status=status,
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


def get_proposed_jobs(db: Session, user_id: int | None = None, offset: int = 0, limit: int = 20):
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

    if user_id and jobs:
        # Lấy danh sách ID các job mà user này đã lưu
        saved_job_ids = db.query(SaveJob.job_id).join(CandidateProfile).filter(
            CandidateProfile.user_id == user_id,
            SaveJob.job_id.in_([j.id for j in jobs])
        ).all()
        
        saved_ids_set = {r[0] for r in saved_job_ids}
        
        for job in jobs:
            job.is_save = job.id in saved_ids_set

    return jobs, total

def get_job_match_cv(
    db: Session,
    current_user: User,
    offset: int = 0,
    limit: int = 20
):
    """Lấy job phù hợp bằng cách search theo tag"""

    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới dùng được API này")

    candidate = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()

    if not candidate:
        raise HTTPException(status_code=404, detail="Bạn chưa có CV")

    candidate_tags = candidate.skill_tags or []

    if not candidate_tags:
        return [], 0

    job_query = db.query(JobPosting).filter(
        JobPosting.status == JobStatusEnum.published
    )

    def normalize(value: str):
        return value.lower().replace(" ", "")
    conditions = []

    for tag in candidate_tags:
        norm_tag = normalize(tag)
        pattern = f"%{norm_tag}%"
        #tạo điều kiệu cho job tag (job.tags LIKE "%reactjs%", "%nodejs%")
        tag_cond = func.replace(
            func.lower(func.cast(JobPosting.tags, String)),
            " ",
            ""
        ).ilike(pattern)

        conditions.append(tag_cond)
        
    job_query = job_query.filter(or_(*conditions))

    total = job_query.count()
    jobs = (
        job_query
        .order_by(JobPosting.created_at.desc())
        .offset(max(0, offset))
        .limit(min(limit, 100))
        .all()
    )

    if jobs:
        saved_job_ids = db.query(SaveJob.job_id).join(CandidateProfile).filter(
            CandidateProfile.user_id == current_user.id,
            SaveJob.job_id.in_([j.id for j in jobs])
        ).all()
        saved_ids_set = {r[0] for r in saved_job_ids}
        for job in jobs:
            job.is_save = job.id in saved_ids_set

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
    app_status = None

    if user_id:
        applied, app_status = has_applied(db, user_id, job_id)
        save = is_save(db, job_id, user_id)

    return job, applied, save, app_status


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
        return False, None

    application = db.query(Application).filter(
        Application.candidate_id == profile.id,
        Application.job_id == job_id,
    ).order_by(Application.applied_at.desc()).first()

    if application:
        return True, application.status.value
    
    return False, None


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
    
