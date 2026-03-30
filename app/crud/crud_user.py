from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.core.logger import logger
from app.core.security import get_password_hash

def create_user(db: Session , user_in: UserCreate):
    try:
        db_user = User(
            email = user_in.email,
            password_hash = get_password_hash(user_in.password),
            role = user_in.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Tạo người dùng mới thành công: {db_user.email}")
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Lỗi khi tạo người dùng: {user_in.email} - {str(e)}")
        raise ValueError("Không thể tạo người dùng. Email có thể đã tồn tại.")
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi không xác định khi tạo người dùng: {user_in.email} - {str(e)}", exc_info=True)
        raise e