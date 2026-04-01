from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user_schema import UserCreate, UserResponse
from app.schemas.base_schema import ResponseSchema
from app.crud import crud_user


router = APIRouter()

@router.post("/register", response_model=ResponseSchema[UserResponse])
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = crud_user.create_user(db, user_in)
        return ResponseSchema(
            success=True,
            data= new_user,
            error=None,
            meta=None
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."
        )
