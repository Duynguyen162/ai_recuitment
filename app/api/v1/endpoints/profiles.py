from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.core.enum import RoleEnum
from app.db.database import get_db
from app.models.user import User
from app.models.candidate_profiles import CandidateProfile
from fastapi import Depends
from app.api.deps import get_current_user
from app.schemas.candidate_profiles_schema import CandidateProfileResponse , CandidateProfileUpdate
from app.schemas.base_schema import ResponseSchema

router = APIRouter()

@router.get("/profileCandidate", response_model = ResponseSchema[CandidateProfileResponse])
def get_profile(db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)
               ):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới có hồ sơ này")

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first() #trả về kiểu đối tượng SQLAlchemy

    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ ứng viên")
    # Chuyển đổi từ SQLAlchemy model ( 1 đối tượng) sang Pydantic model(kiểu json)
    profile_response = CandidateProfileResponse.model_validate(profile)

    return ResponseSchema(
        success=True,
        data=profile_response,
        error=None,
        meta=None
    )

@router.put("/profileCandidate", response_model = ResponseSchema[CandidateProfileResponse])
def update_profile(profile_in: CandidateProfileUpdate,
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user)
                ):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới có hồ sơ này")

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ ứng viên")
    
    # Cập nhật thông tin hồ sơ
    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)

    profile_response = CandidateProfileResponse.model_validate(profile)
    return ResponseSchema(
        success=True,
        data=profile_response,
        error=None,
        meta=None
    )