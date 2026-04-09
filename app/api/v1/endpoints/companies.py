from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.companies import CompanyDocument, CompanyMember
from app.models.user import User
from app.api.deps import  get_current_user
from app.core.enum import RoleEnum
from app.schemas.company_schema import CompanyCreate, CompanyDocumentCreate, CompanyDocumentResponse, CompanyResponse , CompanyRegisterRequest, CompanyUpdate
from app.schemas.base_schema import ResponseSchema
from app.crud import crud_company

router = APIRouter()

@router.post("/register_company", response_model=ResponseSchema[CompanyResponse])
def register_company(
    request_in: CompanyRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    API cho HR đăng ký công ty mới kèm giấy phép kinh doanh.
    """
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403,detail="Chỉ nhà tuyển dụng mới được đăng kí công ty")
    
    existing_company = crud_company.get_company_by_hr(db, current_user.id)
    if existing_company:
        raise HTTPException(status_code=400,detail = "Bạn đã thuộc về 1 công ty, không thể đăng ký thêm")
    
    company_data = CompanyCreate(**request_in.model_dump(exclude={"license_url"}))
    try:
        new_company = crud_company.register_company(db, current_user.id, company_data, request_in.license_url)
        return ResponseSchema(
            success=True,
            data = CompanyResponse.model_validate(new_company),
            error=None,
            meta=None
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()

        raise HTTPException(status_code=400,detail=f"lỗi khi đăng kí công ty")
    
@router.put("/company",response_model=ResponseSchema[CompanyResponse])
def update_my_company(
    company_in: CompanyUpdate,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ Nhà tuyển dụng mới được dùng tính năng này")

    # Lấy công ty của HR ra
    company = crud_company.get_company_by_hr(db, current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="Bạn chưa đăng ký công ty nào")

    # Gọi CRUD để update
    updated_company = crud_company.update_company_info(db, company, company_in)

    return ResponseSchema(
        success=True,
        data=CompanyResponse.model_validate(updated_company),
        error=None,
        meta=None
    )


@router.get("/my_company", response_model=ResponseSchema[CompanyResponse])
def get_my_company(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy thông tin công ty của HR đang đăng nhập
    """
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ Nhà tuyển dụng mới có công ty")

    company = crud_company.get_company_by_hr(db, current_user.id)
    if not company:
        raise HTTPException(status_code=404, detail="Bạn chưa đăng ký công ty nào")

    return ResponseSchema(
        success=True,
        data=CompanyResponse.model_validate(company),
        error=None,
        meta=None
    )    

# @router.post("/leave")
# def leave_company(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     if current_user.role != RoleEnum.hr_manager:
#         raise HTTPException(status_code=403, detail="Chỉ Nhà tuyển dụng mới có thể rời công ty")
    
#     # Tìm xem HR này thuộc công ty nào
#     member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
#     if not member:
#         raise HTTPException(status_code=404, detail="Bạn không thuộc công ty nào")
        
#     crud_company.remove_member_from_company(db, current_user.id, member.company_id)
#     return ResponseSchema(success=True, data="Đã rời khỏi công ty")

@router.get("/my_company/documents", response_model=ResponseSchema[list[CompanyDocumentResponse]])
def get_my_company_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách tài liệu/chính sách của công ty HR đang quản lý"""
    # 1. Tìm công ty của HR
    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn không thuộc công ty nào")

    docs = crud_company.get_company_documents(db, member.company_id)
    return ResponseSchema(
        success=True,
        data=[CompanyDocumentResponse.model_validate(d) for d in docs],
        error=None,
        meta=None
    )

@router.post("/my_company/documents", response_model=ResponseSchema[CompanyDocumentResponse])
def add_company_document(
    doc_in: CompanyDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """HR thêm một tài liệu mới (sau khi đã upload file lấy URL)"""
    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn không thuộc công ty nào")

    new_doc = crud_company.create_company_document(
        db=db, 
        company_id=member.company_id, 
        user_id=current_user.id, 
        doc_in=doc_in
    )
    return ResponseSchema(success=True, data=CompanyDocumentResponse.model_validate(new_doc))

@router.delete("/my_company/documents/{doc_id}")
def remove_company_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Xóa tài liệu công ty"""
    # Kiểm tra quyền: Tài liệu phải thuộc về công ty của HR này
    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    doc = db.query(CompanyDocument).filter(CompanyDocument.id == doc_id).first()
    
    if not doc or not member or doc.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa tài liệu này")

    crud_company.delete_company_document(db, doc_id)
    return ResponseSchema(success=True, data="Đã xóa tài liệu thành công")