from fastapi import APIRouter
from app.api.v1.endpoints import register, auth , profiles

api_router = APIRouter()

api_router.include_router(register.router, prefix="/auth", tags=["Auth"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles Candidate"])

