import os
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.enum import RoleEnum, StatusEnum
from app.core.security import create_access_token, create_password_reset_token
from app.crud.crud_user import authenticate_user, get_user_by_email, reset_pass
from app.db.database import get_db
from app.models.user import User
from app.schemas.user_schema import ForgotPasswordRequest, ResetPasswordRequest, UserLogin
from app.services.email_service import send_reset_password_email

router = APIRouter(tags=["Auth"])

IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

COOKIE_CONFIG = {
    "key": "access_token",
    "httponly": True,
    "secure": IS_PRODUCTION,
    "samesite": "lax",
    "path": "/",
}

ROLE_COOKIE_CONFIG = {
    "key": "role",
    "httponly": False,
    "secure": IS_PRODUCTION,
    "samesite": "lax",
    "path": "/",
}

def _get_access_token_max_age() -> int:
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def _set_auth_cookie(response: Response, access_token: str,role:str) -> None:
    max_age = _get_access_token_max_age()

    response.set_cookie(
        **COOKIE_CONFIG,
        value=access_token,
        max_age=max_age,
    )
    response.set_cookie(
        **ROLE_COOKIE_CONFIG,
        value=role,
        max_age=max_age,
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_CONFIG["key"],
        path=COOKIE_CONFIG["path"],
        secure=COOKIE_CONFIG["secure"],
        httponly=COOKIE_CONFIG["httponly"],
        samesite=COOKIE_CONFIG["samesite"],
    )
    response.delete_cookie(
        key=ROLE_COOKIE_CONFIG["key"],
        path=ROLE_COOKIE_CONFIG["path"],
        secure=ROLE_COOKIE_CONFIG["secure"],
        httponly=ROLE_COOKIE_CONFIG["httponly"],
        samesite=ROLE_COOKIE_CONFIG["samesite"],
    )

@router.get("/me")
def get_me(current_user: User = Depends(get_current_active_user)):
    avatar_url = None
    name = None
    
    if current_user.role == RoleEnum.candidate and current_user.candidate_profile:
        name = current_user.candidate_profile.full_name
        avatar_url = current_user.candidate_profile.avatar_url
        if avatar_url and not avatar_url.startswith("http"):
            # Chèn BASE_URL (http://localhost:8000) vào trước để Frontend gọi được
            avatar_url = f"{settings.BASE_URL}/{avatar_url}"

    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value,
            "name": name,
            "avatar": avatar_url,
        },
    }


@router.post("/login")
def login(response: Response, request_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, request_in.email, request_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    if user.status != StatusEnum.active:
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")
    
    if user.role == RoleEnum.admin:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=access_token_expires,
    )
    _set_auth_cookie(response, access_token, user.role.value)

    return {
        "success": True,
        "message": "Đăng nhập thành công",
        "data": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
        },
    }

@router.post("/admin/login")
def admin_login(response: Response, request_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, request_in.email, request_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu Admin không đúng")
    
    # Chỉ cho phép Admin
    if user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập trang quản trị")
        
    if user.status != StatusEnum.active:
        raise HTTPException(status_code=403, detail="Tài khoản Admin đã bị khóa")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=access_token_expires,
    )
    _set_auth_cookie(response, access_token, user.role.value)

    return {
        "success": True,
        "message": "Đăng nhập Admin thành công",
        "data": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
        },
    }


@router.post("/logout")
def logout(response: Response):
    _clear_auth_cookie(response)
    return {"success": True, "message": "Đã đăng xuất thành công"}


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
