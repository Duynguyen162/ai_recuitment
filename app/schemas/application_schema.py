from datetime import datetime
from pydantic import BaseModel
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
    status: str
    applied_at: datetime
    cv_type: str
    cv_id: int | None = None
    cv_name:str 
    class Config:
        from_attributes = True