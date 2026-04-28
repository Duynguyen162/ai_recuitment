# app/crud/crud_job.py
from fastapi import HTTPException
from sqlalchemy.orm import Session ,joinedload
from app.models.saved_jobs import SaveJob
from app.models.applications import Application
from app.models.candidate_profiles import CandidateProfile
from app.models.job_posting import JobPosting
from app.schemas.job_schema import JobPostingCreate
from app.core.enum import JobStatusEnum
from sqlalchemy import String, and_, column, or_, select
from sqlalchemy import func

def get_list_job(db: Session, user_id: int):
    """
    danh sách các job đã đăng
    """
    data = db.query(JobPosting).filter(JobPosting.created_by == user_id).all()

    if not data:
        raise HTTPException(status_code=404, detail="chưa đăng bài tuyển dụng nào")
    return data

def get_public_jobs(
    db: Session,
    keyword: str | None = None,
    location: str | None = None,
    job_type: str | None = None,
    tag: str | None = None,
    candidate_exp: int | None = None,
    limit: int = 20,
    offset: int = 0,
):
    """tìm kiếm tin tuyển dụng công khai với nhiều tiêu chí khác nhau (có phân trang)"""
    
    query = db.query(JobPosting).filter(JobPosting.status == JobStatusEnum.published)

    # HELPER: Escape pattern
    def escape_pattern(s: str) -> str:
        return s.replace('%', r'\%').replace('_', r'\_') if s else ""


    if keyword and keyword.strip():
        keywords = [w.strip() for w in keyword.split() if w.strip()]
        conditions = []
        
        for word in keywords:
            pattern = f"%{escape_pattern(word)}%"
            
            # Title, Description, Tags
            title_cond = func.unaccent(JobPosting.title).ilike(
                func.unaccent(pattern), escape='\\'
            )
            desc_cond = func.unaccent(JobPosting.description).ilike(
                func.unaccent(pattern), escape='\\'
            )
            tag_cond = func.unaccent(
                func.cast(JobPosting.tags, String)
            ).ilike(func.unaccent(pattern), escape='\\')
            
            conditions.append(or_(title_cond, desc_cond, tag_cond))
        
        query = query.filter(and_(*conditions))

    if tag and tag.strip() and not keyword:
        pattern = f"%{escape_pattern(tag.strip())}%"
        query = query.filter(
            func.unaccent(func.cast(JobPosting.tags, String)).ilike(
                func.unaccent(pattern), escape='\\'
            )
        )

    if candidate_exp is not None:
        query = query.filter(JobPosting.years_of_experience <= candidate_exp)

    if job_type:
        query = query.filter(JobPosting.job_type == job_type)

    if location and location.strip():
        pattern = f"%{escape_pattern(location.strip())}%"
        query = query.filter(
            func.unaccent(JobPosting.location).ilike(
                func.unaccent(pattern), escape='\\'
            )
        )
        
    total = query.count()
    jobs = (
        query.order_by(JobPosting.created_at.desc())
        .offset(max(0, offset))
        .limit(min(limit, 100))
        .all()
    )

    return jobs, total

def update_job_status(db: Session, job_id: int, company_id: int, new_status: JobStatusEnum):
    """HR đổi trạng thái tin tuyển dụng """
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.company_id == company_id
    ).first()
    
    if job:
        job.status = new_status
        db.commit()
        db.refresh(job)
    return job

def create_job_posting(db: Session, company_id: int, user_id: int, job_in: JobPostingCreate):
    """Lưu tin tuyển dụng mới vào CSDL"""
    data = job_in.model_dump()
    if isinstance(data.get("tags"), str):
        import json
        data["tags"] = json.loads(data["tags"])

    try:    
        db_job = JobPosting(
            **data,
            company_id=company_id,
            created_by=user_id,
            status=JobStatusEnum.published
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        db.rollback()
        print(e)
        raise

def get_proposed_jobs(db: Session ,offset: int = 0, limit: int = 20):
    """Lấy danh sách các job mới nhất để hiển thị (có phân trang)"""
    query = db.query(JobPosting).filter(JobPosting.status == JobStatusEnum.published)

    total = query.count()

    jobs = (
        query
        .order_by(JobPosting.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return jobs, total

def is_save(db:Session , job_id:int, user_id:int):
    """kiểm tra xem job đã được user lưu chưa"""
    job = db.query(SaveJob).join(CandidateProfile).filter(
        SaveJob.job_id == job_id,
        CandidateProfile.user_id == user_id 
    ).first()
    if job:
        return True
    return False

def get_job_by_id(db: Session, job_id: int, user_id: int | None ):
    """lấy thông tin chi tiết của 1 job"""
    job = (
        db.query(JobPosting)
        .options(joinedload(JobPosting.company))
        .filter(JobPosting.id == job_id)
        .first()
    )

    if not job:
        return None
    
    applied = False
    save = False
    
    if user_id:
        applied = has_applied(db, user_id, job_id)
        save = is_save(db,job_id,user_id)

    return job, applied ,save


def delete_job(db: Session , job_id: int):
    """ xóa job đã đăng """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy job này")
    
    db.delete(job)
    db.commit()
    return None

def has_applied(db: Session, user_id: int, job_id: int):
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not profile:
        return False

    application = db.query(Application).filter(
        Application.candidate_id == profile.id,
        Application.job_id == job_id
    ).first()

    return application is not None


def list_save_job(db: Session, user_id: int):
    result = db.query(JobPosting).join(SaveJob).join(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).all()

    return result


def save_job(db: Session, job_id: int, user_id: int):
    """lưu lại job yêu thích hoặc đang chú ý"""
    candidate = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == user_id
    ).first()

    if not candidate:
        raise HTTPException(status_code=404, detail="Chưa có profile")

    # check đã lưu chưa
    existing = db.query(SaveJob).filter(
        SaveJob.candidate_id == candidate.id,
        SaveJob.job_id == job_id
    ).first()
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()

    if existing:
        raise HTTPException(status_code=400, detail="Job đã được lưu trước đó")

    try:
        save = SaveJob(
            candidate_id=candidate.id, 
            job_id=job_id
        )
        db.add(save)
        db.commit()
        db.refresh(save)
        return save,job

    except Exception as e:
        db.rollback()
        raise e
    
def delete_saved_job(db:Session , user_id:int, job_id:int):
    save_job = db.query(SaveJob).join(CandidateProfile).filter(
        CandidateProfile.user_id == user_id,
        SaveJob.job_id == job_id
    ).first()
    db.delete(save_job)
    db.commit()
    return None