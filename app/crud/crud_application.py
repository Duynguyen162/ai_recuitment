from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.enum import ApplicationStatusEnum, JobStatusEnum, RoleEnum
from app.models.ai_matching_scores import AiMatchingScore
from app.models.applications import Application
from app.models.candidate_details import CVUpload
from app.models.candidate_profiles import CandidateProfile
from app.models.companies import CompanyMember
from app.models.job_posting import JobPosting
from app.models.user import User
from app.schemas.application_schema import ApplicationCreate, ChangeStatusRequest


APPLICATION_STATUS_TRANSITIONS: dict[ApplicationStatusEnum, set[ApplicationStatusEnum]] = {
    ApplicationStatusEnum.pending: {
        ApplicationStatusEnum.review,
        ApplicationStatusEnum.interviewing,
        ApplicationStatusEnum.hired,
        ApplicationStatusEnum.rejected,
        ApplicationStatusEnum.withdrawn,
    },
    ApplicationStatusEnum.review: {
        ApplicationStatusEnum.interviewing,
        ApplicationStatusEnum.hired,
        ApplicationStatusEnum.rejected,
        ApplicationStatusEnum.withdrawn,
    },
    ApplicationStatusEnum.interviewing: {
        ApplicationStatusEnum.hired,
        ApplicationStatusEnum.rejected,
        ApplicationStatusEnum.withdrawn,
    },
    ApplicationStatusEnum.hired: {
        ApplicationStatusEnum.left_company,
    },
    ApplicationStatusEnum.rejected: set(),
    ApplicationStatusEnum.withdrawn: set(),
    ApplicationStatusEnum.left_company: set(),
}


def _ensure_valid_application_status_transition(
    current_status: ApplicationStatusEnum,
    next_status: ApplicationStatusEnum,
) -> None:
    if current_status == next_status:
        return

    allowed_statuses = APPLICATION_STATUS_TRANSITIONS.get(current_status, set())
    if next_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Khong the chuyen trang thai tu '{current_status.value}' "
                f"sang '{next_status.value}'"
            ),
        )


def create_application(db: Session, user_id: int, request_in: ApplicationCreate):
    """Nop ho so ung tuyen."""
    job = db.query(JobPosting).filter(
        JobPosting.id == request_in.job_id,
        JobPosting.status == JobStatusEnum.published,
    ).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Tin tuyen dung khong ton tai hoac da dong",
        )

    candidate = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile chua ton tai")

    applied_job = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == request_in.job_id,
    ).order_by(Application.applied_at.desc()).first()

    if applied_job and applied_job.status not in {
        ApplicationStatusEnum.withdrawn,
        ApplicationStatusEnum.left_company,
        ApplicationStatusEnum.rejected,
    }:
        raise HTTPException(
            status_code=400,
            detail="Ban da nop ho so cho job nay roi",
        )

    new_applied = Application(
        job_id=request_in.job_id,
        candidate_id=candidate.id,
        cv_type=request_in.cv_type,
        cv_upload_id=request_in.cv_id,
    )

    db.add(new_applied)
    db.commit()
    db.refresh(new_applied)

    return new_applied


def delete_application(db: Session, user_id: int, job_id: int):
    """Huy don ung tuyen nhung van giu lich su."""
    candidate_profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not candidate_profile:
        raise HTTPException(status_code=404, detail="Chua co profile")

    del_applied = db.query(Application).filter(
        Application.candidate_id == candidate_profile.id,
        Application.job_id == job_id,
    ).first()

    if not del_applied:
        raise HTTPException(
            status_code=404,
            detail="Chua ung tuyen vao cong ty nay, khong the huy",
        )

    if del_applied.status in {
        ApplicationStatusEnum.hired,
        ApplicationStatusEnum.left_company,
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Ho so da duoc tuyen hoac da ghi nhan roi cong ty, "
                "khong the huy"
            ),
        )

    if del_applied.status == ApplicationStatusEnum.withdrawn:
        return None

    _ensure_valid_application_status_transition(
        del_applied.status,
        ApplicationStatusEnum.withdrawn,
    )
    del_applied.status = ApplicationStatusEnum.withdrawn

    db.commit()
    db.refresh(del_applied)
    return None


def create_ai_matching_score(db: Session, application_id: int, score_data: dict):
    """Luu ket qua cham diem cua AI vao database."""
    new_score = AiMatchingScore(
        application_id=application_id,
        score=score_data.get("score"),
        strengths=score_data.get("strengths", []),
        weaknesses=score_data.get("weaknesses", []),
        explanation=score_data.get("explanation"),
    )
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    return new_score


def list_job_apply(db: Session, user_id: int):
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not profile:
        return []

    list_job = (
        db.query(Application)
        .options(
            joinedload(Application.job_posting).joinedload(JobPosting.company),
            joinedload(Application.cv_uploads),
        )
        .filter(Application.candidate_id == profile.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    return list_job


def list_application(db: Session):
    db.query(Application).filter()


def list_candidates_applied_by_job(
    db: Session,
    hr_user_id: int,
    job_id: int,
    limit: int = 10,
    offset: int = 0,
):
    member = db.query(CompanyMember).filter(
        CompanyMember.user_id == hr_user_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Ban chua thuoc cong ty nao")

    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.company_id == member.company_id,
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay job hoac ban khong co quyen xem danh sach ung vien",
        )

    query = (
        db.query(Application)
        .options(
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.user),
            joinedload(Application.cv_uploads),
        )
        .filter(Application.job_id == job_id)
    )

    total = query.count()

    applications = (
        query
        .order_by(Application.applied_at.desc())
        .offset(max(0, offset))
        .limit(min(limit, 100))
        .all()
    )

    return applications, total, job


def get_application_by_id(db: Session, application_id: int):
    cv = db.query(CVUpload).join(Application).filter(
        Application.id == application_id,
    ).first()

    if not cv:
        raise HTTPException(status_code=404, detail="CV khong ton tai")

    return cv


def change_status(
    db: Session,
    application_id: int,
    status_change: ChangeStatusRequest,
    curent_user: User,
):
    """Thay doi trang thai don ung tuyen."""
    if curent_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=404, detail="Chi HR moi duoc thay doi")

    app = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not app:
        raise HTTPException(status_code=404, detail="Khong thay ung vien")

    next_status = status_change.status
    _ensure_valid_application_status_transition(app.status, next_status)
    app.status = next_status

    db.commit()
    db.refresh(app)

    return app
