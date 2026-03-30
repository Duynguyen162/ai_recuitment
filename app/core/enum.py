import enum

class RoleEnum(enum.Enum):
    candidate = "candidate"
    hr_manager = "hr_manager"
    hr_staff = "hr_staff"
    admin = "admin"

class StatusEnum(enum.Enum):
    active = "active"
    banned = "banned"
    deleted = "deleted"
