from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token

router = APIRouter()
@router.post("/login")

def login(db: Session = Depends(get_db) , form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(User).filter(User.email == form_data.username).first() #tìm user bằng email

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, 
                            detail="Email hoặc mật khẩu không đúng" , 
                            headers={"WWW-Authenticate": "Bearer"})
    if user.status.value != "active":
        raise HTTPException(status_code=403, detail="Tài khoản bị khóa")
    # sinh token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}   