from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.core.logger import logger
from app.core.security import get_password_hash
from app.models.candidate_profiles import CandidateProfile
from app.core.enum import RoleEnum

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