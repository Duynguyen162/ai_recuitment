import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional , List
class CandidateProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    skills_tags: Optional[List[str]] = []
    years_of_experience: Optional[int] = None

class CandidateProfileResponse(BaseModel):
    id: int 
    user_id: int
    
    # cho phép chuyển đổi từ SQLAlchemy model sang Pydantic model
    model_config = ConfigDict(from_attributes=True)  

