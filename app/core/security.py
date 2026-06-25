from fastapi import HTTPException
from datetime import datetime, timedelta, timezone   
from typing import Optional
from jose import jwt, JWTError
from app.core.config import settings
import hashlib
import bcrypt

def get_password_hash(password: str) -> str:
    """Mã hóa mật khẩu dùng BCrypt"""
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu không được vượt quá 72 bytes"
        )
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu dùng BCrypt"""
    plain_bytes = plain_password.encode("utf-8")
    if len(plain_bytes) > 72:
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu không được vượt quá 72 bytes"
        )
    try:
        return bcrypt.checkpw(plain_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

# Tạo token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = data.copy()
    to_encode.update({"exp": expire}) 

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Reset password
RESET_TOKEN_EXPIRE_MINUTES = 15 

def create_password_reset_token(email: str) -> str:
    """Tạo token chuyên dụng cho việc reset mật khẩu"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": email, "type": "reset_password"} 
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password_reset_token(token: str) -> str | None:
    """Giải mã token và trả về email nếu hợp lệ"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "reset_password":
            return None
        return payload.get("sub")
    except JWTError:
        return None