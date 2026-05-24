import os
from app.core.config import settings
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import crud_application
from app.core.enum import RoleEnum
from app.db.database import get_db
from app.models.user import User
from app.schemas.application_schema import (
    ApplicationCreate,
    ApplicationResponse,
    CandidateAppliedResponse,
    ChangeStatusRequest,
    PaginatedCandidatesResponse,
    CandidatesStatsResponse,
    InterviewDetailResponse,
    ApplicationDetailResponse,
    CandidateProfileForHrResponse,
    AiScoreStatusResponse,
    AiRequeueResponse,
)
from app.schemas.base_schema import ResponseSchema
from app.services.ai_matching import (
    enqueue_ai_matching_job,
    enqueue_and_process_ai_matching,
    process_ai_matching_queue,
)

router = APIRouter()


@router.get(
    "/get_apply_job",
    response_model=ResponseSchema[List[ApplicationResponse]],
    tags=["Candidate Jobs"],
    summary="Ứng viên lấy danh sách job đã apply",
)
def get_apply_job(
    db: Session = Depends(get_db),
    curent_user: User = Depends(get_current_user),
):
    """Lấy danh sách job ứng viên đã apply."""
    if curent_user.role != RoleEnum.candidate:
        raise HTTPException(
            status_code=404,
            detail="Chỉ ứng viên mới có chức năng này",
        )

    applications = crud_application.list_job_apply(db, curent_user.id)

    data = [
        ApplicationResponse(
            id=app.id,
            job_id=app.job_id,
            job_title=app.job_posting.title,
            company_name=app.job_posting.company.name,
            status=app.status.value,
            applied_at=app.applied_at,
            cv_id=app.cv_upload_id,
            cv_type=app.cv_type,
            cv_name=app.cv_uploads.file_name if app.cv_uploads else "Không có CV",
            cv_url=f"{settings.BASE_URL}/{app.cv_uploads.file_url}" if app.cv_uploads else None,
        )
        for app in applications
    ]

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta=None,
    )


@router.post(
    "/apply_job",
    response_model=ResponseSchema[ApplicationResponse],
    tags=["Candidate Jobs"],
    summary="Ứng viên apply vào job",
)
def apply_for_job(
    request_in: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ứng viên nộp đơn ứng tuyển vào 1 job."""
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(
            status_code=403,
            detail="Chỉ ứng viên mới được ứng tuyển",
        )

    new_applied = crud_application.create_application(db, current_user.id, request_in)

    # AI matching chay ngam qua queue de tranh block API apply
    background_tasks.add_task(enqueue_and_process_ai_matching, new_applied.id)

    return ResponseSchema(
        success=True,
        data=ApplicationResponse(
            id=new_applied.id,
            job_id=new_applied.job_id,
            job_title=new_applied.job_posting.title,
            company_name=new_applied.job_posting.company.name,
            status=new_applied.status.value,
            applied_at=new_applied.applied_at,
            cv_type=new_applied.cv_type,
            cv_id=new_applied.cv_upload_id,
            cv_name=new_applied.cv_uploads.file_name if new_applied.cv_uploads else "",
            cv_url=f"{settings.BASE_URL}/{new_applied.cv_uploads.file_url}" if new_applied.cv_uploads else None,
        ),
        error=None,
        meta=None,
    )


@router.delete(
    "/delete_apply",
    tags=["Candidate Jobs"],
    summary="Ung vien huy don apply",
)
def delete_apply_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(
            status_code=404,
            detail="Chi ung vien moi co the dung chuc nang nay",
        )

    crud_application.delete_application(db, current_user.id, job_id)

    return ResponseSchema(
        success=True,
        data=job_id,
        error=None,
        meta=None,
    )


@router.get(
    "/list_candidate/{job_id}",
    response_model=ResponseSchema[List[CandidateAppliedResponse]],
    tags=["HR Applications"],
    summary="HR lay danh sach ung vien da apply theo job",
)
def get_list_candidate_apply_by_job(
    job_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """HR lay danh sach ung vien da apply vao 1 job, co phan trang."""
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(
            status_code=403,
            detail="Chi HR moi co the dung chuc nang nay",
        )

    offset = (page - 1) * page_size
    applications, total, job = crud_application.list_candidates_applied_by_job(
        db=db,
        hr_user_id=current_user.id,
        job_id=job_id,
        limit=page_size,
        offset=offset,
    )

    data = [
        CandidateAppliedResponse(
            application_id=application.id,
            candidate_id=application.candidate_profile.id,
            full_name=application.candidate_profile.full_name,
            email=application.candidate_profile.user.email,
            phone=application.candidate_profile.phone,
            avatar_url=application.candidate_profile.avatar_url,
            years_of_experience=application.candidate_profile.years_of_experience,
            skill_tags=application.candidate_profile.skill_tags or [],
            status=application.status.value,
            cv_type=application.cv_type,
            applied_at=application.applied_at,
            cv_id=application.cv_upload_id,
            cv_name=application.cv_uploads.file_name if application.cv_uploads else None,
            cv_url=f"{settings.BASE_URL}/{application.cv_uploads.file_url}" if application.cv_uploads else None,
            job_title=application.job_posting.title if application.job_posting else None,
        )
        for application in applications
    ]

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta={
            "job_id": job.id,
            "job_title": job.title,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    )


@router.get(
    "/hr/{application_id}/cv/view",
    tags=["HR Applications"],
    summary="HR xem CV cua ung vien",
)
def view_cv_by_hr(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """API xem CV cua HR."""
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(
            status_code=404,
            detail="Chi nha tuyen dung moi dung duoc api nay",
        )

    cv = crud_application.get_application_by_id(db, application_id)
    file_path = cv.file_url

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File khong ton tai tren server")

    return FileResponse(
        path=file_path,
        filename=cv.file_name,
        headers={"Access-Control-Expose-Headers": "Content-Disposition"},
    )


@router.put(
    "/{application_id}/status",
    response_model=ResponseSchema[ApplicationResponse],
    tags=["HR Applications"],
    summary="HR cap nhat trang thai don ung tuyen",
)
def change_status(
    application_id: int,
    status: ChangeStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = crud_application.change_status(db, application_id, status, current_user)

    return ResponseSchema(
        success=True,
        data=ApplicationResponse(
            id=res.id,
            job_id=res.job_id,
            job_title=res.job_posting.title,
            company_name=res.job_posting.company.name,
            status=res.status.value,
            applied_at=res.applied_at,
            cv_type=res.cv_type,
            cv_id=res.cv_upload_id,
            cv_name=res.cv_uploads.file_name if res.cv_uploads else "",
            cv_url=f"{settings.BASE_URL}/{res.cv_uploads.file_url}" if res.cv_uploads else None,
        ),
        error=None,
        meta=None,
    )


@router.get(
    "/hr/candidates",
    response_model=PaginatedCandidatesResponse,
    tags=["HR Applications"],
    summary="HR lấy danh sách các ứng viên đã apply vào công ty",
)
def get_hr_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    job_id: int | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(
            status_code=403,
            detail="Chỉ HR mới có thể sử dụng chức năng này",
        )

    applications, total = crud_application.list_hr_candidates(
        db=db,
        hr_user_id=current_user.id,
        page=page,
        page_size=page_size,
        job_id=job_id,
        status=status,
        search=search,
    )

    data = [
        CandidateAppliedResponse(
            application_id=application.id,
            candidate_id=application.candidate_profile.id,
            full_name=application.candidate_profile.full_name,
            email=application.candidate_profile.user.email,
            phone=application.candidate_profile.phone,
            avatar_url=application.candidate_profile.avatar_url,
            years_of_experience=application.candidate_profile.years_of_experience,
            skill_tags=application.candidate_profile.skill_tags or [],
            status=application.status.value,
            cv_type=application.cv_type,
            applied_at=application.applied_at,
            cv_id=application.cv_upload_id,
            cv_name=application.cv_uploads.file_name if application.cv_uploads else None,
            cv_url=f"{settings.BASE_URL}/{application.cv_uploads.file_url}" if application.cv_uploads else None,
            job_title=application.job_posting.title if application.job_posting else None,
        )
        for application in applications
    ]

    return PaginatedCandidatesResponse(
        data=data,
        total=total,
    )


@router.get(
    "/hr/candidates/stats",
    response_model=CandidatesStatsResponse,
    tags=["HR Applications"],
    summary="HR lấy thống kê số lượng ứng viên",
)
def get_hr_candidates_stats(
    job_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(
            status_code=403,
            detail="Chỉ HR mới có thể dùng chức năng này",
        )

    stats = crud_application.get_hr_candidates_stats(
        db=db,
        hr_user_id=current_user.id,
        job_id=job_id,
    )

    return CandidatesStatsResponse(**stats)


@router.get(
    "/hr/{application_id}/candidate_profile",
    response_model=ResponseSchema[CandidateProfileForHrResponse],
    tags=["HR Applications"],
    summary="HR xem profile đầy đủ của ứng viên theo đơn ứng tuyển",
)
def get_candidate_profile_by_application_for_hr(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(
            status_code=403,
            detail="Chỉ HR mới có thể dùng chức năng này",
        )

    profile_data = crud_application.get_candidate_profile_by_application_for_hr(
        db=db,
        hr_user_id=current_user.id,
        application_id=application_id,
    )

    return ResponseSchema(
        success=True,
        data=CandidateProfileForHrResponse(**profile_data),
        error=None,
        meta=None,
    )


@router.get(
    "/hr/{application_id}/ai_score_status",
    response_model=ResponseSchema[AiScoreStatusResponse],
    tags=["HR Applications"],
    summary="HR xem trang thai cham diem AI theo application",
)
def get_ai_score_status_for_hr(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(
            status_code=403,
            detail="Chi HR moi co the dung chuc nang nay",
        )

    data = crud_application.get_ai_score_status_for_hr(
        db=db,
        hr_user_id=current_user.id,
        application_id=application_id,
    )

    return ResponseSchema(success=True, data=AiScoreStatusResponse(**data), error=None, meta=None)


@router.post(
    "/hr/{application_id}/ai-score/requeue",
    response_model=ResponseSchema[AiRequeueResponse],
    tags=["HR Applications"],
    summary="HR yeu cau cham lai AI cho 1 application",
)
def requeue_ai_score_for_application_by_hr(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chi HR moi co the dung chuc nang nay")

    application = crud_application.validate_hr_can_access_application(
        db=db,
        hr_user_id=current_user.id,
        application_id=application_id,
    )
    enqueue_ai_matching_job(application.id)
    background_tasks.add_task(process_ai_matching_queue, 1)

    return ResponseSchema(
        success=True,
        data=AiRequeueResponse(queued_count=1, skipped_count=0, application_ids=[application.id]),
        error=None,
        meta=None,
    )


@router.post(
    "/hr/candidates/{candidate_id}/ai-score/requeue",
    response_model=ResponseSchema[AiRequeueResponse],
    tags=["HR Applications"],
    summary="HR requeue cham diem AI cho cac don cua 1 ung vien",
)
def requeue_ai_score_for_candidate_by_hr(
    candidate_id: int,
    only_missing_score: bool = True,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chi HR moi co the dung chuc nang nay")

    application_ids = crud_application.list_hr_candidate_application_ids_for_requeue(
        db=db,
        hr_user_id=current_user.id,
        candidate_id=candidate_id,
        only_missing_score=only_missing_score,
    )

    queued = 0
    for app_id in application_ids:
        enqueue_ai_matching_job(app_id)
        queued += 1

    if queued > 0 and background_tasks is not None:
        background_tasks.add_task(process_ai_matching_queue, min(queued, 10))

    return ResponseSchema(
        success=True,
        data=AiRequeueResponse(
            queued_count=queued,
            skipped_count=0,
            application_ids=application_ids,
        ),
        error=None,
        meta={"only_missing_score": only_missing_score},
    )


@router.get(
    "/candidate/{application_id}/interview",
    response_model=ResponseSchema[InterviewDetailResponse],
    tags=["Candidate Jobs"],
    summary="Ứng viên xem chi tiết lịch phỏng vấn",
)
def get_candidate_interview(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.crud import crud_interview
    
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(
            status_code=403,
            detail="Chỉ ứng viên mới xem được thông tin này",
        )
    
    interviews = crud_interview.list_interviews_by_application(db, current_user, application_id)
    if not interviews:
        raise HTTPException(status_code=404, detail="Chưa có lịch phỏng vấn")
        
    interview = interviews[0]
    
    mode = "online" if interview.meeting_link else "offline"
    
    data = InterviewDetailResponse(
        interview_time=interview.interview_time,
        location=interview.location,
        meeting_link=interview.meeting_link,
        mode=mode,
        notes=interview.notes,
    )
    
    return ResponseSchema(success=True, data=data)


@router.get(
    "/get_application_detail",
    response_model=ResponseSchema[ApplicationDetailResponse],
    tags=["Candidate Jobs"],
    summary="Ứng viên lấy thông tin chi tiết lịch hẹn phỏng vấn hoặc lý do từ chối",
)
def get_application_detail_endpoint(
    job_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(
            status_code=403,
            detail="Chỉ ứng viên mới xem được thông tin này",
        )

    detail_data = crud_application.get_application_detail(db, current_user.id, job_id)

    return ResponseSchema(
        success=True,
        data=ApplicationDetailResponse(**detail_data),
        error=None,
        meta=None,
    )
