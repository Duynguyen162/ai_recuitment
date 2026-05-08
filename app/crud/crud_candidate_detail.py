import uuid
from sqlalchemy.orm import Session,joinedload
from app.models.candidate_details import CandidateExperience, CandidateEducation, CandidateCertification, CVUpload
from fastapi import HTTPException

from app.models.candidate_profiles import CandidateProfile
from app.models.user import User
from app.schemas.candidate_details_schema import CVUploadResponse
# CRUD for candidate details
def get_candidate_experience(db: Session, profile: CandidateExperience):
    candidate_exp = db.query(CandidateExperience).filter(CandidateExperience.candidate_id == profile.id).all()
    if not candidate_exp:
        raise HTTPException(status_code=404, detail=" không có dữ liệu")
    return candidate_exp

def create_candidate_experience(db: Session, experience_data: dict , candidate_id: int) -> CandidateExperience:
    new_experience = CandidateExperience(**experience_data, candidate_id=candidate_id)
    db.add(new_experience)
    db.commit()
    db.refresh(new_experience)
    return new_experience

def update_candidate_experience(db: Session, experience_id: int, experience_data: dict, current_user: User) -> CandidateExperience:
    experience = db.query(CandidateExperience).filter(CandidateExperience.id == experience_id,
                                                      CandidateProfile.user_id == current_user.id).first()
    if not experience:
        raise HTTPException(status_code=404, detail="Không tìm thấy kinh nghiệm với id này")
    
    for key, value in experience_data.items():
        setattr(experience, key, value)

    db.commit()
    db.refresh(experience)
    return experience

def delete_candidate_experience(db: Session, experience_id: int , current_user: User) -> None:
    experience = db.query(CandidateExperience).filter(CandidateExperience.id == experience_id,
                                                      CandidateProfile.user_id == current_user.id).first()
    if not experience:
        raise HTTPException(status_code=404, detail="Không tìm thấy kinh nghiệm với id này")
    db.delete(experience)
    db.commit()
    return None

##################################
##################################
##################################
def get_candidate_education(db: Session, profile: CandidateEducation):
    education = db.query(CandidateEducation).filter(CandidateEducation.candidate_id == profile.id).all()
    if not education:
        raise HTTPException(status_code=404, detail=" không có dữ liệu")
    return education

def create_candidate_education(db: Session, education_data: dict , candidate_id: int) -> CandidateEducation:
    new_education = CandidateEducation(**education_data, candidate_id=candidate_id)
    db.add(new_education)
    db.commit()
    db.refresh(new_education)
    return new_education

def update_candidate_education(db: Session, education_id: int, education_data: dict, current_user: User) -> CandidateEducation:
    education = db.query(CandidateEducation).filter(CandidateEducation.id == education_id,
                                                      CandidateProfile.user_id == current_user.id).first()
    if not education:
        raise HTTPException(status_code=404, detail="Không tìm thấy học vấn với id này")
    
    for key, value in education_data.items():
        setattr(education, key, value)

    db.commit()
    db.refresh(education)
    return education
def delete_candidate_education(db: Session, education_id: int , current_user: User) -> None:
    education = db.query(CandidateEducation).filter(CandidateEducation.id == education_id,
                                                      CandidateProfile.user_id == current_user.id).first()
    if not education:
        raise HTTPException(status_code=404, detail="Không tìm thấy học vấn với id này")
    db.delete(education)
    db.commit()
    return None

##################################
##################################
##################################
def get_candidate_certification(db: Session, profile: CandidateCertification):
    certification = db.query(CandidateCertification).filter(CandidateCertification.candidate_id == profile.id).all()
    if not certification:
        raise HTTPException(status_code=404, detail=" không có dữ liệu")
    return certification

def create_candidate_certification(db: Session, certification_data: dict , candidate_id: int) -> CandidateCertification:
    new_certification = CandidateCertification(**certification_data, candidate_id=candidate_id)
    db.add(new_certification)
    db.commit()
    db.refresh(new_certification)
    return new_certification

def update_candidate_certification(db: Session, certification_id: int, certification_data: dict, current_user: User) -> CandidateCertification:
    certification = db.query(CandidateCertification).filter(CandidateCertification.id == certification_id,
                                                      CandidateProfile.user_id == current_user.id).first()
    if not certification:
        raise HTTPException(status_code=404, detail="Không tìm thấy chứng chỉ với id này")
    
    for key, value in certification_data.items():
        setattr(certification, key, value)

    db.commit()
    db.refresh(certification)
    return certification

def delete_candidate_certification(db: Session, certification_id: int , current_user: User) -> None:
    certification = db.query(CandidateCertification).filter(CandidateCertification.id == certification_id,
                                                      CandidateProfile.user_id == current_user.id).first()
    if not certification:
        raise HTTPException(status_code=404, detail="Không tìm thấy chứng chỉ với id này")
    db.delete(certification)
    db.commit()
    return None

##################################
##################################
##################################
import os
import shutil
from fastapi import UploadFile
UPLOAD_DIR = "uploads/cvs"
os.makedirs(UPLOAD_DIR, exist_ok=True) 

def get_candidate_cv(db: Session, profile: CVUpload ):
    education = db.query(CVUpload).filter(CVUpload.candidate_id == profile.id).all()
    if not education:
        raise HTTPException(status_code=404, detail=" không có dữ liệu")
    return education

def get_candidate_cv_by_id(db: Session, profile: CandidateProfile, cv_id: int):
    cv = db.query(CVUpload).filter(
        CVUpload.id == cv_id,
        CVUpload.candidate_id == profile.id
    ).first()

    if not cv:
        raise HTTPException(status_code=404, detail="CV không tồn tại")

    return cv

def create_candidate_cv(db: Session, file: UploadFile, candidate_id: int, user_id: int) -> CVUpload:
    #Validate định dạng file (chỉ cho phép PDF và DOCX)
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF hoặc DOCX")
    
    # Mỗi ứng viên tối đa 5 CV
    cv_count = db.query(CVUpload).filter(CVUpload.candidate_id == candidate_id).count()

    if cv_count >= 5:
        raise HTTPException(status_code=400, detail="Bạn chỉ được lưu tối đa 5 file CV. Vui lòng xóa CV cũ.")

    #Tạo filename unique
    unique_name = f"{user_id}_{uuid.uuid4()}_{file.filename}"
    file_location = os.path.join(UPLOAD_DIR, unique_name)

    #Lưu file vật lý vào server (hoặc sau này thay bằng code đẩy lên AWS S3)
    file_location = f"{UPLOAD_DIR}/{user_id}_{file.filename}"

    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    #Lưu thông tin (metadata) vào Database
    cv_record = CVUpload(
        candidate_id = candidate_id,
        file_name = file.filename,
        file_url = file_location # Đường dẫn để HR có thể tải về sau này
    )
    db.add(cv_record)
    db.commit()
    db.refresh(cv_record)
    return cv_record

def delete_candidate_cv(db: Session , cv_id: int , current_user: User)->None:

    cv_record = db.query(CVUpload).filter(CVUpload.id == cv_id,
                                    CandidateProfile.user_id == current_user.id).first()
    if not cv_record:
        raise HTTPException(status_code=404, detail="Không tìm thấy chứng chỉ với id này")
    # xóa file vật lý
    if os.path.exists(cv_record.file_url):
        os.remove(cv_record.file_url)
        
    db.delete(cv_record)
    db.commit()


def get_full_candidate_cv(db: Session, candidate_id: int):
    profile = db.query(CandidateProfile).options(
        joinedload(CandidateProfile.experiences),
        joinedload(CandidateProfile.educations),
        joinedload(CandidateProfile.certifications),
    ).filter(
        CandidateProfile.id == candidate_id
    ).first()

    return profile
