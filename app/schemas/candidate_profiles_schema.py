import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List

from app.schemas.candidate_details_schema import CandidateExperienceResponse, CandidateEducationResponse, CandidateCertificationResponse, CVUploadResponse

class CandidateProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    skill_tags: Optional[List[str]] = Field(default_factory=list)
    years_of_experience: Optional[int] = None

class CandidateProfileResponse(BaseModel):
    id: int 
    user_id: int
    full_name: str | None = None
    phone: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    skill_tags: Optional[List[str]] = []
    years_of_experience: Optional[int] = None
    
    @field_validator('avatar_url', mode='before')
    @classmethod
    def prepend_base_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("http"):
            from app.core.config import settings
            return f"{settings.BASE_URL}/{v}"
        return v
    
    experiences: List[CandidateExperienceResponse] = []
    educations: List[CandidateEducationResponse] = []
    certifications: List[CandidateCertificationResponse] = []
    cv_uploads: List[CVUploadResponse] = []

    # cho phép chuyển đổi từ SQLAlchemy model sang Pydantic model
    model_config = ConfigDict(from_attributes=True)  

