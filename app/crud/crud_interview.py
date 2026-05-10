from app.schemas.interview_schema import InterviewUpdateNote
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.core.enum import ApplicationStatusEnum, RoleEnum
from app.models.applications import Application
from app.models.candidate_profiles import CandidateProfile
from app.models.companies import CompanyMember
from app.models.interview import Interview
from app.models.job_posting import JobPosting
from app.models.user import User
from app.schemas.interview_schema import InterviewCreate, InterviewUpdate


def _ensure_hr(current_user: User) -> None:
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ HR mới được quản lý lịch phỏng vấn")


def _get_hr_company_id(db: Session, hr_user_id: int) -> int:
    member = db.query(CompanyMember).filter(CompanyMember.user_id == hr_user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="HR chưa thuộc công ty nào")
    return member.company_id


def _get_owned_application(db: Session, application_id: int, hr_user_id: int) -> Application:
    company_id = _get_hr_company_id(db, hr_user_id)
    application = (
        db.query(Application)
        .options(
            joinedload(Application.job_posting),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.user),
            joinedload(Application.interviews),
        )
        .join(JobPosting, JobPosting.id == Application.job_id)
        .filter(
            Application.id == application_id,
            JobPosting.company_id == company_id,
        )
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ ứng viên hoặc bạn không có quyền")
    return application


def create_interview(db: Session, current_user: User, detail_interview: InterviewCreate) -> Interview:
    _ensure_hr(current_user)
    application = _get_owned_application(db, detail_interview.application_id, current_user.id)

    existing = db.query(Interview).filter(Interview.application_id == detail_interview.application_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Hồ sơ này đã có lịch phỏng vấn, vui lòng dùng API cập nhật")

    new_interview = Interview(
        application_id=detail_interview.application_id,
        interviewer_id=current_user.id,
        interview_time=detail_interview.interview_time,
        meeting_link=detail_interview.meeting_link,
        location=detail_interview.location,
        notes=detail_interview.notes,
    )
    db.add(new_interview)
    application.status = ApplicationStatusEnum.interviewing
    db.flush()
    new_interview.application = application
    return new_interview


def update_interview(
    db: Session,
    current_user: User,
    interview_id: int,
    payload: InterviewUpdate,
) -> Interview:
    _ensure_hr(current_user)
    company_id = _get_hr_company_id(db, current_user.id)
    interview = (
        db.query(Interview)
        .join(Application, Application.id == Interview.application_id)
        .join(JobPosting, JobPosting.id == Application.job_id)
        .options(
            joinedload(Interview.application)
            .joinedload(Application.candidate_profile)
            .joinedload(CandidateProfile.user)
        )
        .filter(
            Interview.id == interview_id,
            JobPosting.company_id == company_id,
        )
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch phỏng vấn")

    interview.interview_time = payload.interview_time
    interview.meeting_link = payload.meeting_link
    interview.location = payload.location
    interview.notes = payload.notes
    interview.interviewer_id = current_user.id

    if interview.application.status != ApplicationStatusEnum.interviewing:
        interview.application.status = ApplicationStatusEnum.interviewing

    db.flush()
    return interview


def get_interview_by_id(db: Session, current_user: User, interview_id: int) -> Interview:
    if current_user.role == RoleEnum.hr_manager:
        company_id = _get_hr_company_id(db, current_user.id)
        interview = (
            db.query(Interview)
            .join(Application, Application.id == Interview.application_id)
            .join(JobPosting, JobPosting.id == Application.job_id)
            .options(
                joinedload(Interview.application)
                .joinedload(Application.candidate_profile)
                .joinedload(CandidateProfile.user)
            )
            .filter(
                Interview.id == interview_id,
                JobPosting.company_id == company_id,
            )
            .first()
        )
    else:
        interview = (
            db.query(Interview)
            .join(Application, Application.id == Interview.application_id)
            .join(CandidateProfile, CandidateProfile.id == Application.candidate_id)
            .options(
                joinedload(Interview.application)
                .joinedload(Application.candidate_profile)
                .joinedload(CandidateProfile.user)
            )
            .filter(
                Interview.id == interview_id,
                CandidateProfile.user_id == current_user.id,
            )
            .first()
        )

    if not interview:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch phỏng vấn")
    return interview


def list_interviews_by_application(db: Session, current_user: User, application_id: int) -> list[Interview]:
    if current_user.role == RoleEnum.hr_manager:
        _get_owned_application(db, application_id, current_user.id)
        interviews = (
            db.query(Interview)
            .filter(Interview.application_id == application_id)
            .order_by(Interview.interview_time.desc())
            .all()
        )
    else:
        interviews = (
            db.query(Interview)
            .join(Application, Application.id == Interview.application_id)
            .join(CandidateProfile, CandidateProfile.id == Application.candidate_id)
            .filter(
                Interview.application_id == application_id,
                CandidateProfile.user_id == current_user.id,
            )
            .order_by(Interview.interview_time.desc())
            .all()
        )
    return interviews


def list_my_interviews(db: Session, current_user: User) -> list[Interview]:
    if current_user.role == RoleEnum.hr_manager:
        company_id = _get_hr_company_id(db, current_user.id)
        interviews = (
            db.query(Interview)
            .join(Application, Application.id == Interview.application_id)
            .join(JobPosting, JobPosting.id == Application.job_id)
            .filter(JobPosting.company_id == company_id)
            .order_by(Interview.interview_time.asc())
            .all()
        )
    else:
        interviews = (
            db.query(Interview)
            .join(Application, Application.id == Interview.application_id)
            .join(CandidateProfile, CandidateProfile.id == Application.candidate_id)
            .filter(CandidateProfile.user_id == current_user.id)
            .order_by(Interview.interview_time.asc())
            .all()
        )
    return interviews

def update_interview_note(db: Session, current_user: User, application_id: int, payload: InterviewUpdateNote) -> Interview:
    _ensure_hr(current_user)
    company_id = _get_hr_company_id(db, current_user.id)
    interview = (
        db.query(Interview)
        .join(Application, Application.id == Interview.application_id)
        .join(JobPosting, JobPosting.id == Application.job_id)
        .options(
            joinedload(Interview.application)
            .joinedload(Application.candidate_profile)
            .joinedload(CandidateProfile.user)
        )
        .filter(
            Application.id == application_id,
            JobPosting.company_id == company_id,
        )
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch phỏng vấn")
    interview.notes = payload.notes
    db.flush()
    db.commit()
    db.refresh(interview)
    return interview