from datetime import datetime, timedelta , timezone   
from typing import Optional
from jose import jwt ,JWTError
from passlib.context import CryptContext
from app.core.config import settings

#khởi tạo thuật toán bcrypt để mã hóa mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password) # check mk khớp với mã băm ko

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) # mã hóa mk

# Tạo token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Tạo bản sao dict để tránh sửa dữ liệu gốc
    to_encode = data.copy()
    to_encode.update({"exp": expire}) 

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# reset pass
RESET_TOKEN_EXPIRE_MINUTES = 15 

def create_password_reset_token(email: str) -> str:
    """Tạo token chuyên dụng cho việc reset mật khẩu"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    # Thêm trường "type" để phân biệt với token đăng nhập
    to_encode = {"exp": expire, "sub": email, "type": "reset_password"} 
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password_reset_token(token: str) -> str | None:
    """Giải mã token và trả về email nếu hợp lệ"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Kiểm tra xem đây có đúng là token dùng để reset pass không
        if payload.get("type") != "reset_password":
            return None
        return payload.get("sub") # Trả về email
    except JWTError:
        return None