from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.enum import CompanyVerificationStatusEnum , VerificationLogStatusEnum, JobStatusEnum
from app.models.companies import Company, CompanyDocument, CompanyVerification, CompanyMember
from app.models.user import User
from app.models.company_follows import CompanyFollow
from app.models.job_posting import JobPosting
from app.models.candidate_profiles import CandidateProfile
from app.schemas.company_schema import CompanyCreate, CompanyDocumentCreate,CompanyUpdate
from app.services.rag_service import delete_document_from_chroma

def get_company_by_hr(db: Session , user_id: int):
    """Lấy thông tin công ty mà HR đang quản lý"""
    member = db.query(CompanyMember).filter(CompanyMember.user_id == user_id).first()
    if member:
        return db.query(Company).filter(Company.id == member.company_id).first()
    return None

def register_company(db: Session, hr_id: int , company_in: CompanyCreate , license_url:str ):
    try:
        company_data = company_in.model_dump(exclude={"is_vip"})
        
        db_company = Company(
            **company_data,
            is_vip = False,
            verification_status = CompanyVerificationStatusEnum.pending
        )
        db.add(db_company)
        db.flush() # Lưu tạm để lấy db_company.id
        
        # Thêm bảng xác thực cty
        db_verification = CompanyVerification(
            company_id = db_company.id,
            license_url = license_url,
            status = VerificationLogStatusEnum.pending
        )
        db.add(db_verification)
        
        # Gán user vào công ty
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

def get_company_documents(db: Session, company_id: int):
    """Lấy danh sách tất cả tài liệu của một công ty"""
    return db.query(CompanyDocument).filter(CompanyDocument.company_id == company_id).all()

def create_company_document(
    db: Session, 
    company_id: int, 
    user_id: int, 
    doc_in: CompanyDocumentCreate,
):
    """Lưu thông tin tài liệu vào DB"""
    db_doc = CompanyDocument(
        company_id=company_id,
        upload_by_id=user_id,
        file_url=doc_in.file_url, 
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def delete_company_document(db: Session, doc_id: int, user_id: int):
    """Xóa tài liệu (SQL + Chroma)"""
    
    member = db.query(CompanyMember).filter(
        CompanyMember.user_id == user_id
    ).first()

    doc = db.query(CompanyDocument).filter(
        CompanyDocument.id == doc_id
    ).first()

    if not doc or not member or doc.company_id != member.company_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa tài liệu này")

    try:
        delete_document_from_chroma(doc_id, member.company_id)
    except Exception as e:
        print(f"Lỗi khi xóa vector DB: {str(e)}")
        raise HTTPException(status_code=500, detail="Không thể xóa vector database")

    db.delete(doc)
    db.commit()

    return True 

def get_public_company(db: Session, company_id: int, user_id: int | None = None):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")
        
    follower_count = db.query(CompanyFollow).filter(CompanyFollow.company_id == company_id).count()
    is_followed = False
    if user_id:
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
        if profile:
            follow = db.query(CompanyFollow).filter(
                CompanyFollow.company_id == company_id,
                CompanyFollow.candidate_id == profile.id
            ).first()
            if follow:
                is_followed = True

    return {
        **company.__dict__,
        "follower_count": follower_count,
        "is_followed": is_followed
    }

from sqlalchemy.orm import joinedload

def get_public_company_jobs(db: Session, company_id: int, page: int = 1, page_size: int = 10):
    query = db.query(JobPosting).options(joinedload(JobPosting.company)).filter(
        JobPosting.company_id == company_id,
        JobPosting.status == JobStatusEnum.published
    ).order_by(JobPosting.created_at.desc())
    
    total = query.count()
    jobs = query.offset((page - 1) * page_size).limit(page_size).all()
    return jobs, total

def toggle_follow_company(db: Session, candidate_profile_id: int, company_id: int) -> bool:
    """chuyển đổi trạng thái theo dõi. Trả về True nếu đang được theo dõi, False nếu chưa được theo dõi."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Không tìm thấy công ty")

    follow = db.query(CompanyFollow).filter(
        CompanyFollow.candidate_id == candidate_profile_id,
        CompanyFollow.company_id == company_id
    ).first()

    if follow:
        db.delete(follow)
        db.commit()
        return False
    else:
        new_follow = CompanyFollow(
            candidate_id=candidate_profile_id,
            company_id=company_id
        )
        db.add(new_follow)
        db.commit()
        return True

def get_company_follower_count(db: Session, company_id: int) -> int:
    return db.query(CompanyFollow).filter(CompanyFollow.company_id == company_id).count()

def list_companies_followed(db: Session, candidate_profile_id: int):
    companies = db.query(Company).join(CompanyFollow).filter(
        CompanyFollow.candidate_id == candidate_profile_id
    ).all()
    
    # Tính toán follower_count cho từng công ty
    followed_companies = []
    for company in companies:
        follower_count = db.query(CompanyFollow).filter(CompanyFollow.company_id == company.id).count()
        followed_companies.append({
            **company.__dict__,
            "follower_count": follower_count,
            "is_followed": True
        })
    return followed_companies