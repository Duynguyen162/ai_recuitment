from datetime import datetime

from pydantic import BaseModel


class InterviewCreate(BaseModel):
    application_id: int
    interview_time: datetime
    meeting_link: str | None = None
    location: str | None = None
    notes: str | None = None

class InterviewUpdateNote(BaseModel):
    notes: str | None = None

class InterviewUpdate(BaseModel):
    interview_time: datetime
    meeting_link: str | None = None
    location: str | None = None
    notes: str | None = None


class InterviewResponse(BaseModel):
    id: int
    application_id: int
    interviewer_id: int
    interview_time: datetime
    meeting_link: str | None = None
    location: str | None = None
    notes: str | None = None

    class Config:
        from_attributes = True
