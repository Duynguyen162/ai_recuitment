from sqlalchemy import Column, Integer, String, Enum, DateTime ,ForeignKey
from sqlalchemy.dialects.postgresql import JSONB 
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
    skilltags = Column(JSONB, default=list, nullable=True)
    years_of_experience = Column(Integer, nullable=True , default=0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # thiết lập quan hệ 1-1 với User
    user = relationship("User", back_populates="candidate_profile")
    # thiết lập quan hệ 1-n với CandidateExperience
    experiences = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan")
    educations = relationship("CandidateEducation", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("CandidateCertification", back_populates="candidate", cascade="all, delete-orphan")
    cv_uploads = relationship("CVUpload", back_populates="candidate", cascade="all, delete-orphan")
    #Tác dụng lớn nhất của relationship:
    # - JOIN tự động
    # - lazy loading
    # - cascade delete
    # - truy cập object trực tiếp