from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.candidate_profiles import CandidateProfile
from app.models.user import User
from app.api.deps import get_current_user
from app.core.enum import RoleEnum
from app.schemas.application_schema import ApplicationCreate, ApplicationResponse
from app.schemas.base_schema import ResponseSchema
from app.crud import crud_application
from app.services.ai_matching import run_ai_matching

router = APIRouter()

@router.get("/get_apply_job",response_model=ResponseSchema[List[ApplicationResponse]])
def get_apply_job(
    db:Session = Depends(get_db),
    curent_user:User =Depends(get_current_user),
):
    """lấy danh sách job đã ứng tuyển"""
    if curent_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=404,detail="Chỉ ứng viên mới có chức năng này")
    
    applications = crud_application.list_job_apply(db, curent_user.id)

    data = [
        ApplicationResponse(
            id=str(app.id),
            job_id=str(app.job_id),
            job_title=app.job_posting.title,
            company_name=app.job_posting.company.name,
            status=app.status.name.upper(),
            applied_at=app.applied_at,
            cv_id=str(app.cv_upload_id) if app.cv_upload_id else None,
            cv_type=app.cv_type,
            cv_name=app.cv_uploads.file_name if app.cv_uploads else "khong có",
        )
        for app in applications
    ]

    return ResponseSchema(
        success=True,
        data= data,
        error=None,
        meta=None
    )

@router.post("/apply_job", response_model=ResponseSchema[ApplicationResponse])
def apply_for_job(
    request_in: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ứng viên nộp đơn ứng tuyển vào 1 job"""
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403 , detail="Chỉ ứng viên mới được ứng tuyển")
        
    new_applied = crud_application.create_application(db, current_user.id, request_in)
    
    # AI phân tích sẽ chạy ngầm
    # background_tasks.add_task(run_ai_matching, new_applied.id)

    return ResponseSchema(
        success=True, 
        data=ApplicationResponse(
            id=new_applied.id,
            job_id=new_applied.job_id,
            job_title=new_applied.job_posting.title,
            company_name=new_applied.job_posting.company.name,
            status=new_applied.status,
            applied_at=new_applied.applied_at,
            cv_type = new_applied.cv_type,
            cv_id=new_applied.cv_upload_id, 
            cv_name=new_applied.cv_uploads.file_name if new_applied.cv_uploads else "" 
        ),
        error=None,
        meta=None
    )

@router.delete("/delete_apply")
def delete_apply_job(
    job_id:int,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=404, detail="Chỉ ứng viên mới có thể dùng chức năng này")
    
    crud_application.delete_application(db , current_user.id , job_id)

    return ResponseSchema(
        success=True,
        data=job_id,
        error=None,
        meta=None
    )