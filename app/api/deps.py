from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyCookie
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.models.user import User
from app.core.enum import StatusEnum
from app.models.candidate_profiles import CandidateProfile
from app.core.enum import RoleEnum

cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)

# check token
def get_current_user(request: Request, 
                     token_str: str = Depends(cookie_scheme), db: 
                     Session = Depends(get_db)) -> User:
    """
    Dependency dùng để kiểm tra token và lấy thông tin user hiện tại.
    """
    # Swagger UI sẽ truyền token_str vào, hoặc lấy trực tiếp từ request
    token_str = token_str or request.cookies.get("access_token")

    if not token_str:
        raise HTTPException(status_code=401, detail="Bạn chưa đăng nhập")
    # Cắt bỏ chữ "Bearer "
    token = token_str.split(" ")[1] if "Bearer" in token_str else token_str
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub") #sub là user_id đã được mã hóa trong token
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Người dùng không còn tồn tại")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency dùng để kiểm tra trạng thái của user hiện tại. 
    Chỉ cho phép user có trạng thái active truy cập.
    
    """
    if current_user.status != StatusEnum.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đã bị khóa.",
        )
    return current_user


def get_current_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CandidateProfile:
    """
    Dependency dùng chung cho mọi API của Ứng viên.
    Tự động kiểm tra quyền và trả về profile gốc.
    """
    if current_user.role != RoleEnum.candidate:
        raise HTTPException(status_code=403, detail="Chỉ ứng viên mới được dùng tính năng này")
        
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(status_code=400, detail="Vui lòng cập nhật thông tin cá nhân (Profile) trước")
        
    return profile