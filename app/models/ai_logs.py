from sqlalchemy import BIGINT, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class AiLog(Base):
    """Ghi lại mỗi lần gọi dịch vụ AI (matching, chatbot, jd_moderation...)."""
    __tablename__ = "ai_logs"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    service_type = Column(String(50), nullable=False, index=True)  # matching | chatbot | jd_moderation
    application_id = Column(BIGINT, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    is_error = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    application = relationship("Application", backref="ai_logs")


class AiAlertConfig(Base):
    """Cấu hình ngưỡng cảnh báo cho hệ thống AI."""
    __tablename__ = "ai_alert_configs"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    metric = Column(String(50), nullable=False)   # error_rate | avg_latency | daily_tokens
    threshold = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
