from sqlalchemy.orm import Session
from app.core.enum import CompanyVerificationStatusEnum , VerificationLogStatusEnum
from app.models.companies import Company, CompanyVerification, CompanyMember
from app.schemas.company_schema import CompanyCreate,CompanyUpdate

def get_company_by_hr(db: Session , user_id: int):
    """Lấy thông tin công ty mà HR đang quản lý"""
    member = db.query(CompanyMember).filter(CompanyMember.user_id == user_id).first()
    if member:
        return db.query(Company).filter(Company.id == member.company_id).first()
    return None

def register_company(db: Session, hr_id: int , company_in: CompanyCreate , license_url:str ):
    try:
        #tạo bản ghi công ty
        db_company = Company(
            **company_in.model_dump(),
            verification_status = CompanyVerificationStatusEnum.pending
        )
        db.add(db_company)
        db.flush()
        # thêm bảng xác thực cty
        db_verification = CompanyVerification(
            company_id = db_company.id,
            license_url = license_url,
            status = VerificationLogStatusEnum.pending
        )
        db.add(db_verification)
        #gán user vào công ty
        db_member = CompanyMember(
            company_id = db_company.id,
            user_id = hr_id
        )
        db.add(db_member)
        
        db.commit()
        db.refresh(db_company)
        return db_company

    except Exception as e:
        db.rollback()
        raise e
    
# def delete_company_data(db: Session, company_id: int):
#     """ dùng để xóa công ty"""
#     company = db.query(Company).filter(Company.id == company_id).first()
#     if company:
#         db.delete(company)
#         db.commit()
#     return True


def update_company_info(db: Session, db_company: Company, company_in: CompanyUpdate):
    """Cập nhật thông tin công ty"""
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    db.commit()
    db.refresh(db_company)
    return db_company

def remove_member_from_company(db: Session, user_id: int, company_id: int):
    """ rời khỏi công ty"""
    member = db.query(CompanyMember).filter(
        CompanyMember.user_id == user_id, 
        CompanyMember.company_id == company_id
    ).first()
    if member:
        db.delete(member)
        db.commit()
    return True