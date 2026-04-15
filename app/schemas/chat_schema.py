from pydantic import BaseModel
from datetime import datetime
from app.core.enum import SenderEnum

class ChatRequest(BaseModel):
    content: str
    job_id: int | None = None
    session_id: int | None = None

class ChatMessageResponse(BaseModel):
    id: int
    sender: SenderEnum
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    session_id: int
    user_message: ChatMessageResponse
    ai_response: ChatMessageResponse