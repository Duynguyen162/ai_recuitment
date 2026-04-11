from sqlalchemy.orm import Session
from app.models.applications import Application
from app.models.candidate_profiles import CandidateProfile
from app.models.job_posting import JobPosting
from app.core.enum import JobStatusEnum
from fastapi import HTTPException

def create_application(db:Session , user_id:int , job_id: int ):
    """Nộp hồ sơ ứng tuyển"""
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.status == JobStatusEnum.published
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Tin tuyển dụng không tồn tại hoặc đã đóng")
    
    candidate = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
        ).first()
    if not candidate:
        raise HTTPException(404, "Candidate profile chưa tồn tại")
    
    applied_job = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == job_id
    ).first()
    if applied_job:
        raise HTTPException(status_code=404, detail=" đã nộp hồ sơ cho job này rồi")
    
    new_applied = Application(job_id = job_id , candidate_id = candidate.id)
    
    db.add(new_applied)
    db.commit()
    db.refresh(new_applied)

    return new_applied

def delete_application(db:Session , user_id: int , job_id: int):
    """Hủy đơn ứng tuyển""" 
    candidate_profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not candidate_profile:
        raise HTTPException(status_code=404 , detail="chưa có profile")
    
    del_applied = db.query(Application).filter(
        Application.candidate_id == candidate_profile.id,
        Application.job_id == job_id
    ).first()

    if not del_applied:
        raise HTTPException(status_code=404 , detail="Chưa ứng tuyển vào công ty này, không thể hủy")
    
    db.delete(del_applied)
    db.commit()
    return None

# app/crud/crud_application.py
from app.models.ai_matching_scores import AiMatchingScore

def create_ai_matching_score(db: Session, application_id: int, score_data: dict):
    """Lưu kết quả chấm điểm của AI vào Database"""
    new_score = AiMatchingScore(
        application_id=application_id,
        score=score_data.get("score"),
        strengths=score_data.get("strengths", []),
        weaknesses=score_data.get("weaknesses", []),
        explanation=score_data.get("explanation")
    )
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    return new_score