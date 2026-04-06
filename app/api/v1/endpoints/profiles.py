from fastapi import APIRouter, File, HTTPException
from sqlalchemy.orm import Session
from app.core.enum import RoleEnum
from app.crud.crud_candidate_detail import create_candidate_certification, create_candidate_cv, create_candidate_education, create_candidate_experience, delete_candidate_certification, delete_candidate_cv, delete_candidate_education, delete_candidate_experience, get_candidate_certification, get_candidate_cv, get_candidate_education, get_candidate_experience, update_candidate_certification, update_candidate_education, update_candidate_experience
from app.db.database import get_db
from app.models.user import User
from app.models.candidate_profiles import CandidateProfile
from app.models.candidate_details import CandidateExperience , CandidateEducation, CandidateCertification, CVUpload
from app.api.deps import get_current_user
from app.schemas.candidate_details_schema import CandidateExperienceCreate ,CandidateExperienceResponse
from app.schemas.candidate_details_schema import CandidateEducationCreate, CandidateEducationResponse
from app.schemas.candidate_profiles_schema import CandidateProfileResponse , CandidateProfileUpdate
from app.schemas.candidate_details_schema import CandidateCertificationCreate, CandidateCertificationResponse
from app.schemas.candidate_details_schema import CVUploadCreate, CVUploadResponse
from app.crud.crud_candidate_profile import get_candidate_profile, upsert_profile
from app.schemas.base_schema import ResponseSchema
from fastapi import Depends
from app.api.deps import get_current_candidate_profile

router = APIRouter()

@router.get("/profileCandidate", response_model = ResponseSchema[CandidateProfileResponse])
def get_profile(db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user),
                profile: CandidateProfile = Depends(get_current_candidate_profile)
               ): 
    # Chuyển đổi từ SQLAlchemy model ( 1 đối tượng) sang Pydantic model(kiểu json)
    profile_response = CandidateProfileResponse.model_validate(profile)

    return ResponseSchema(
        success=True,
        data=profile_response,
        error=None,
        meta=None
    )

@router.post("/profileCandidate", response_model = ResponseSchema[CandidateProfileResponse])
def update_profile(profile_in: CandidateProfileUpdate,
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user),
                profile: CandidateProfile = Depends(get_current_candidate_profile)
                ):   
    upsert_profile(db, current_user.id, profile_in)
    profile_response = CandidateProfileResponse.model_validate(profile)
    return ResponseSchema(
        success=True,
        data=profile_response,
        error=None,
        meta=None
    )
#=============================================================#
#====================== KINH NGHIỆM ==========================#
#=============================================================#
@router.get("/experiences",response_model = ResponseSchema[list[CandidateExperienceResponse]])
def get_experience(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    exp_detail = get_candidate_experience(db,profile)
    return ResponseSchema(
        success=True,
        data=exp_detail,
        error=None,
        meta=None
    )

@router.post("/experiences", response_model = ResponseSchema[CandidateExperienceResponse])
def create_experience(experience_in: CandidateExperienceCreate,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    candidate_exp = create_candidate_experience(db, experience_in.model_dump(), profile.id) # truyền candidate_id vào để liên kết
    return ResponseSchema(
        success=True,
        data=CandidateExperienceResponse.model_validate(candidate_exp),
        error=None,
        meta=None
    )

@router.put("/experiences/{experience_id}", 
            response_model = ResponseSchema[CandidateExperienceResponse])
def update_experience(experience_id: int,
                    experience_in: CandidateExperienceCreate,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    exp = update_candidate_experience(db, experience_id, experience_in.model_dump(), current_user) # truyền dữ liệu đã chuyển đổi thành dict
    return ResponseSchema(
        success=True,
        data=CandidateExperienceResponse.model_validate(exp),
        error=None,
        meta=None
    )

@router.delete("/experiences/{experience_id}")
def delete_experience(experience_id: int,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    delete_candidate_experience(db, experience_id, current_user )
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )
#=============================================================#
#====================== HỌC VẤN ==============================#
#=============================================================#
@router.get("/educations",response_model = ResponseSchema[list[CandidateEducationResponse]])
def get_experience(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    edu_detail = get_candidate_education(db,profile)
    return ResponseSchema(
        success=True,
        data=edu_detail,
        error=None,
        meta=None
    )

@router.post("/educations", response_model = ResponseSchema[CandidateEducationResponse])
def create_education(education_in: CandidateEducationCreate,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user),
                     profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ): 
    education = create_candidate_education(db, education_in.model_dump(), profile.id) # truyền candidate_id vào để liên kết
    return ResponseSchema(
        success=True,
        data=CandidateEducationResponse.model_validate(education),
        error=None,
        meta=None
    )
@router.put("/educations{education_id}", response_model = ResponseSchema[CandidateEducationResponse])
def update_education(education_id: int,
                    education_in: CandidateEducationCreate,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    education = update_candidate_education(db, education_id, education_in.model_dump(), current_user)
    return ResponseSchema(
        success=True,
        data=CandidateEducationResponse.model_validate(education),
        error=None,
        meta=None
    )
@router.delete("/educations{education_id}")
def delete_education(education_id: int,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user),
                     profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    delete_candidate_education(db, education_id, current_user)
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )

#=============================================================#
#====================== BẰNG CẤP ==============================#
#=============================================================#
@router.get("/certifications",response_model = ResponseSchema[list[CandidateCertificationResponse]])
def get_certification(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    exp_detail = get_candidate_certification(db,profile)
    return ResponseSchema(
        success=True,
        data=exp_detail,
        error=None,
        meta=None
    )

@router.post("/certifications", response_model = ResponseSchema[CandidateCertificationResponse])
def create_certification(certification_in: CandidateCertificationCreate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                         ):  
    certification = create_candidate_certification(db, certification_in.model_dump(), profile.id) # truyền candidate_id vào để liên kết
    return ResponseSchema(
        success=True,
        data=CandidateCertificationResponse.model_validate(certification),
        error=None,
        meta=None
    )
@router.put("/certifications{certification_id}", response_model = ResponseSchema[CandidateCertificationResponse])
def update_certification(certification_id: int,
                         certification_in: CandidateCertificationCreate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    
    certification = update_candidate_certification(db, certification_id, certification_in.model_dump(), current_user)
    return ResponseSchema(
        success=True,
        data=CandidateCertificationResponse.model_validate(certification),
        error=None,
        meta=None
    )
@router.delete("/certifications{certification_id}")
def delete_certification(certification_id: int,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    delete_candidate_certification(db, certification_id, current_user)
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )
#=============================================================#
#=========================== CV ==============================#
#=============================================================#

from fastapi import UploadFile, File   
from sqlalchemy.orm import Session
@router.get("/cv_upload",response_model = ResponseSchema[list[CVUploadResponse]])
def get_experience(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    url_cv = get_candidate_cv(db,profile)
    return ResponseSchema(
        success=True,
        data=url_cv,
        error=None,
        meta=None
    )

@router.post("/cv_upload", response_model = ResponseSchema[CVUploadResponse])
def create_cv_upload(file: UploadFile = File(...),
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user),
                     profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    cv_record = create_candidate_cv(db, file, profile.id, profile.user_id)
    return ResponseSchema(
        success=True,
        data=CVUploadResponse.model_validate(cv_record),
        error=None,
        meta=None
    )
@router.delete("/cv_upload/{cv_upload_id}")
def delete_cv_upload(cv_upload_id: int,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    delete_candidate_cv(db,cv_upload_id,current_user)
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )
