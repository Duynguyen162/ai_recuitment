from sqlalchemy import  DateTime, Enum, Integer
from sqlalchemy import BIGINT, Column, ForeignKey, func,Text
from sqlalchemy.orm import relationship
from app.core.enum import SenderEnum
from app.db.base import Base
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(BIGINT, primary_key=True, index=True)
    session_id = Column(BIGINT, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    sender = Column(Enum(SenderEnum), nullable=False)
    content = Column(Text, nullable=False)
    # Lưu số lượng token mà LLM đã tiêu thụ (chỉ áp dụng khi sender = 'ai')
    tokens_used = Column(Integer, nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")