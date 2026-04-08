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

def verify_company_license(db:Session , company_id:int, admin_id: int , is_approved: bool):
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
    if is_approved:
        company.verification_status = CompanyVerificationStatusEnum.approved
        verification.status = VerificationLogStatusEnum.approved
    else:
        company.verification_status = CompanyVerificationStatusEnum.rejected
        verification.status = VerificationLogStatusEnum.rejected
    
    verification.reviewed_by = admin_id
    
    db.commit()
    db.refresh(company)
    
    return company
    
def lock_or_unlock_company(db: Session, company_id: int, is_locked: bool):
    """Khóa hoặc Mở khóa một công ty"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    if is_locked:
        company.verification_status = CompanyVerificationStatusEnum.locked
    else:
        company.verification_status = CompanyVerificationStatusEnum.approved

    db.commit()
    db.refresh(company)
    
    return company
