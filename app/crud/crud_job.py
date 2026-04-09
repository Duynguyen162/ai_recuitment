# app/crud/crud_job.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.job_posting import JobPosting
from app.schemas.job_schema import JobPostingCreate
from app.core.enum import JobStatusEnum
from sqlalchemy import or_

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
    tag: str | None = None,
    limit: int = 20,
    offset: int = 0
):
    """API tìm kiếm các công việc đang public"""
    query = db.query(JobPosting).filter(
        JobPosting.status == JobStatusEnum.published
    )

    if keyword:
        query = query.filter(
            or_(
                JobPosting.title.ilike(f"%{keyword}%"),
                JobPosting.description.ilike(f"%{keyword}%"),
                JobPosting.requirements.ilike(f"%{keyword}%")
            )
        )

    if location:
        query = query.filter(JobPosting.location.ilike(f"%{location}%"))

    if tag:
        query = query.filter(JobPosting.tags.contains([tag]))

    return (
        query.order_by(JobPosting.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

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

def delete_job(db: Session , job_id: int):
    """ xóa job đã đăng """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy job này")
    
    db.delete(job)
    db.commit()
    return None
        
