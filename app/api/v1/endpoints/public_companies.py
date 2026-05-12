from app.api.deps import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user_optional, get_current_candidate_profile
from app.db.database import get_db
from app.models.user import User
from app.models.candidate_profiles import CandidateProfile
from app.crud import crud_company
from app.schemas.base_schema import ResponseSchema
from app.schemas.company_schema import PublicCompanyResponse, CompanyFollowResponse
from app.schemas.job_schema import JobPostingResponse

router = APIRouter(tags=["Public Companies"])

@router.get("/followed", response_model=ResponseSchema[List[PublicCompanyResponse]])
def get_list_followed_companies(
    db: Session = Depends(get_db),
    candidate_profile: CandidateProfile = Depends(get_current_candidate_profile),
):
    """Lấy danh sách các công ty mà candidate đã theo dõi"""
    companies = crud_company.list_companies_followed(db, candidate_profile.id)

    return ResponseSchema(
        success=True,
        data=companies,
        error=None, 
        meta=None
    )

@router.get("/{company_id}", response_model=ResponseSchema[PublicCompanyResponse])
def get_public_company_info(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional)
):
    """Lấy thông tin public của công ty. Có kèm số lượng người theo dõi và trạng thái theo dõi (nếu đăng nhập)."""
    user_id = current_user.id if current_user else None
    company_data = crud_company.get_public_company(db, company_id, user_id)
    return ResponseSchema(
        success=True,
        data=company_data,
        error=None,
        meta=None
    )

@router.get("/{company_id}/jobs", response_model=ResponseSchema[List[JobPostingResponse]])
def get_public_company_jobs_list(
    company_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lấy danh sách tin tuyển dụng public của công ty (phân trang)."""
    jobs, total = crud_company.get_public_company_jobs(db, company_id, page, page_size)
    return ResponseSchema(
        success=True,
        data=jobs,
        error=None,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total
        }
    )

@router.post("/{company_id}/follow", response_model=ResponseSchema[CompanyFollowResponse])
def toggle_follow_company_action(
    company_id: int,
    db: Session = Depends(get_db),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """
    Theo dõi hoặc hủy theo dõi công ty. 
    Nếu đang theo dõi -> Hủy.
    Nếu chưa theo dõi -> Theo dõi.
    Dành cho Candidate.
    """
    is_followed = crud_company.toggle_follow_company(db, profile.id, company_id)
    follower_count = crud_company.get_company_follower_count(db, company_id)
    return ResponseSchema(
        success=True,
        data={
            "is_followed": is_followed,
            "follower_count": follower_count
        },
        error=None,
        meta=None
    )


