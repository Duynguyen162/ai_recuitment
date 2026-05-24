from datetime import datetime
from pydantic import BaseModel, Field
from typing import List

from app.core.enum import ApplicationStatusEnum, CvTypeEnum


class ApplicationCreate(BaseModel):
    job_id: int
    cv_type: CvTypeEnum
    cv_id:int | None = None

class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    job_title: str 
    company_name: str
    status: ApplicationStatusEnum
    applied_at: datetime
    cv_type: CvTypeEnum
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
    cv_type: CvTypeEnum
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


class CandidateExperienceItem(BaseModel):
    company_name: str | None = None
    job_title: str | None = None
    description: str | None = None


class CandidateEducationItem(BaseModel):
    institution_name: str | None = None
    major: str | None = None
    degree: str | None = None


class CandidateCertificationItem(BaseModel):
    name: str | None = None
    issuer: str | None = None


class CandidateProfileForHrResponse(BaseModel):
    full_name: str | None = None
    email: str
    phone: str | None = None
    address: str | None = None
    date_of_birth: str | None = None
    summary: str | None = None
    skills: List[str] = Field(default_factory=list)
    experiences: List[CandidateExperienceItem] = Field(default_factory=list)
    educations: List[CandidateEducationItem] = Field(default_factory=list)
    certifications: List[CandidateCertificationItem] = Field(default_factory=list)


class AiScoreStatusResponse(BaseModel):
    application_id: int
    status: str
    score: float | None = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    explanation: str | None = None
    error_message: str | None = None


class AiRequeueResponse(BaseModel):
    queued_count: int
    skipped_count: int
    application_ids: List[int] = Field(default_factory=list)
