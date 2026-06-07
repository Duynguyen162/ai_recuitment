from enum import Enum
from sqlalchemy.orm import Session
from app.models.companies import Company, CompanyVerification
from app.core.enum import CompanyVerificationStatusEnum, VerificationLogStatusEnum
from fastapi import HTTPException


def get_list_companies(db: Session, status: CompanyVerificationStatusEnum | None = None):
    """Lấy danh sách các công ty theo trạng thái"""
    query = db.query(Company)
    if status:
        query = query.filter(Company.verification_status == status)

    return query.all()

def verify_company_license(db:Session , company_id:int, admin_id: int , status: VerificationLogStatusEnum, reason: str | None = None):
    """Duyệt hoặc Từ chối giấy phép kinh doanh của công ty"""
    # 1. Tìm công ty
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
    
    # 2. Tìm yêu cầu xác minh đang pending của công ty này
    verification = db.query(CompanyVerification).filter(
        CompanyVerification.company_id == company_id,
        CompanyVerification.status == VerificationLogStatusEnum.pending
    ).first()

    if not verification:
            raise HTTPException(status_code=400, detail="Công ty này không có giấy phép nào đang chờ duyệt")
    
    # 3. Cập nhật trạng thái
    if status == VerificationLogStatusEnum.approved:
        company.verification_status = CompanyVerificationStatusEnum.approved
        verification.status = VerificationLogStatusEnum.approved
    elif status == VerificationLogStatusEnum.rejected:
        company.verification_status = CompanyVerificationStatusEnum.rejected
        verification.status = VerificationLogStatusEnum.rejected
        
    verification.reviewed_by = admin_id
    
    # Gửi thông báo đến tất cả thành viên của công ty
    from app.crud.crud_notification import create_notification
    from app.models.companies import CompanyMember

    members = db.query(CompanyMember).filter(CompanyMember.company_id == company_id).all()
    for member in members:
        if status == VerificationLogStatusEnum.approved:
            create_notification(
                db=db,
                user_id=member.user_id,
                title="Giấy phép kinh doanh đã được duyệt",
                body=f"Giấy phép kinh doanh của công ty '{company.name}' đã được phê duyệt thành công bởi Ban quản trị."
            )
        elif status == VerificationLogStatusEnum.rejected:
            create_notification(
                db=db,
                user_id=member.user_id,
                title="Giấy phép kinh doanh bị từ chối",
                body=f"Giấy phép kinh doanh của công ty '{company.name}' đã bị từ chối duyệt. Lý do: {reason or 'Không có lý do cụ thể'}."
            )

    db.commit()
    db.refresh(company)
    
    return company
    
def lock_or_unlock_company(db: Session, company_id: int, status: CompanyVerificationStatusEnum, reason: str|None=None):
    """Khóa hoặc Mở khóa một công ty"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    if status == CompanyVerificationStatusEnum.locked:
        company.verification_status = CompanyVerificationStatusEnum.locked
        reason = reason
    elif status == CompanyVerificationStatusEnum.approved:
        company.verification_status = CompanyVerificationStatusEnum.approved
        reason = None
    else:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    # Gửi thông báo đến tất cả thành viên của công ty
    from app.crud.crud_notification import create_notification
    from app.models.companies import CompanyMember

    members = db.query(CompanyMember).filter(CompanyMember.company_id == company_id).all()
    for member in members:
        if status == CompanyVerificationStatusEnum.locked:
            create_notification(
                db=db,
                user_id=member.user_id,
                title="Công ty của bạn đã bị khóa tài khoản",
                body=f"Công ty '{company.name}' đã bị khóa bởi Ban quản trị. Lý do: {reason or 'Không có lý do cụ thể'}."
            )
        elif status == CompanyVerificationStatusEnum.approved:
            create_notification(
                db=db,
                user_id=member.user_id,
                title="Công ty của bạn đã được mở khóa",
                body=f"Công ty '{company.name}' đã được mở khóa hoạt động trở lại."
            )

    db.commit()
    db.refresh(company)
    
    return company

def verify_company_license_by_id(
    db: Session,
    verification_id: int,
    admin_id: int,
    status: VerificationLogStatusEnum,
    reason: str | None = None
) -> CompanyVerification:
    """Duyệt hoặc Từ chối một bản ghi CompanyVerification cụ thể"""
    verification = db.query(CompanyVerification).filter(CompanyVerification.id == verification_id).first()
    if not verification:
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu xác minh")

    company = db.query(Company).filter(Company.id == verification.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty liên kết")

    # Cập nhật trạng thái của bản ghi xác minh
    verification.status = status
    verification.reviewed_by = admin_id

    # Đồng bộ trạng thái của công ty tương ứng
    if status == VerificationLogStatusEnum.approved:
        company.verification_status = CompanyVerificationStatusEnum.approved
    elif status == VerificationLogStatusEnum.rejected:
        company.verification_status = CompanyVerificationStatusEnum.rejected

    # Gửi thông báo đến tất cả thành viên của công ty
    from app.crud.crud_notification import create_notification
    from app.models.companies import CompanyMember

    members = db.query(CompanyMember).filter(CompanyMember.company_id == company.id).all()
    for member in members:
        if status == VerificationLogStatusEnum.approved:
            create_notification(
                db=db,
                user_id=member.user_id,
                title="Giấy phép kinh doanh đã được duyệt",
                body=f"Giấy phép kinh doanh của công ty '{company.name}' đã được phê duyệt thành công bởi Ban quản trị."
            )
        elif status == VerificationLogStatusEnum.rejected:
            create_notification(
                db=db,
                user_id=member.user_id,
                title="Giấy phép kinh doanh bị từ chối",
                body=f"Giấy phép kinh doanh của công ty '{company.name}' đã bị từ chối duyệt. Lý do: {reason or 'Không có lý do cụ thể'}."
            )

    db.commit()
    db.refresh(verification)
    return verification

