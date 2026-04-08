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
    pending = "pending"   
    approved = "approved"
    rejected = "rejected" 
    locked = "locked"     

class VerificationLogStatusEnum(str ,enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
