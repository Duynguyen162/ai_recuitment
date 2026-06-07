from pydantic import BaseModel
from datetime import datetime
from app.core.enum import CompanyVerificationStatusEnum, DocumentStatus, VerificationLogStatusEnum, VipEnum

# BẢNG COMPANIES
class CompanyBase(BaseModel):
    name: str
    logo_url: str | None = None
    size: str | None = None
    website: str | None = None
    description: str | None = None
    is_vip: bool | None = None
    vip_expire_at: datetime | None = None

class CompanyCreate(CompanyBase):
    pass
class CompanyRegisterRequest(CompanyCreate):
    license_url: str
    
class CompanyUpdate(BaseModel):
    name: str | None = None
    logo_url: str | None = None
    size: str | None = None
    website: str | None = None
    description: str | None = None
    verification_status: CompanyVerificationStatusEnum | None = None

class CompanyResponse(CompanyBase):
    id: int
    verification_status: CompanyVerificationStatusEnum
    license_url: str | None = None
    created_at: datetime
    vip_remaining_days: int | None = None

    class Config:
        from_attributes = True

class PublicCompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    follower_count: int = 0
    is_followed: bool = False

    class Config:
        from_attributes = True
        
class CompanyFollowResponse(BaseModel):
    is_followed: bool
    follower_count: int

# BẢNG COMPANY_VERIFICATIONS

class CompanyVerificationCreate(BaseModel):
    license_url: str

class CompanyVerificationUpdate(BaseModel):
    status: VerificationLogStatusEnum
    reviewed_by: int # ID của Admin duyệt

class CompanyVerificationResponse(BaseModel):
    id: int
    company_id: int
    reviewed_by: int | None = None
    license_url: str
    status: VerificationLogStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

# BẢNG COMPANY_MEMBERS
class CompanyMemberResponse(BaseModel):
    id: int
    company_id: int
    user_id: int
    joined_at: datetime

    class Config:
        from_attributes = True


# BẢNG COMPANY_DOCUMENTS
class CompanyDocumentCreate(BaseModel):
    file_url: str

class CompanyDocumentResponse(BaseModel):
    id: int
    company_id: int
    upload_by_id: int | None = None
    file_url: str
    created_at: datetime
    updated_at: datetime
    status: DocumentStatus
    class Config:
        from_attributes = True
        
class VerifyRequest(BaseModel):
    status: VerificationLogStatusEnum
    reason: str | None = None

class LockRequest(BaseModel):
    status: CompanyVerificationStatusEnum
    reason: str | None = None

class ResubmitVerificationRequest(BaseModel):
    license_url: str

