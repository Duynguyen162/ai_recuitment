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
)
from app.schemas.base_schema import ResponseSchema

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
    summary="Ung vien apply vao job",
)
def apply_for_job(
    request_in: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ung vien nop don ung tuyen vao 1 job."""
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(
            status_code=403,
            detail="Chi ung vien moi duoc ung tuyen",
        )

    new_applied = crud_application.create_application(db, current_user.id, request_in)

    # AI phan tich se chay ngam
    # background_tasks.add_task(run_ai_matching, new_applied.id)
    _ = background_tasks

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
            applied_at=application.applied_at,
            cv_id=application.cv_upload_id,
            cv_name=application.cv_uploads.file_name if application.cv_uploads else None,
            cv_url=f"{settings.BASE_URL}/{application.cv_uploads.file_url}" if application.cv_uploads else None,
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
