# app/api/v1/endpoints/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.models.companies import CompanyMember, Company
from app.api.deps import get_current_user
from app.core.enum import RoleEnum, CompanyVerificationStatusEnum
from app.schemas.job_schema import JobPostingCreate, JobPostingResponse, StatusUpdateRequest
from app.schemas.base_schema import ResponseSchema
from app.crud import crud_job

router = APIRouter()

import enum
class UpdateJobStatusEnum(str, enum.Enum):
    published = "published"  # Cho phép HR mở lại tin đang tạm dừng
    paused = "paused"        # Tạm dừng tin
    closed = "closed"        # Đóng hẳn tin

@router.get("/get_jobs_create_by_hr",response_model=ResponseSchema[list[JobPostingResponse]])
def get_job_posting(
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """lấy danh sách job đã đăng"""
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=404 , detail="chỉ có hr mới dùng được api này")
    
    list_job = crud_job.get_list_job(db , current_user.id )
    data = []
    for job in list_job:
        job_response = JobPostingResponse.model_validate(job)
        data.append(job_response)

    return ResponseSchema(
        success=True,
        data = data,
        error=None,
        meta=None
    )

@router.get("/search_jobs",response_model=ResponseSchema[list[JobPostingResponse]])
def search_public_jobs(
    keyword: str | None = Query(None,description="tìm theo tiêu đề "),
    location: str | None = Query(None, description="Tìm theo địa điểm"),
    tag: str | None = Query(None, description=" Tìm theo tag"  ),

    limit: int = Query(10, description="Số job mỗi lần trả về"),
    offset: int = Query(0, description="Bỏ qua bao nhiêu job đầu"),

    db: Session = Depends(get_db)
):
    """API public: hiển thị danh sách việc làm cho ứng viên"""
    jobs = crud_job.get_public_jobs(
        db,
        keyword=keyword,
        location= location, 
        tag=tag ,
        limit=limit,
        offset=offset
        )
    return ResponseSchema(
        success=True,
        data = jobs,
        error=None,
        meta=None
        )

@router.put("/{job_id}/status", response_model=ResponseSchema[JobPostingResponse])
def change_job_status(
    job_id: int,
    status: UpdateJobStatusEnum = Query(..., description="Chọn trạng thái muốn chuyển đổi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """HR Tạm dừng hoặc Đóng tin tuyển dụng"""
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ Nhà tuyển dụng mới được đổi trạng thái")

    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn chưa thuộc công ty nào")

    updated_job = crud_job.update_job_status(
        db=db, 
        job_id=job_id, 
        company_id=member.company_id, 
        new_status=status.value
    )
    
    if not updated_job:
        raise HTTPException(status_code=404, detail="Không tìm thấy tin tuyển dụng hoặc bạn không có quyền")

    return ResponseSchema(
        success=True, 
        data=JobPostingResponse.model_validate(updated_job),
        error=None,
        meta=None
)

@router.post("/create_jobs", response_model=ResponseSchema[JobPostingResponse])
def create_job(
    job_in: JobPostingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """HR đăng tin tuyển dụng mới"""
    # 1. Kiểm tra phải là HR không
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ Nhà tuyển dụng mới được đăng tin")

    # 2. Tìm công ty của HR này
    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn chưa thuộc công ty nào. Vui lòng đăng ký công ty trước.")

    # 3. Lấy thông tin công ty để kiểm tra trạng thái kiểm duyệt
    company = db.query(Company).filter(Company.id == member.company_id).first()
    
    if company.verification_status == CompanyVerificationStatusEnum.pending:
        raise HTTPException(status_code=403, detail="Giấy phép kinh doanh đang chờ duyệt. Chưa thể đăng tin!")
    elif company.verification_status == CompanyVerificationStatusEnum.rejected:
        raise HTTPException(status_code=403, detail="Giấy phép kinh doanh bị từ chối. Vui lòng cập nhật lại!")
    elif company.verification_status == CompanyVerificationStatusEnum.locked:
        raise HTTPException(status_code=403, detail="Tài khoản công ty đã bị khóa!")

    new_job = crud_job.create_job_posting(
        db=db, 
        company_id=company.id, 
        user_id=current_user.id, 
        job_in=job_in
    )

    return ResponseSchema(
        success=True,
        data=JobPostingResponse.model_validate(new_job),
        error=None,
        meta=None
    )

@router.get("/job_proposed", response_model=ResponseSchema[list[JobPostingResponse]])
def get_proposed_jobs(
    limit: int = Query(20, description="Số lượng mỗi trang"),
    offset: int = Query(0, description="Bắt đầu từ bản ghi số mấy"),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Ứng viên xem danh sách các job mới đăng """

    proposed_jobs = crud_job.get_proposed_jobs(db, limit=limit, offset=offset)
    data = [JobPostingResponse.model_validate(job) for job in proposed_jobs]

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta=None
    )

@router.delete("/delete_jobs")
def deleted_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    crud_job.delete_job(db , job_id)
    return ResponseSchema(
        success=True,
        data=job_id,
        error=None,
        meta=None
    )
