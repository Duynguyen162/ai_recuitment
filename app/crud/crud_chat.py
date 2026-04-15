from sqlalchemy.orm import Session
from app.models.chat_messages import ChatMessage
from app.models.chat_sessions import ChatSession
from app.core.enum import SenderEnum

# def get_or_creat_session(db: Session, candidate_id: int, session_id: int | None = None, job_id: int | None = None):
