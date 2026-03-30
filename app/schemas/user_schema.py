from pydantic import BaseModel, ConfigDict, EmailStr , Field
from typing import Optional
from app.models.user import RoleEnum

# dữ liệu client gửi lên khi đăng ký tài khoản mới
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6 ,max_length=50)  # mật khẩu tối thiểu 6 ký tự
    role: Optional[RoleEnum] = RoleEnum.candidate

# dữ liệu trả về
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: RoleEnum
    status: str

    # cho phép chuyển đổi từ SQLAlchemy model sang Pydantic model
    model_config = ConfigDict(from_attributes=True)  