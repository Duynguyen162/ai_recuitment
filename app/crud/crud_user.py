from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.schemas.user_schema import ResetPasswordRequest, UserCreate
from app.core.logger import logger
from app.core.security import get_password_hash, verify_password
from app.models.candidate_profiles import CandidateProfile
from app.core.enum import RoleEnum
from jose import JWTError, jwt
from app.core.config import settings

def create_user(db: Session , user_in: UserCreate):
    try:
        if user_in.role == RoleEnum.admin:
            raise HTTPException(status_code=403, detail=" không thể đăng kí role này")
        
        db_user = User(
            email = user_in.email,
            password_hash = get_password_hash(user_in.password),
            role = user_in.role
        )
       
        db.add(db_user)
        db.flush()# Tạo id cho user mà chưa commit
        if user_in.role == RoleEnum.hr_manager:
            logger.info(f"tạo tài khoản hr thành công")
        elif user_in.role == RoleEnum.candidate:
            logger.info(f"tạo tài khoản ứng viên thành công")
        
        #tạo luôn profile ứng viên nếu role là candidate
        if user_in.role == RoleEnum.candidate:
            db_profile = CandidateProfile(
                user_id=db_user.id
            )
            db.add(db_profile)
    
        db.commit()
        db.refresh(db_user)

        if user_in.role == RoleEnum.candidate:
            db.refresh(db_profile)    # refresh profile nếu cần
            logger.info(f"Tạo hồ sơ ứng viên thành công: {db_profile.id}")
        
        return db_user
    
    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Lỗi khi tạo người dùng: {user_in.email} - {str(e)}")
        raise ValueError("Không thể tạo người dùng. Email có thể đã tồn tại.")
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi không xác định khi tạo người dùng: {user_in.email} - {str(e)}", exc_info=True)
        raise e

def reset_pass(db: Session, request_in: ResetPasswordRequest):
    """ Xử lý reset mật khẩu:
        1. Giải mã token để lấy email
        2. Kiểm tra token hợp lệ và chưa hết hạn
        3. Tìm user theo email
        4. Cập nhật mật khẩu mới (đã hash) và lưu vào DB
    """
    try:
        payload = jwt.decode(
            request_in.token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        if not email or payload.get("type") != "reset_password":
            raise HTTPException(status_code=400, detail="Token không hợp lệ")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token không hợp lệ hoặc đã hết hạn")

    user = db.query(User).filter(User.email == email).first()
    if user:
        user.password_hash = get_password_hash(request_in.password)
        db.commit()

def authenticate_user(db: Session, email: str, password: str):
    """ Xác thực người dùng:
        1. Tìm user theo email
        2. Nếu không tìm thấy, trả về False
        3. Nếu tìm thấy, so sánh mật khẩu nhập vào với mật khẩu đã hash trong DB
        4. Nếu khớp, trả về user; nếu không khớp, trả về False
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    # So sánh mật khẩu người dùng nhập vào với mật khẩu đã băm trong DB
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()