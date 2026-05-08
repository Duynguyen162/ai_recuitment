from fastapi import APIRouter
from app.api.v1.endpoints import register, auth , profiles,companies,admin,upload,jobs,application

api_router = APIRouter()

api_router.include_router(register.router, prefix="/auth", tags=["Auth"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles Candidate"])
api_router.include_router(upload.router, prefix="/upload",tags=["API upload file"])
api_router.include_router(companies.router, prefix="/companies",tags=["Manager Company"])
api_router.include_router(admin.router, prefix="/admin",tags=["Admin Verify company"])
api_router.include_router(jobs.router, prefix="/job",tags=["Job Posting"])
api_router.include_router(application.router, prefix="/application",tags=["Application"])