from pydantic import BaseModel
from datetime import datetime
from app.core.enum import SenderEnum

class ChatRequest(BaseModel):
    message: str
    job_id: int

class ChatMessageResponse(BaseModel):
    id: int
    sender: SenderEnum
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: str
    sender: SenderEnum
    text: str
    timestamp: datetime