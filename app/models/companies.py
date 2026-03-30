import enum
from sqlalchemy import Column, Integer, String, DateTime ,Enum
from sqlalchemy.sql import func
from app.db.base import Base

class VerificationStatusEnum(enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    locked = "locked"

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    logo_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    size = Column(String, nullable=True)
    website = Column(String, nullable=True)
    verification_status = Column(Enum(VerificationStatusEnum), default=VerificationStatusEnum.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
