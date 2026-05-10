import enum

class RoleEnum(str ,enum.Enum):
    candidate = "candidate"
    hr_manager = "hr_manager"
    admin = "admin"

class StatusEnum(str ,enum.Enum):
    active = "active"
    banned = "banned"
    deleted = "deleted"
    
class CompanyVerificationStatusEnum( str ,enum.Enum):
    """áp dụng cho bảng companies xem có được đăng tin tuyển dụng hay không"""
    pending = "pending"   
    approved = "approved"
    rejected = "rejected" 
    locked = "locked"     

class VerificationLogStatusEnum(str ,enum.Enum):
    """áp dụng cho company_verifications"""
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class JobTypeEnum(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    remote = "remote"

class JobStatusEnum(str, enum.Enum):
    draft = "draft"          
    published = "published"   
    paused = "paused"         
    closed = "closed" 

class ApplicationStatusEnum(str ,enum.Enum):
    pending = "pending"
    review = "review"
    interviewing = "interviewing"
    hired = "hired"
    rejected = "rejected"
    withdrawn = "withdrawn"
    left_company = "left_company"

class SenderEnum(str , enum.Enum):
    user = "user"
    ai = "ai"

class VipEnum(str ,enum.Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"

class DocumentStatus(str, enum.Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"
