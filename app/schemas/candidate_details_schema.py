from pydantic import BaseModel
from pydantic import ConfigDict

# bảng candidate_experiences
class CandidateExperienceCreate(BaseModel):
    company_name: str | None = None
    job_title: str | None = None
    description: str | None = None

class CandidateExperienceResponse(BaseModel):
    id: int
    candidate_id: int
    company_name: str | None = None
    job_title: str | None = None
    description: str | None = None

    # cho phép chuyển đổi từ SQLAlchemy model sang Pydantic model
    model_config = ConfigDict(from_attributes=True) 

# bảng candidate_educations
class CandidateEducationCreate(BaseModel):
    institution_name: str | None = None
    major: str | None = None
    degree: str | None = None

class CandidateEducationResponse(BaseModel):
    id: int
    candidate_id: int
    institution_name: str | None = None
    major: str | None = None
    degree: str | None = None

    model_config = ConfigDict(from_attributes=True)

# bảng candidate_certifications
class CandidateCertificationCreate(BaseModel):
    name: str | None = None
    issuer: str | None = None

class CandidateCertificationResponse(BaseModel):
    id: int
    candidate_id: int
    name: str | None = None
    issuer: str | None = None
    model_config = ConfigDict(from_attributes=True)


# bảng cv_uploads
class CVUploadCreate(BaseModel):
    file_url: str | None = None
    file_name: str | None = None

class CVUploadResponse(BaseModel):
    id: int
    candidate_id: int
    file_url: str | None = None
    file_name: str | None = None
    model_config = ConfigDict(from_attributes=True)
