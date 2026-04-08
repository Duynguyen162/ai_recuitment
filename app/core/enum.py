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
