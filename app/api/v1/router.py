from fastapi import APIRouter

from app.api.v1.endpoints import admin, admin_dashboard, application, auth, companies, public_companies, dashboard, interview, jobs, notifications, profiles, register, upload

api_router = APIRouter()

api_router.include_router(register.router, prefix="/auth")
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(profiles.router, prefix="/profiles")
api_router.include_router(upload.router, prefix="/upload")
api_router.include_router(companies.router, prefix="/companies")
api_router.include_router(public_companies.router, prefix="/public/companies")
api_router.include_router(admin.router, prefix="/admin")
api_router.include_router(admin_dashboard.router, prefix="/admin")
api_router.include_router(jobs.router, prefix="/job")
api_router.include_router(application.router, prefix="/application")
api_router.include_router(interview.router, prefix="/interview")
api_router.include_router(notifications.router, prefix="/notifications")
api_router.include_router(dashboard.router, prefix="/hr/dashboard", tags=["HR Dashboard"])
