from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.core.enum import RoleEnum
from app.schemas.application_schema import ApplicationCreate, ApplicationResponse
from app.schemas.base_schema import ResponseSchema
from app.crud import crud_application
from app.services.ai_matching import run_ai_matching

router = APIRouter()

@router.post("/apply_job", response_model=ResponseSchema[ApplicationResponse])
def apply_for_job(
    request_in: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ứng viên nộp đơn ứng tuyển vào 1 job"""
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=404 , detail="Chỉ ứng viên mới được ứng tuyển")
    new_applied = crud_application.create_application(db, current_user.id, request_in.job_id)
    
    # AI phân tích sẽ chạy ngầm
    background_tasks.add_task(run_ai_matching, new_applied.id)

    return ResponseSchema(
        success=True, 
        data=ApplicationResponse.model_validate(new_applied),
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