import os
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.enum import RoleEnum, StatusEnum
from app.crud.crud_user import authenticate_user, get_user_by_email, reset_pass
from app.db.database import get_db
from app.core.security import create_access_token, create_password_reset_token
from app.models.user import User
from app.schemas.user_schema import ForgotPasswordRequest, ResetPasswordRequest, UserLogin
from fastapi import BackgroundTasks
from app.services.email_service import send_reset_password_email
from app.api.deps import get_current_active_user

router = APIRouter(tags=["Auth"])

# Đọc từ env để dễ switch giữa dev và production
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

# Cookie config tập trung — tránh không nhất quán giữa login/logout
COOKIE_CONFIG = {
    "key": "access_token",
    "httponly": True,
    "secure": IS_PRODUCTION,       # False ở dev (HTTP), True ở prod (HTTPS)
    "samesite": "lax",             # "lax" hoạt động tốt khi same-origin qua proxy
    "path": "/",
}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_active_user)):
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value,
            "name": (
                current_user.candidate_profile.full_name
                if current_user.role == RoleEnum.candidate
                else None
            ),
        },
    }


@router.post("/login")
def login(response: Response, request_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, request_in.email, request_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    if user.status != StatusEnum.active:
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    
    return {
        "success": True,
        "data": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "token": access_token,
        }
    }

@router.post("/logout")
def logout():
    return {"success": True, "message": "Đã đăng xuất"}


@router.post("/forgot-password")
def forgot_password(
    request_in: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, request_in.email)
    if user:
        token = create_password_reset_token(user.email)
        reset_link = f"http://localhost:3000/auth/reset-password?token={token}"
        background_tasks.add_task(send_reset_password_email, user.email, reset_link)

    return {
        "success": True,
        "message": "Nếu email tồn tại trong hệ thống, chúng tôi đã gửi một liên kết khôi phục mật khẩu. Vui lòng kiểm tra hộp thư.",
    }


@router.post("/reset-password")
def reset_password(request_in: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_pass(db, request_in)
    return {"success": True, "message": "Đặt lại mật khẩu thành công"}
