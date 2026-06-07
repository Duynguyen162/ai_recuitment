import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import crud_company
from app.core.enum import DocumentStatus, RoleEnum
from app.db.database import get_db
from app.models.companies import Company, CompanyDocument, CompanyMember
from app.models.user import User
from app.schemas.base_schema import ResponseSchema
from app.schemas.company_schema import (
    CompanyCreate,
    CompanyDocumentCreate,
    CompanyDocumentResponse,
    CompanyRegisterRequest,
    CompanyResponse,
    CompanyUpdate,
    ResubmitVerificationRequest,
)
from app.services.rag_service import process_and_store_document, resolve_document_path

router = APIRouter(tags=["HR Companies"])


@router.post("/register_company", response_model=ResponseSchema[CompanyResponse])
def register_company(
    request_in: CompanyRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    API cho HR đăng ký công ty mới kèm giấy phép kinh doanh.
    """
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ nhà tuyển dụng mới được đăng kí công ty")

    existing_company = crud_company.get_company_by_hr(db, current_user.id)
    if existing_company:
        raise HTTPException(status_code=400, detail="Bạn đã thuộc về 1 công ty, không thể đăng ký thêm")

    company_data = CompanyCreate(**request_in.model_dump(exclude={"license_url"}))
    try:
        new_company = crud_company.register_company(db, current_user.id, company_data, request_in.license_url)
        return ResponseSchema(
            success=True,
            data=CompanyResponse.model_validate(new_company),
            error=None,
            meta=None,
        )
    except Exception:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=400, detail="Lỗi khi đăng kí công ty")


@router.put("/company", response_model=ResponseSchema[CompanyResponse])
def update_my_company(
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ nhà tuyển dụng mới được dùng tính năng này")

    company = crud_company.get_company_by_hr(db, current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="Bạn chưa đăng ký công ty nào")

    update_data = company_in.model_dump(exclude_unset=True, exclude={"is_vip"})
    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)

    return ResponseSchema(
        success=True,
        data=CompanyResponse.model_validate(company),
        error=None,
        meta=None,
    )


@router.get("/my_company", response_model=ResponseSchema[CompanyResponse])
def get_my_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy thông tin công ty của HR đang đăng nhập.
    """
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ nhà tuyển dụng mới có công ty")

    company = crud_company.get_company_by_hr(db, current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="Bạn chưa đăng ký công ty nào")

    return ResponseSchema(
        success=True,
        data=CompanyResponse.model_validate(company),
        error=None,
        meta=None,
    )


@router.get("/my_company/documents", response_model=ResponseSchema[list[CompanyDocumentResponse]])
def get_my_company_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách tài liệu/chính sách của công ty HR đang quản lý."""
    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn không thuộc công ty nào")

    docs = crud_company.get_company_documents(db, member.company_id)
    return ResponseSchema(
        success=True,
        data=[CompanyDocumentResponse.model_validate(d) for d in docs],
        error=None,
        meta=None,
    )


@router.post("/my_company/documents", response_model=ResponseSchema[CompanyDocumentResponse])
def add_company_document(
    doc_in: CompanyDocumentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """HR thêm tài liệu. Bắt buộc phải là VIP."""
    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn không thuộc công ty nào")

    company = db.query(Company).filter(Company.id == member.company_id).first()
    if not company.is_vip:
        raise HTTPException(
            status_code=403,
            detail="Tính năng Đào tạo AI nội bộ chỉ dành cho tài khoản VIP. Vui lòng nâng cấp!",
        )

    new_doc = crud_company.create_company_document(
        db=db,
        company_id=member.company_id,
        user_id=current_user.id,
        doc_in=doc_in,
    )

    file_path = resolve_document_path(doc_in.file_url)
    if os.path.exists(file_path):
        background_tasks.add_task(
            process_and_store_document,
            new_doc.id,
            file_path,
            member.company_id,
        )
    else:
        new_doc.status = DocumentStatus.failed
        db.commit()

    return ResponseSchema(success=True, data=CompanyDocumentResponse.model_validate(new_doc))


@router.delete("/my_company/documents/{doc_id}")
def remove_company_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa tài liệu công ty."""
    crud_company.delete_company_document(db, doc_id, current_user.id)
    return ResponseSchema(success=True, data="Đã xóa tài liệu thành công")


@router.post("/my_company/documents/{doc_id}/retry")
def retry_document_rag(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(CompanyDocument).filter(CompanyDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")

    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member or doc.company_id != member.company_id:
        raise HTTPException(403, "Không có quyền")

    if doc.status != DocumentStatus.failed:
        raise HTTPException(400, "Chỉ retry tài liệu bị lỗi")

    file_path = resolve_document_path(doc.file_url)
    if not os.path.exists(file_path):
        raise HTTPException(400, f"Không tìm thấy file gốc để retry: {file_path}")

    doc.status = DocumentStatus.processing
    db.commit()

    background_tasks.add_task(
        process_and_store_document,
        doc.id,
        file_path,
        member.company_id,
    )
    return ResponseSchema(
        success=True,
        data="Đã retry xử lý tài liệu",
        error=None,
        meta=None,
    )

@router.post("/my_company/resubmit_verification", response_model=ResponseSchema[CompanyResponse])
def resubmit_verification(
    request_in: ResubmitVerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cho phép HR gửi yêu cầu duyệt lại giấy phép kinh doanh (khi bị từ chối)
    """
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ nhà tuyển dụng mới có quyền thực hiện")

    company = crud_company.get_company_by_hr(db, current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="Bạn chưa thuộc công ty nào")

    updated_company = crud_company.resubmit_company_verification(
        db=db,
        company_id=company.id,
        license_url=request_in.license_url
    )

    return ResponseSchema(
        success=True,
        data=CompanyResponse.model_validate(updated_company),
        error=None,
        meta=None
    )

