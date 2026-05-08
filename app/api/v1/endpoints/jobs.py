# app/api/v1/endpoints/jobs.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.models.companies import CompanyMember, Company
from app.api.deps import get_current_user, get_current_user_optional
from app.core.enum import RoleEnum, CompanyVerificationStatusEnum
from app.schemas.job_schema import JobDetailResponse, JobPostingCreate, JobPostingResponse, JobPostingUpdate, StatusUpdateRequest
from app.schemas.base_schema import ResponseSchema
from app.crud import crud_job
from app.schemas.save_job_schema import SaveJobResponse

router = APIRouter()

import enum
class UpdateJobStatusEnum(str, enum.Enum):
    published = "published"  # Cho phép HR mở lại tin đang tạm dừng
    paused = "paused"        # Tạm dừng tin
    closed = "closed"        # Đóng hẳn tin

@router.get("/get_jobs_create_by_hr", response_model=ResponseSchema[list[JobPostingResponse]])
def get_job_posting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="chỉ có hr mới dùng được api này")

    offset = (page - 1) * page_size

    jobs, total = crud_job.get_list_job(
        db,
        current_user.id,
        limit=page_size,
        offset=offset
    )

    data = [JobPostingResponse.model_validate(job) for job in jobs]

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta={
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) 
        }
    )

@router.get("/search_jobs",response_model=ResponseSchema[list[JobPostingResponse]])
def search_public_jobs(
    keyword: str | None = Query(None,description="tìm theo tiêu đề "),
    location: str | None = Query(None, description="Tìm theo địa điểm"),
    tag: str | None = Query(None, description=" Tìm theo tag"  ),
    job_type: str | None = Query(None, description="Tìm theo loại công việc"),
    candidate_exp: int | None = Query(None, description="Tìm theo số năm kinh nghiệm của ứng viên"),
    limit: int = Query(10, description="Số job mỗi lần trả về"),
    offset: int = Query(0, description="Bỏ qua bao nhiêu job đầu"),

    db: Session = Depends(get_db)
):
    """API public: hiển thị danh sách việc làm cho ứng viên"""
    jobs ,total = crud_job.get_public_jobs(
        db,
        keyword=keyword,
        location= location, 
        tag=tag ,
        job_type=job_type,
        candidate_exp=candidate_exp,
        limit=limit,
        offset=offset
        )
    return ResponseSchema(
        success=True,
        data = jobs,
        error=None,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset
        }
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

@router.put("/update_job/{job_id}",response_model=ResponseSchema[JobPostingResponse])
def update_job(
    job_id: int,
    job_update: JobPostingUpdate,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=404 , detail="Chỉ hr mới có chức năng này")
    
    if job_update.status != "draft":
        raise HTTPException(status_code=404 ,detail="chỉ bản nháp mới có thể chỉnh sửa")
        
    job_update = crud_job.update_job_crud(db, job_id , job_update , current_user.id)

    return ResponseSchema(
        success=True,
        data=JobPostingResponse.model_validate(job_update),
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

    proposed_jobs, total = crud_job.get_proposed_jobs(db, limit=limit, offset=offset)
    data = [JobPostingResponse.model_validate(job) for job in proposed_jobs]

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset
        }
    )

@router.delete("/delete_jobs")
def deleted_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=404,detail="chỉ Hr mới có chức năng này")
    
    crud_job.delete_job(db , job_id)
    return ResponseSchema(
        success=True,
        data=job_id,
        error=None,
        meta=None
    )

@router.get("/job_detail/{job_id}", response_model=ResponseSchema[JobDetailResponse])
def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional), 
):
    user_id = current_user.id if current_user else None

    job_data = crud_job.get_job_by_id(db, job_id=job_id, user_id=user_id)

    if not job_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin công việc")

    job, has_applied_flag ,save = job_data
    data = JobDetailResponse.model_validate(job)

    if current_user:
        data.has_applied = has_applied_flag
        data.is_save = save

    return ResponseSchema(success=True, data=data)

@router.get("/save_job", response_model=ResponseSchema[List[JobDetailResponse]])
def get_list_save_job(
    db:Session =Depends(get_db),
    current_user:User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới có chức năng này")
    data = crud_job.list_save_job(db,current_user.id)

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta=None
    )

@router.post("/save_job/{job_id}", response_model=ResponseSchema[SaveJobResponse])
def save_job_favourite(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới lưu được job.")

    save ,job = crud_job.save_job(db, job_id, current_user.id)

    data = SaveJobResponse.model_validate(save)

    return ResponseSchema(
        success=True,
        data=data,  
        error=None,
        meta=None
    )

@router.delete("/delete_saved_job")
def deleted_saved_job(
    job_id:int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    crud_job.delete_saved_job(db , current_user.id,job_id)
    return ResponseSchema(
        success=True,
        data=job_id,
        error=None,
        meta=None
    )
