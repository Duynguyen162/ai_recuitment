import enum
from pydantic import BaseModel, Field
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
    location: str | None = Field(None, description="Địa điểm làm việc")
    tags: list[str] = Field(default=[], description="Danh sách từ khóa kỹ năng (vd: ['Python', 'FastAPI'])")
    salary_min: int | None = None
    salary_max: int | None = None
    years_of_experience: int | None = None
    job_type: JobTypeEnum
    expired_at: datetime

class JobPostingCreate(JobPostingBase):
    pass

class JobPostingUpdate(BaseModel):
    title: str = Field(..., description="Tiêu đề công việc")
    description: str = Field(..., description="Mô tả công việc")
    requirements: str = Field(..., description="Yêu cầu ứng viên")
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
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    years_of_experience: int
    tags: List[str] | None = [] # Các thẻ kỹ năng để AI Matching
    job_type: JobTypeEnum
    status: JobStatusEnum
    created_at: datetime
    expired_at: datetime
    company: CompanyShortResponse
    has_applied: bool | None = None
    is_save:bool | None = None

    class Config:
        from_attributes = True

class JobPostingResponse(JobPostingBase):
    id: int
    company_id: int
    created_by: int
    status: JobStatusEnum
    created_at: datetime
    company: CompanyShortResponse
    class Config:
        from_attributes = True

class JobStatusActionEnum(str, enum.Enum):
    publish = "publish"
    pause = "pause"
    close = "close"


class JobStatusActionRequest(BaseModel):
    action: JobStatusActionEnum
