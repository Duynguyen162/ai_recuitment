from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.models.user import User
from app.core.enum import StatusEnum
from app.models.candidate_profiles import CandidateProfile
from app.core.enum import RoleEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
# check token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Không thể xác thực thông tin.)",
        headers = {"WWW-Authenticate": "Bearer"},
    )
    """
    Dependency dùng để kiểm tra token và lấy thông tin user hiện tại.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub") #sub là user_id đã được mã hóa trong token
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

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