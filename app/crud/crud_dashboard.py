from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.user import User
from app.models.companies import CompanyMember
from app.models.job_posting import JobPosting
from app.models.applications import Application
from app.models.candidate_profiles import CandidateProfile
from app.models.interview import Interview
from app.models.ai_matching_scores import AiMatchingScore
from app.core.enum import JobStatusEnum, ApplicationStatusEnum, RoleEnum

def get_company_id(db: Session, hr_id: int) -> int:
    member = db.query(CompanyMember).filter(CompanyMember.user_id == hr_id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Chưa tham gia công ty nào")
    return member.company_id

def get_dashboard_stats(db: Session, hr_user: User):
    company_id = get_company_id(db, hr_user.id)
    # Lấy timezone hiện tại thay vì ép utc nếu database timezone không khớp
    # Tuy nhiên mặc định SQLAlchemy nếu dùng DateTime(timezone=True) sẽ map tốt
    now = datetime.now(timezone.utc)
    
    # activeJobs
    active_jobs = db.query(JobPosting).filter(
        JobPosting.company_id == company_id,
        JobPosting.status == JobStatusEnum.published
    ).count()
    
    # newApplicants (status pending)
    new_applicants = db.query(Application).join(JobPosting).filter(
        JobPosting.company_id == company_id,
        Application.status == ApplicationStatusEnum.pending
    ).count()
    
    # interviewsToday
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    interviews_today = db.query(Interview).join(Application).join(JobPosting).filter(
        JobPosting.company_id == company_id,
        Interview.interview_time >= today_start,
        Interview.interview_time <= today_end
    ).count()
    
    # responseRate
    total_apps = db.query(Application).join(JobPosting).filter(
        JobPosting.company_id == company_id
    ).count()
    responded_apps = db.query(Application).join(JobPosting).filter(
        JobPosting.company_id == company_id,
        Application.status != ApplicationStatusEnum.pending
    ).count()
    
    response_rate = int((responded_apps / total_apps * 100)) if total_apps > 0 else 0
    
    return {
        "activeJobs": active_jobs,
        "newApplicants": new_applicants,
        "interviewsToday": interviews_today,
        "responseRate": response_rate
    }

def get_pending_applications(db: Session, hr_user: User, limit: int = 5):
    company_id = get_company_id(db, hr_user.id)
    
    applications = db.query(
        Application.id,
        CandidateProfile.full_name,
        JobPosting.title,
        Application.applied_at
    ).join(CandidateProfile).join(JobPosting).filter(
        JobPosting.company_id == company_id,
        Application.status == ApplicationStatusEnum.pending
    ).order_by(Application.applied_at.desc()).limit(limit).all()
    
    return [
        {
            "id": app.id,
            "candidate_name": app.full_name,
            "job_title": app.title,
            "time": app.applied_at.strftime("%H:%M - %d/%m/%Y") if app.applied_at else ""
        } for app in applications
    ]

def get_upcoming_interviews(db: Session, hr_user: User, limit: int = 5):
    company_id = get_company_id(db, hr_user.id)
    now = datetime.now(timezone.utc)
    
    interviews = db.query(
        Interview.id,
        CandidateProfile.full_name,
        JobPosting.title,
        Interview.interview_time
    ).join(Application, Interview.application_id == Application.id)\
     .join(CandidateProfile, Application.candidate_id == CandidateProfile.id)\
     .join(JobPosting, Application.job_id == JobPosting.id)\
     .filter(
        JobPosting.company_id == company_id,
        Interview.interview_time >= now
    ).order_by(Interview.interview_time.asc()).limit(limit).all()
    
    return [
        {
            "id": i.id,
            "candidate_name": i.full_name,
            "job_title": i.title,
            "time": i.interview_time.strftime("%H:%M - %d/%m/%Y") if i.interview_time else ""
        } for i in interviews
    ]

def get_active_jobs(db: Session, hr_user: User, limit: int = 5):
    company_id = get_company_id(db, hr_user.id)
    now = datetime.now(timezone.utc)
    
    jobs = db.query(JobPosting).filter(
        JobPosting.company_id == company_id,
        JobPosting.status == JobStatusEnum.published
    ).order_by(JobPosting.created_at.desc()).limit(limit).all()
    
    result = []
    for job in jobs:
        applicants_count = db.query(Application).filter(Application.job_id == job.id).count()
        
        ai_scores = db.query(AiMatchingScore.score).join(Application).filter(
            Application.job_id == job.id,
            AiMatchingScore.score.isnot(None)
        ).all()
        
        avg_score = 0
        if ai_scores:
            total_score = sum([s[0] for s in ai_scores if s[0] is not None])
            avg_score = int(total_score / len(ai_scores)) if len(ai_scores) > 0 else 0
            
        days_remaining = 0
        if job.expired_at:
            delta = job.expired_at - now
            days_remaining = max(0, delta.days)
            
        result.append({
            "id": job.id,
            "title": job.title,
            "applicants_count": applicants_count,
            "ai_avg_score": avg_score,
            "days_remaining": days_remaining
        })
    return result
