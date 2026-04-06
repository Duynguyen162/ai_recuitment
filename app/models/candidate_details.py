from sqlalchemy import Column, Integer, String, ForeignKey, func,Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import DateTime

class CandidateExperience(Base):
    __tablename__ = "candidate_experiences"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    description = Column(String , nullable=True)

    # back_ref tự động tạo quan hệ ngược (reverse relationship) giữa 2 model mà không cần khai báo ở model còn lại
    candidate = relationship("CandidateProfile", back_populates="experiences")

class CandidateEducation(Base):
    __tablename__ = "candidate_educations"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    
    institution_name = Column(String(255), nullable=False)
    major = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)

    candidate = relationship("CandidateProfile", back_populates="educations")

class CandidateCertification(Base):
    __tablename__ = "candidate_certifications"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False) # tên chứng chỉ
    issuer = Column(String(255), nullable=False) # tổ chức cấp chứng chỉ
    updated_at = Column( DateTime(timezone=True), server_default=func.now()) # ngày cấp chứng chỉ

    candidate = relationship("CandidateProfile", back_populates="certifications")

class CVUpload(Base):
    __tablename__ = "cv_uploads"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)
    
    file_url = Column(Text, nullable=False) # đường dẫn lưu trữ file CV
    file_name = Column(String(255), nullable=False) # tên file CV gốc

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now()) # ngày tải lên CV

    candidate = relationship("CandidateProfile", back_populates="cv_uploads")