from app.core.logger import logger
from sqlalchemy.orm import Session
from app.models.candidate_profiles import CandidateProfile
from app.schemas.candidate_profiles_schema import CandidateProfileUpdate

#lấy profile của ứng viên
def get_candidate_profile(db: Session, user_id: int):
    return db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()

def upsert_profile(db: Session, user_id: int, profile_in: CandidateProfileUpdate):
    profile = get_candidate_profile(db, user_id)

    if not profile:
        # Tạo mới
        profile_dict = profile_in.model_dump(exclude_unset=True)
        profile = CandidateProfile(user_id=user_id, **profile_dict)
        db.add(profile)
    else:
        # Update
        update_data = profile_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    
    logger.info(f"Upsert profile thành công cho user_id: {user_id}")
    return profile

    