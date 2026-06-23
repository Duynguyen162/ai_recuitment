from app.models.job_reports import JobReportStatusEnum
import enum
from pydantic import BaseModel, Field

class AIGenerateJobRequest(BaseModel):
    prompt: str = Field(..., description="Yêu cầu tuyển dụng ngắn gọn từ HR")
from datetime import datetime
from typing import List
from app.core.enum import JobTypeEnum, JobStatusEnum

class CompanyShortResponse(BaseModel):
    id: int
    name: str
    logo_url: str | None = None

    class Config:
        from_attributes = True

class JobPostingBase(BaseModel):
    title: str = Field(..., description="Tiêu đề công việc")
    description: str = Field(..., description="Mô tả công việc")
    requirements: str = Field(..., description="Yêu cầu ứng viên")
    benefits: str = Field(..., description="Quyền lợi ứng viên")
    location: str | None = Field(None, description="Địa điểm làm việc")
    tags: list[str] = Field(default=[], description="Danh sách từ khóa kỹ năng (vd: ['Python', 'FastAPI'])")
    salary_min: int | None = None
    salary_max: int | None = None
    years_of_experience: int | None = None
    job_type: JobTypeEnum
    expired_at: datetime

class JobPostingCreate(JobPostingBase):
    status: JobStatusEnum | None = JobStatusEnum.published

class JobPostingUpdate(BaseModel):
    title: str = Field(..., description="Tiêu đề công việc")
    description: str = Field(..., description="Mô tả công việc")
    requirements: str = Field(..., description="Yêu cầu ứng viên")
    benefits: str = Field(..., description="Quyền lợi ứng viên")
    location: str | None = Field(None, description="Địa điểm làm việc")
    tags: list[str] = Field(default=[], description="Danh sách từ khóa kỹ năng")
    salary_min: int | None = None
    salary_max: int | None = None
    years_of_experience: int | None = None
    job_type: JobTypeEnum
    expired_at: datetime

class JobDetailResponse(BaseModel):
    id: int
    title: str
    description: str # Mô tả chi tiết
    requirements: str # Yêu cầu chi tiết
    benefits: str # Quyền lợi
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    years_of_experience: int
    tags: List[str] | None = [] # Các thẻ kỹ năng để AI Matching
    job_type: JobTypeEnum
    status: JobStatusEnum
    locked_by_admin: bool = False
    created_at: datetime
    expired_at: datetime
    company: CompanyShortResponse
    has_applied: bool | None = None
    application_status: str | None = None
    is_save:bool | None = None

    class Config:
        from_attributes = True

class JobPostingResponse(JobPostingBase):
    id: int
    company_id: int
    created_by: int
    status: JobStatusEnum
    locked_by_admin: bool = False
    created_at: datetime
    company: CompanyShortResponse
    is_save:bool | None = None
    class Config:
        from_attributes = True

class JobStatusActionEnum(str, enum.Enum):
    publish = "publish"
    published = "published" # Alias cho publish
    pause = "pause"
    paused = "paused"       # Alias cho pause
    close = "close"
    closed = "closed"       # Alias cho close


class JobStatusActionRequest(BaseModel):
    action: JobStatusActionEnum

class JobReposting(BaseModel):
    reason: str
    
class JobReportingRequest(BaseModel):
    job_id: int = Field(..., description="ID của tin tuyển dụng bị báo cáo")
    reason: str = Field(..., description="Lý do báo cáo")

class JobReportingResponse(BaseModel):
    id: int
    job_id: int
    reason: str
    reported_by: int
    created_at: datetime
    status: JobReportStatusEnum
    
    class Config:
        from_attributes = True