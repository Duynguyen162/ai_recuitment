from datetime import datetime
from pydantic import BaseModel
from app.core.enum import ApplicationStatusEnum


class ApplicationCreate(BaseModel):
    job_id: int

class ApplicationResponse(BaseModel):
    id: int 
    job_id: int
    candidate_id: int
    status: ApplicationStatusEnum
    applied_at: datetime

    class Config:
        from_attributes = True