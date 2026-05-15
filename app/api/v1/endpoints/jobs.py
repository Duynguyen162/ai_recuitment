from app.schemas.job_schema import JobStatusActionEnum
from app.schemas.job_schema import JobReposting
from app.schemas.job_schema import JobReportingResponse
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.core.enum import CompanyVerificationStatusEnum, RoleEnum, JobStatusEnum
from app.crud import crud_job
from app.db.database import get_db
from app.models.companies import Company, CompanyMember
from app.models.user import User
from app.schemas.base_schema import ResponseSchema
from app.schemas.job_schema import (
    JobDetailResponse,
    JobPostingCreate,
    JobPostingResponse,
    JobPostingUpdate,
    JobStatusActionRequest,
)
from app.schemas.save_job_schema import SaveJobResponse

router = APIRouter()


@router.get(
    "/get_jobs_create_by_hr",
    response_model=ResponseSchema[list[JobPostingResponse]],
    tags=["HR Jobs"],
    summary="HR lấy danh sách job đã tạo",
)
def get_job_posting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: JobStatusEnum | None = Query(None, description="Lọc theo trạng thái"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ có HR mới dùng được API này")

    offset = (page - 1) * page_size
    jobs, total = crud_job.get_list_job(
        db,
        current_user.id,
        status=status,
        limit=page_size,
        offset=offset,
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
            "total_pages": (total + page_size - 1) // page_size,
        },
    )


@router.get(
    "/search_jobs",
    response_model=ResponseSchema[list[JobPostingResponse]],
    tags=["Public Jobs"],
    summary="Tìm kiếm job công khai",
)
def search_public_jobs(
    keyword: str | None = Query(None, description="Tìm theo tiêu đề"),
    location: str | None = Query(None, description="Tìm theo địa điểm"),
    tag: str | None = Query(None, description="Tìm theo tag"),
    job_type: str | None = Query(None, description="Tìm theo loại công việc"),
    candidate_exp: int | None = Query(None, description="Tìm theo số năm kinh nghiệm"),
    limit: int = Query(10, description="Số job mỗi lần trả về"),
    offset: int = Query(0, description="Bỏ qua bao nhiêu job đầu"),
    db: Session = Depends(get_db),
):
    jobs, total = crud_job.get_public_jobs(
        db,
        keyword=keyword,
        location=location,
        tag=tag,
        job_type=job_type,
        candidate_exp=candidate_exp,
        limit=limit,
        offset=offset,
    )
    return ResponseSchema(
        success=True,
        data=jobs,
        error=None,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )


@router.put(
    "/{job_id}/status",
    response_model=ResponseSchema[JobPostingResponse],
    tags=["HR Jobs"],
    summary="HR đổi trạng thái job",
)
def change_job_status(
    job_id: int,
    action: JobStatusActionEnum = Query(..., alias="status", description="Hành động: published, paused, closed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chỉ xử lý chuyển trạng thái job theo action hợp lệ."""
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ HR mới được đổi trạng thái job")

    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn chưa thuộc công ty nào")

    # Mặc định mapping nếu frontend gửi string trạng thái thay vì động từ hành động
    mapping = {
        JobStatusActionEnum.published: JobStatusActionEnum.publish,
        JobStatusActionEnum.paused: JobStatusActionEnum.pause,
        JobStatusActionEnum.closed: JobStatusActionEnum.close,
    }
    final_action = mapping.get(action, action)

    updated_job = crud_job.update_job_status(
        db=db,
        job_id=job_id,
        company_id=member.company_id,
        action=final_action,
    )

    if not updated_job:
        raise HTTPException(status_code=404, detail="Không tìm thấy job hoặc bạn không có quyền")

    return ResponseSchema(
        success=True,
        data=JobPostingResponse.model_validate(updated_job),
        error=None,
        meta=None,
    )


@router.post(
    "/create_jobs",
    response_model=ResponseSchema[JobPostingResponse],
    tags=["HR Jobs"],
    summary="HR tạo job mới",
)
def create_job(
    job_in: JobPostingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """HR tạo job mới, mặc định lưu ở draft."""
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ nhà tuyển dụng mới được đăng tin")

    member = db.query(CompanyMember).filter(CompanyMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(
            status_code=404,
            detail="Bạn chưa thuộc công ty nào. Vui lòng đăng ký công ty trước.",
        )

    company = db.query(Company).filter(Company.id == member.company_id).first()
    if company.verification_status == CompanyVerificationStatusEnum.pending:
        raise HTTPException(status_code=403, detail="Giấy phép kinh doanh đang chờ duyệt")
    if company.verification_status == CompanyVerificationStatusEnum.rejected:
        raise HTTPException(status_code=403, detail="Giấy phép kinh doanh bị từ chối")
    if company.verification_status == CompanyVerificationStatusEnum.locked:
        raise HTTPException(status_code=403, detail="Tài khoản công ty đã bị khóa")

    new_job = crud_job.create_job_posting(
        db=db,
        company_id=company.id,
        user_id=current_user.id,
        job_in=job_in,
    )

    return ResponseSchema(
        success=True,
        data=JobPostingResponse.model_validate(new_job),
        error=None,
        meta=None,
    )


@router.put(
    "/update_job/{job_id}",
    response_model=ResponseSchema[JobPostingResponse],
    tags=["HR Jobs"],
    summary="HR cập nhật nội dung job draft",
)
def update_job(
    job_id: int,
    job_update: JobPostingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chỉ cho phép sửa nội dung khi job đang là draft."""
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ HR mới có chức năng này")

    updated_job = crud_job.update_job_crud(db, job_id, job_update, current_user.id)

    return ResponseSchema(
        success=True,
        data=JobPostingResponse.model_validate(updated_job),
        error=None,
        meta=None,
    )


@router.get(
    "/job_proposed",
    response_model=ResponseSchema[list[JobPostingResponse]],
    tags=["Public Jobs"],
    summary="Lấy danh sách job đề xuất",
)
def get_proposed_jobs(
    limit: int = Query(20, description="Số lượng mỗi trang"),
    offset: int = Query(0, description="Bắt đầu từ bản ghi số mấy"),
    db: Session = Depends(get_db),
):
    proposed_jobs, total = crud_job.get_proposed_jobs(db, limit=limit, offset=offset)
    data = [JobPostingResponse.model_validate(job) for job in proposed_jobs]

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )

@router.get(
    "/job_matched_cv",
    response_model=ResponseSchema[list[JobPostingResponse]],
    tags=["Public Jobs"],
    summary="Lấy danh sách job phù hợp với các tag của ứng viên",
)
def get_job_match_cv(
    limit: int = Query(20, description="Số lượng mỗi trang"),
    offset: int = Query(0, description="Bắt đầu từ bản ghi số mấy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới có chức năng này")
        
    proposed_jobs, total = crud_job.get_job_match_cv(db , current_user, limit=limit, offset=offset,)
    data = [JobPostingResponse.model_validate(job) for job in proposed_jobs]

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    )

@router.delete(
    "/delete_jobs",
    tags=["HR Jobs"],
    summary="HR xóa job",
)
def deleted_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(status_code=403, detail="Chỉ HR mới có chức năng này")

    crud_job.delete_job(db, job_id)
    return ResponseSchema(
        success=True,
        data=job_id,
        error=None,
        meta=None,
    )


@router.get(
    "/job_detail/{job_id}",
    response_model=ResponseSchema[JobDetailResponse],
    tags=["Public Jobs"],
    summary="Lấy chi tiết job",
)
def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    job_data = crud_job.get_job_by_id(db, job_id=job_id, user_id=user_id)

    if not job_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin công việc")

    job, has_applied_flag, save = job_data
    data = JobDetailResponse.model_validate(job)

    if current_user:
        data.has_applied = has_applied_flag
        data.is_save = save

    return ResponseSchema(success=True, data=data)


@router.get(
    "/save_job",
    response_model=ResponseSchema[List[JobDetailResponse]],
    tags=["Candidate Jobs"],
    summary="Ứng viên lấy danh sách job đã lưu",
)
def get_list_save_job(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới có chức năng này")
    data = crud_job.list_save_job(db, current_user.id)

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta=None,
    )


@router.post(
    "/save_job/{job_id}",
    response_model=ResponseSchema[SaveJobResponse],
    tags=["Candidate Jobs"],
    summary="Ứng viên lưu job",
)
def save_job_favourite(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới lưu được job")

    save, _job = crud_job.save_job(db, job_id, current_user.id)
    data = SaveJobResponse.model_validate(save)

    return ResponseSchema(
        success=True,
        data=data,
        error=None,
        meta=None,
    )


@router.delete(
    "/delete_saved_job",
    tags=["Candidate Jobs"],
    summary="Ứng viên bỏ lưu job",
)
def deleted_saved_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    crud_job.delete_saved_job(db, current_user.id, job_id)
    return ResponseSchema(
        success=True,
        data=job_id,
        error=None,
        meta=None,
    )

@router.post(
    "/report_job",
    tags = ["Candidate Jobs"],
    summary = "Ứng viên báo cáo job",
    response_model= ResponseSchema[JobReportingResponse]
    )
def report_job(
    job_id: int,
    reason: JobReposting,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới báo cáo được job")
    
    report = crud_job.report_job(db, job_id, current_user.id, reason.reason)
    return ResponseSchema(
        success=True,
        data=JobReportingResponse.model_validate(report),
        error=None,
        meta=None,
    )

