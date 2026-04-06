import enum

class RoleEnum(enum.Enum):
    candidate = "candidate"
    hr_manager = "hr_manager"
    admin = "admin"

class StatusEnum(enum.Enum):
    active = "active"
    banned = "banned"
    deleted = "deleted"

