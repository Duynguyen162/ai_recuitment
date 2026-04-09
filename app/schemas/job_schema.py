from pydantic import BaseModel, Field
from datetime import datetime
from app.core.enum import JobTypeEnum, JobStatusEnum

class JobPostingBase(BaseModel):
    title: str = Field(..., description="Tiêu đề công việc")
    description: str = Field(..., description="Mô tả công việc")
    requirements: str = Field(..., description="Yêu cầu ứng viên")
    location: str | None = Field(None, description="Địa điểm làm việc")
    
    # Kỹ năng từ khóa (Dành cho AI Matching)
    tags: list[str] = Field(default=[], description="Danh sách từ khóa kỹ năng (vd: ['Python', 'FastAPI'])")
    
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: JobTypeEnum
    expired_at: datetime

class JobPostingCreate(JobPostingBase):
    pass

class JobPostingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    requirements: str | None = None
    location: str | None = None
    tags: list[str] | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: JobTypeEnum | None = None
    status: JobStatusEnum | None = None
    expired_at: datetime | None = None

class JobPostingResponse(JobPostingBase):
    id: int
    company_id: int
    created_by: int
    status: JobStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

class StatusUpdateRequest(BaseModel):
    status: JobStatusEnum