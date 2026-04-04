from pydantic import BaseModel
from pydantic import ConfigDict

# bảng candidate_experiences
class CandidateExperienceUpdate(BaseModel):
    company_name: str | None = None
    job_title: str | None = None
    description: str | None = None

class CandidateExperienceResponse(BaseModel):
    id: int
    candidate_id: int

    # cho phép chuyển đổi từ SQLAlchemy model sang Pydantic model
    model_config = ConfigDict(from_attributes=True) 

# bảng candidate_educations
class CandidateEducationUpdate(BaseModel):
    institution_name: str | None = None
    major: str | None = None
    degree: str | None = None

class CandidateEducationResponse(BaseModel):
    id: int
    candidate_id: int

    model_config = ConfigDict(from_attributes=True)

# bảng candidate_certifications
class CandidateCertificationUpdate(BaseModel):
    name: str | None = None
    issuer: str | None = None

class CandidateCertificationResponse(BaseModel):
    id: int
    candidate_id: int

    model_config = ConfigDict(from_attributes=True)


# bảng cv_uploads
class CVUploadUpdate(BaseModel):
    file_url: str | None = None
    file_name: str | None = None

class CVUploadResponse(BaseModel):
    id: int
    candidate_id: int

    model_config = ConfigDict(from_attributes=True)
