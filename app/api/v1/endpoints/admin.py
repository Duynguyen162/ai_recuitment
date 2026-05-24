from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.core.enum import CompanyVerificationStatusEnum, RoleEnum
from app.schemas.company_schema import CompanyResponse , VerifyRequest,LockRequest
from app.schemas.base_schema import ResponseSchema
from app.crud import crud_admin
from pydantic import BaseModel

router = APIRouter(tags=["Admin Companies"])

@router.get("/list_companies", response_model=ResponseSchema[list[CompanyResponse]])
def get_list_company(
    status: CompanyVerificationStatusEnum | None = Query(None, description="Lọc công ty theo trạng thái (pending, approved, rejected, locked)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin lấy danh sách công ty đang chờ duyệt giấy phép"""
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")
        
    list_companies = crud_admin.get_list_companies(db, status)
    
    return ResponseSchema(
        success=True,
        data=[CompanyResponse.model_validate(c) for c in list_companies],
        error=None,
        meta=None
    )

@router.put("/companies/{company_id}/verify", response_model=ResponseSchema[CompanyResponse])
def verify_company(
    company_id: int,
    request_in: VerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin Phê duyệt (is_approved=true) hoặc Từ chối (is_approved=false) công ty"""
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")

    updated_company = crud_admin.verify_company_license(
        db=db, 
        company_id=company_id, 
        admin_id=current_user.id, 
        status=request_in.status
    )

    return ResponseSchema(
        success=True,
        data=CompanyResponse.model_validate(updated_company),
        error=None,
        meta=None
    )

@router.put("/companies/{company_id}/lock", response_model=ResponseSchema[CompanyResponse])
def lock_company(
    company_id: int,
    request_in: LockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin Khóa (is_locked=true) hoặc Mở khóa (is_locked=false) toàn bộ hoạt động của công ty.
    Khi bị khóa, công ty sẽ không thể đăng tin tuyển dụng mới.
    """
    if current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Chỉ Admin mới có quyền truy cập")

    updated_company = crud_admin.lock_or_unlock_company(
        db=db, 
        company_id=company_id, 
        is_locked=request_in.is_locked
    )

    return ResponseSchema(
        success=True,
        data=CompanyResponse.model_validate(updated_company),
        error=None,
        meta=None
    )
