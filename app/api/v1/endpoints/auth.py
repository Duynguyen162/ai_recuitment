from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.enum import StatusEnum
from app.crud.crud_user import authenticate_user, get_user_by_email, reset_pass
from app.db.database import get_db
from app.core.security import create_access_token, create_password_reset_token
from app.models.user import User
from app.schemas.user_schema import ForgotPasswordRequest, ResetPasswordRequest, UserLogin
from fastapi import BackgroundTasks
from app.services.email_service import send_reset_password_email


router = APIRouter()

@router.post("/login")
def login(response: Response, request_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, request_in.email, request_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    if user.status != StatusEnum.active:
        raise HTTPException(status_code=403, detail="Tài khoản của bạn đã bị khóa")
    # Tạo JWT Token
    access_token = create_access_token(data={"sub": str(user.id)})

    # GẮN COOKIE BẢO MẬT
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,  # Chống XSS (JS không đọc được)
        secure=False,   # Đặt là True nếu chạy thực tế với HTTPS, False nếu test localhost
        samesite="lax", # Chống CSRF (Chỉ gửi cookie nếu cùng domain)
        max_age=86400   # Thời gian sống (1 ngày)
    )

    return {"success": True, "message": "Đăng nhập thành công"} 

@router.post("/logout")
def logout(response: Response):
    # Ghi đè cookie cũ bằng một cookie trống và cho hết hạn ngay lập tức
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,
        samesite="lax"
    )
    return {"success": True, "message": "Đã đăng xuất"}


@router.post("/forgot-password")
def forgot_password(
    request_in: ForgotPasswordRequest,
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, request_in.email)
    
    if user:
        token = create_password_reset_token(user.email)
        reset_link = f"http://localhost:3000/auth/reset-password?token={token}"
        
        # đây là hàm async và sẽ ném vào event loop chạy ngầm
        background_tasks.add_task(send_reset_password_email, user.email, reset_link)
        
    return {
        "success": True, 
        "message": "Nếu email tồn tại trong hệ thống, chúng tôi đã gửi một liên kết khôi phục mật khẩu. Vui lòng kiểm tra hộp thư."
    }

@router.post("/reset-password")
def reset_password(
    request_in: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    reset_pass(db, request_in)
    return {"success": True, "message": "Đặt lại mật khẩu thành công"}
    