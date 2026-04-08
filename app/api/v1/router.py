from fastapi import APIRouter
from app.api.v1.endpoints import register, auth , profiles,companies,admin

api_router = APIRouter()

api_router.include_router(register.router, prefix="/auth", tags=["Auth"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles Candidate"])
api_router.include_router(companies.router, prefix="/companies",tags=["Company"])
api_router.include_router(admin.router, prefix="/admin",tags=["Admin Verify"])

