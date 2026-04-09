import enum
from app.models.user import User
from sqlalchemy import BIGINT, Column, Integer, String, DateTime ,Enum,ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.enum import VerificationLogStatusEnum ,CompanyVerificationStatusEnum
from app.db.base import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(BIGINT, primary_key=True, index=True,autoincrement=True)
    name = Column(String, unique=True, index=True)
    logo_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    size = Column(String, nullable=True)
    website = Column(String, nullable=True)
    verification_status = Column(Enum(CompanyVerificationStatusEnum), default=CompanyVerificationStatusEnum.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    verifications = relationship(
        "CompanyVerification",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    members = relationship(
        "CompanyMember",
        back_populates="company",
        cascade="all, delete-orphan"
    )

    documents = relationship(
        "CompanyDocument",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    job_postings = relationship(
        "JobPosting",
        back_populates="company",
        cascade="all, delete-orphan"
    )

class CompanyVerification(Base):
    __tablename__ = "company_verifications"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(BIGINT, ForeignKey("companies.id", ondelete="CASCADE") , nullable=False)
    reviewed_by = Column(BIGINT,ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    license_url = Column(String , nullable=False)
    status = Column(Enum(VerificationLogStatusEnum), default=VerificationLogStatusEnum.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    company = relationship("Company", back_populates="verifications")

class CompanyMember(Base):
    __tablename__ = "company_members"
    id = Column(BIGINT, primary_key=True, index=True,autoincrement=True)
    company_id = Column(BIGINT, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company = relationship("Company", back_populates="members")
    user = relationship("User", back_populates="company_memberships")

class CompanyDocument(Base):
    __tablename__ = "company_documents"
    id = Column(BIGINT, primary_key=True, index=True, autoincrement=True)
    company_id = Column(BIGINT, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    upload_by_id = Column(BIGINT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    file_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)

    company = relationship("Company", back_populates="documents")
