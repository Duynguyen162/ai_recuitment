# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user_schema import UserResponse
from app.schemas.base_schema import ResponseSchema
from app.models.user import User
from app.api.deps import get_current_active_user # Import dependency vừa viết

router = APIRouter()

# API lấy thông tin của CHÍNH MÌNH (yêu cầu đăng nhập)
@router.get("/me", response_model=ResponseSchema[UserResponse])

def read_users_me(
    current_user: User = Depends(get_current_active_user) # BẮT BUỘC PHẢI CÓ TOKEN
):
    """
    Lấy thông tin tài khoản đang đăng nhập. 
    FastAPI tự động trích xuất token, giải mã và trả về current_user.
    """
    return {
        "success": True,
        "data": current_user,
        "error": None,
        "meta": None
    }