from datetime import datetime
from pydantic import BaseModel, Field
from typing import List

from app.core.enum import ApplicationStatusEnum


class ApplicationCreate(BaseModel):
    job_id: int
    cv_type:str
    cv_id:int | None = None

class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    job_title: str 
    company_name: str
    status: ApplicationStatusEnum
    applied_at: datetime
    cv_type: str
    cv_id: int | None = None
    cv_name: str 
    cv_url: str | None = None
    class Config:
        from_attributes = True


class CandidateAppliedResponse(BaseModel):
    application_id: int
    candidate_id: int
    full_name: str | None = None
    email: str
    phone: str | None = None
    avatar_url: str | None = None
    years_of_experience: int | None = None
    skill_tags: List[str] = Field(default_factory=list)
    status: str
    applied_at: datetime
    cv_id: int | None = None
    cv_name: str | None = None
    cv_url: str | None = None
    job_title: str | None = None

    class Config:
        from_attributes = True

class ChangeStatusRequest(BaseModel):
    status: ApplicationStatusEnum

class PaginatedCandidatesResponse(BaseModel):
    data: List[CandidateAppliedResponse]
    total: int

class CandidatesStatsResponse(BaseModel):
    all: int
    applied: int
    interviewing: int
    hired: int
    rejected: int
    left_company: int

class InterviewDetailResponse(BaseModel):
    interview_time: datetime
    location: str | None = None
    meeting_link: str | None = None
    mode: str
    notes: str | None = None


class ApplicationDetailResponse(BaseModel):
    job_id: str
    status: str
    rejection_reason: str | None = None
    rejected_at: datetime | None = None
    interview_mode: str | None = None
    interview_time: datetime | None = None
    location: str | None = None
    meeting_link: str | None = None
    notes: str | None = None
    hr_contact_name: str | None = None
    hr_contact_email: str | None = None
    hr_contact_phone: str | None = None

    class Config:
        from_attributes = True