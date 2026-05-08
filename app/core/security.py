from datetime import datetime, timedelta, timezone   
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings
import hashlib

# Khởi tạo thuật toán bcrypt để mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from passlib.context import CryptContext
import hashlib

# Khởi tạo bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Mã hóa mật khẩu  dùng BCrypt"""
    # Giới hạn password tại 72 bytes TRƯỚC khi hash
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu dùng BCrypt"""
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    
    return pwd_context.verify(plain_password, hashed_password)

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