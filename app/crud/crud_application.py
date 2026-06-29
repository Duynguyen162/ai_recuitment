from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func

from app.core.enum import ApplicationStatusEnum, CvTypeEnum, JobStatusEnum, RoleEnum
from app.models.ai_matching_scores import AiMatchingScore
from app.models.ai_matching_jobs import AiMatchingJob
from app.models.applications import Application
from app.models.candidate_details import CVUpload
from app.models.candidate_profiles import CandidateProfile
from app.models.companies import CompanyMember
from app.models.job_posting import JobPosting
from app.models.user import User
from app.models.interview import Interview
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
            detail="Tin tuyển dụng không tồn tại hoặc đã đóng",
        )

    candidate = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate profile chưa tồn tại")

    # Kiem tra xem ung vien da duoc nhan vao cong ty nay chua (va chua nghi viec)
    hired_in_company = db.query(Application).join(JobPosting, Application.job_id == JobPosting.id).filter(
        Application.candidate_id == candidate.id,
        JobPosting.company_id == job.company_id,
        Application.status == ApplicationStatusEnum.hired
    ).first()

    if hired_in_company:
        raise HTTPException(
            status_code=400,
            detail="Bạn đang làm việc tại công ty này nên không thể ứng tuyển thêm.",
        )

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
            detail="Bạn đã nộp hồ sơ cho công việc này.",
        )

    cv_upload_id = request_in.cv_id
    if request_in.cv_type == CvTypeEnum.profile:
        cv_upload_id = None
    else:
        if not cv_upload_id:
            raise HTTPException(
                status_code=422,
                detail="cv_id là bắt buộc khi cv_type='uploaded_cv'",
            )
        cv_record = db.query(CVUpload).filter(
            CVUpload.id == cv_upload_id,
            CVUpload.candidate_id == candidate.id,
        ).first()
        if not cv_record:
            raise HTTPException(
                status_code=404,
                detail="CV upload không tồn tại hoặc không thuộc về ứng viên",
            )

    new_applied = Application(
        job_id=request_in.job_id,
        candidate_id=candidate.id,
        cv_type=request_in.cv_type,
        cv_upload_id=cv_upload_id,
    )

    db.add(new_applied)
    db.commit()
    db.refresh(new_applied)

    return new_applied


def delete_application(db: Session, user_id: int, job_id: int):
    """Xóa đơn ứng tuyển khỏi database."""
    candidate_profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not candidate_profile:
        raise HTTPException(status_code=404, detail="Chưa có profile")

    # Tìm đơn ứng tuyển mới nhất cho job này
    del_applied = db.query(Application).filter(
        Application.candidate_id == candidate_profile.id,
        Application.job_id == job_id,
    ).order_by(Application.applied_at.desc()).first()

    if not del_applied:
        raise HTTPException(
            status_code=404,
            detail="Chưa ứng tuyển vào công việc này",
        )

    # Chỉ cho phép xóa nếu đang ở trạng thái chờ xử lý hoặc đang xem xét
    if del_applied.status not in {
        ApplicationStatusEnum.pending,
        ApplicationStatusEnum.review,
        ApplicationStatusEnum.withdrawn,
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Hồ sơ đang trong quá trình xử lý chuyên sâu, không thể hủy"
            ),
        )

    db.delete(del_applied)
    db.commit()
    return True


def create_ai_matching_score(db: Session, application_id: int, score_data: dict):
    """Luu ket qua cham diem cua AI vao database."""
    existing = db.query(AiMatchingScore).filter(
        AiMatchingScore.application_id == application_id
    ).first()

    if existing:
        existing.score = score_data.get("score")
        existing.strengths = score_data.get("strengths", [])
        existing.weaknesses = score_data.get("weaknesses", [])
        existing.explanation = score_data.get("explanation")
        db.commit()
        db.refresh(existing)
        return existing

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
            joinedload(Application.job_posting),
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

def list_hr_candidates(
    db: Session,
    hr_user_id: int,
    page: int = 1,
    page_size: int = 10,
    job_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
):
    member = db.query(CompanyMember).filter(CompanyMember.user_id == hr_user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn chưa thuộc công ty nào")

    query = (
        db.query(Application)
        .join(JobPosting, Application.job_id == JobPosting.id)
        .options(
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.user),
            joinedload(Application.cv_uploads),
            joinedload(Application.job_posting),
            joinedload(Application.interviews),
        )
        .filter(JobPosting.company_id == member.company_id)
    )

    if job_id:
        query = query.filter(Application.job_id == job_id)

    if status and status != "all":
        if status == "applied":
            status = "pending"
            
        try:
            enum_status = ApplicationStatusEnum(status)
            query = query.filter(Application.status == enum_status)
        except ValueError:
            pass

    if search:
        search_term = f"%{search.lower()}%"
        query = (
            query.join(CandidateProfile, Application.candidate_id == CandidateProfile.id)
            .join(User, CandidateProfile.user_id == User.id)
            .outerjoin(CVUpload, Application.cv_upload_id == CVUpload.id)
            .filter(
                or_(
                    CandidateProfile.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    CVUpload.file_name.ilike(search_term),
                )
            )
        )

    total = query.count()
    offset = (page - 1) * page_size

    applications = (
        query.order_by(Application.applied_at.desc())
        .offset(max(0, offset))
        .limit(min(page_size, 100))
        .all()
    )

    return applications, total

def get_hr_candidates_stats(
    db: Session,
    hr_user_id: int,
    job_id: int | None = None,
):
    member = db.query(CompanyMember).filter(CompanyMember.user_id == hr_user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn chưa thuộc công ty nào")

    query = (
        db.query(Application.status, func.count(Application.id))
        .join(JobPosting, Application.job_id == JobPosting.id)
        .filter(JobPosting.company_id == member.company_id)
    )

    if job_id:
        query = query.filter(Application.job_id == job_id)

    stats_raw = query.group_by(Application.status).all()
    
    stats_dict = {status_enum.value: count for status_enum, count in stats_raw}
    
    total = sum(stats_dict.values())
    
    return {
        "all": total,
        "applied": stats_dict.get(ApplicationStatusEnum.pending.value, 0),
        "interviewing": stats_dict.get(ApplicationStatusEnum.interviewing.value, 0),
        "hired": stats_dict.get(ApplicationStatusEnum.hired.value, 0),
        "rejected": stats_dict.get(ApplicationStatusEnum.rejected.value, 0),
        "withdrawn": stats_dict.get(ApplicationStatusEnum.withdrawn.value, 0),
        "left_company": stats_dict.get(ApplicationStatusEnum.left_company.value, 0),
    }


def get_application_detail(db: Session, user_id: int, job_id: int) -> dict:
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ ứng viên")

    application = (
        db.query(Application)
        .options(
            joinedload(Application.job_posting).joinedload(JobPosting.company),
            joinedload(Application.job_posting).joinedload(JobPosting.creator),
            joinedload(Application.interviews).joinedload(Interview.interviewer),
        )
        .filter(
            Application.candidate_id == candidate.id,
            Application.job_id == job_id,
        )
        .order_by(Application.applied_at.desc())
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn ứng tuyển")

    res_data = {
        "job_id": str(application.job_id),
        "status": application.status.value,
        "rejection_reason": None,
        "rejected_at": None,
        "interview_mode": None,
        "interview_time": None,
        "location": None,
        "meeting_link": None,
        "notes": None,
        "hr_contact_name": None,
        "hr_contact_email": None,
        "hr_contact_phone": None,
    }

    company_name = application.job_posting.company.name if application.job_posting and application.job_posting.company else "Công ty"
    hr_email = application.job_posting.creator.email if application.job_posting and application.job_posting.creator else "hr@company.com"

    if application.status == ApplicationStatusEnum.rejected:
        rejection_reason = getattr(application, 'rejection_reason', None)
        if not rejection_reason:
            rejection_reason = "Cảm ơn bạn đã quan tâm đến vị trí này. Tuy nhiên, sau khi xem xét kỹ lưỡng hồ sơ, chúng tôi nhận thấy kinh nghiệm hiện tại của bạn chưa hoàn toàn phù hợp với định hướng dự án sắp tới. Chúc bạn nhiều thành công trên con đường sự nghiệp!"
        
        rejected_at = getattr(application, 'rejected_at', None) or application.update_at
        
        res_data.update({
            "rejection_reason": rejection_reason,
            "rejected_at": rejected_at,
            "hr_contact_name": f"Bộ phận Tuyển dụng - {company_name}",
            "hr_contact_email": hr_email,
        })
    elif application.status in {ApplicationStatusEnum.interviewing, ApplicationStatusEnum.hired}:
        interviews = application.interviews
        if interviews:
            interview = sorted(interviews, key=lambda i: i.interview_time, reverse=True)[0]
            mode = "online" if interview.meeting_link else "offline"
            interviewer_email = interview.interviewer.email if interview.interviewer else hr_email
            
            res_data.update({
                "interview_mode": mode,
                "interview_time": interview.interview_time,
                "location": interview.location,
                "meeting_link": interview.meeting_link,
                "notes": interview.notes,
                "hr_contact_name": f"Bộ phận Tuyển dụng - {company_name}",
                "hr_contact_email": interviewer_email,
                "hr_contact_phone": None,
            })
        else:
            res_data.update({
                "notes": "Lịch phỏng vấn đang được nhà tuyển dụng cập nhật.",
                "hr_contact_name": f"Bộ phận Tuyển dụng - {company_name}",
                "hr_contact_email": hr_email,
            })
    else:
        res_data.update({
            "notes": "Hồ sơ của bạn đã được tiếp nhận và đang trong quá trình đánh giá. Chúng tôi sẽ liên hệ lại qua Email hoặc Số điện thoại nếu hồ sơ phù hợp.",
            "hr_contact_name": f"Bộ phận Tuyển dụng - {company_name}",
            "hr_contact_email": hr_email,
        })

    return res_data


def get_candidate_profile_by_application_for_hr(
    db: Session,
    hr_user_id: int,
    application_id: int,
) -> dict:
    member = db.query(CompanyMember).filter(
        CompanyMember.user_id == hr_user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Ban chua thuoc cong ty nao")

    application = (
        db.query(Application)
        .join(JobPosting, Application.job_id == JobPosting.id)
        .options(
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.user),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.experiences),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.educations),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.certifications),
            joinedload(Application.interviews),
        )
        .filter(
            Application.id == application_id,
            JobPosting.company_id == member.company_id,
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay don ung tuyen hoac ban khong co quyen truy cap",
        )

    if application.cv_type != CvTypeEnum.profile:
        raise HTTPException(
            status_code=400,
            detail="Don ung tuyen nay khong su dung profile, vui long xem CV upload",
        )

    profile = application.candidate_profile
    if not profile or not profile.user:
        raise HTTPException(status_code=404, detail="Khong tim thay du lieu ung vien")

    interview_data = None
    if application.interviews:
        latest_interview = sorted(application.interviews, key=lambda i: i.interview_time, reverse=True)[0]
        mode = "online" if latest_interview.meeting_link else "offline"
        interview_data = {
            "id": latest_interview.id,
            "interview_time": latest_interview.interview_time,
            "location": latest_interview.location,
            "meeting_link": latest_interview.meeting_link,
            "mode": mode,
            "notes": latest_interview.notes,
        }

    return {
        "full_name": profile.full_name,
        "email": profile.user.email,
        "phone": profile.phone,
        "address": None,
        "date_of_birth": None,
        "summary": profile.bio,
        "skills": profile.skill_tags or [],
        "experiences": [
            {
                "company_name": exp.company_name,
                "job_title": exp.job_title,
                "description": exp.description,
            }
            for exp in (profile.experiences or [])
        ],
        "educations": [
            {
                "institution_name": edu.institution_name,
                "major": edu.major,
                "degree": edu.degree,
            }
            for edu in (profile.educations or [])
        ],
        "certifications": [
            {
                "name": cert.name,
                "issuer": cert.issuer,
            }
            for cert in (profile.certifications or [])
        ],
        "interview": interview_data,
    }


def get_ai_score_status_for_hr(
    db: Session,
    hr_user_id: int,
    application_id: int,
) -> dict:
    member = db.query(CompanyMember).filter(CompanyMember.user_id == hr_user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Ban chua thuoc cong ty nao")

    application = (
        db.query(Application)
        .join(JobPosting, Application.job_id == JobPosting.id)
        .filter(
            Application.id == application_id,
            JobPosting.company_id == member.company_id,
        )
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay don ung tuyen hoac ban khong co quyen truy cap",
        )

    score = db.query(AiMatchingScore).filter(
        AiMatchingScore.application_id == application_id
    ).first()
    if score:
        return {
            "application_id": application_id,
            "status": "done",
            "score": float(score.score) if score.score is not None else None,
            "strengths": score.strengths or [],
            "weaknesses": score.weaknesses or [],
            "explanation": score.explanation,
            "error_message": None,
        }

    queue_job = db.query(AiMatchingJob).filter(
        AiMatchingJob.application_id == application_id
    ).first()
    if not queue_job:
        return {
            "application_id": application_id,
            "status": "not_queued",
            "score": None,
            "strengths": [],
            "weaknesses": [],
            "explanation": None,
            "error_message": None,
        }

    return {
        "application_id": application_id,
        "status": queue_job.status.value,
        "score": None,
        "strengths": [],
        "weaknesses": [],
        "explanation": None,
        "error_message": queue_job.error_message,
    }


def validate_hr_can_access_application(
    db: Session,
    hr_user_id: int,
    application_id: int,
) -> Application:
    member = db.query(CompanyMember).filter(CompanyMember.user_id == hr_user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Ban chua thuoc cong ty nao")

    application = (
        db.query(Application)
        .join(JobPosting, Application.job_id == JobPosting.id)
        .filter(
            Application.id == application_id,
            JobPosting.company_id == member.company_id,
        )
        .first()
    )
    if not application:
        raise HTTPException(
            status_code=404,
            detail="Khong tim thay don ung tuyen hoac ban khong co quyen truy cap",
        )
    return application


def list_hr_candidate_application_ids_for_requeue(
    db: Session,
    hr_user_id: int,
    candidate_id: int,
    only_missing_score: bool = True,
) -> list[int]:
    member = db.query(CompanyMember).filter(CompanyMember.user_id == hr_user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Ban chua thuoc cong ty nao")

    query = (
        db.query(Application.id)
        .join(JobPosting, Application.job_id == JobPosting.id)
        .filter(
            Application.candidate_id == candidate_id,
            JobPosting.company_id == member.company_id,
        )
    )

    if only_missing_score:
        query = query.outerjoin(
            AiMatchingScore,
            AiMatchingScore.application_id == Application.id,
        ).filter(AiMatchingScore.id.is_(None))

    return [row[0] for row in query.all()]
