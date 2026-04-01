from sqlalchemy import Column, Integer, String, Enum, DateTime ,ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String, nullable=True , default="")
    phone = Column(String, nullable=True , default="")
    bio = Column(String, nullable=True , default="")
    avatar_url = Column(String, nullable=True , default="")
    portfolio_url = Column(String, nullable=True , default="")
    linkedin_url = Column(String, nullable=True , default="")
    github_url = Column(String, nullable=True , default="")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # thiết lập quan hệ 1-1 với User
    user = relationship("User", back_populates="candidate_profile")
    
    #Tác dụng lớn nhất của relationship:
    # - JOIN tự động
    # - lazy loading
    # - cascade delete
    # - truy cập object trực tiếp