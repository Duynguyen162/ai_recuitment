from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.config import settings
from app.models.user import User
from app.core.enum import StatusEnum, RoleEnum
from app.models.candidate_profiles import CandidateProfile
from app.core.config import settings

http_bearer = HTTPBearer()

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
        db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(401, "Token không hợp lệ")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "User không tồn tại")
    if user.status == StatusEnum.banned:
        raise HTTPException(403, "User bị khóa")
    return user

http_bearer_optional = HTTPBearer(auto_error=False)
def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer_optional),
    db: Session = Depends(get_db)
) -> User | None:

    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user

def get_current_active_user(
    user: User = Depends(get_current_user)
) -> User:
    """
     Kiểm tra user status = active
    """
    if user.status != StatusEnum.active:
        raise HTTPException(403, "User bị khóa")
    return user

def get_current_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CandidateProfile:
    """
    Dependency cho candidate-only endpoints
    """
    # Kiểm tra role
    if current_user.role != RoleEnum.candidate:
        print(f"User role: {current_user.role}, expected: candidate")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ ứng viên mới được dùng tính năng này"
        )
    
    # Lấy profile
    profile = db.query(CandidateProfile).filter(
        CandidateProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        print(f"Candidate profile not found for user: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng cập nhật thông tin cá nhân (Profile) trước"
        )
    
    print(f"Candidate profile found: {profile.id}")
    return profile