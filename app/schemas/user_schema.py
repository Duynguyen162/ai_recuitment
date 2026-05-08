from app.models.user import RoleEnum
import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class PasswordValidatorMixin:
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,50}$"
        if not re.match(pattern, v):
            raise ValueError("Mật khẩu phải có chữ hoa, chữ thường, số và ký tự đặc biệt")
        return v
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(PasswordValidatorMixin, BaseModel):
    token: str
    password: str = Field(..., min_length=8, max_length=50)

class UserCreate(PasswordValidatorMixin , BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=50)
    role: RoleEnum

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    status: str

    class Config:
        from_attributes = True