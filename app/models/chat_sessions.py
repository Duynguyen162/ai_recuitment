from sqlalchemy import DateTime
from sqlalchemy import BIGINT, Column, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    application_id = Column(BIGINT, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(BIGINT, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    application = relationship("Application", back_populates="chat_sessions")
    job = relationship("JobPosting", back_populates="chat_sessions")

    # Một phiên chat có nhiều tin nhắn, xóa phiên thì xóa hết tin nhắn
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

