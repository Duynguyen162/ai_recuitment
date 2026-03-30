from fastapi import APIRouter, Depends, HTTPException
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
        return {
            "success": True,
            "data": new_user,
            "error": None,
            "meta": None
        }
    except ValueError as ve:
        return{
            "success": False,
            "data": None,
            "error": str(ve),
            "meta": None
        }
