from sqlalchemy import BIGINT, Boolean, Column, ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")
