from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.core.enum import RoleEnum
from app.schemas.base_schema import ResponseSchema

from app.schemas.dashboard_schema import (
    DashboardStatsResponse,
    DashboardPendingApplication,
    DashboardUpcomingInterview,
    DashboardActiveJob
)
from app.crud import crud_dashboard

router = APIRouter()

def verify_hr_role(current_user: User):
    if current_user.role != RoleEnum.hr_manager:
        raise HTTPException(
            status_code=403,
            detail="Chỉ HR Manager mới có quyền xem Dashboard"
        )

@router.get(
    "/stats",
    response_model=ResponseSchema[DashboardStatsResponse],
    summary="Lấy số liệu tổng quan cho HR Dashboard"
)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_hr_role(current_user)
    stats = crud_dashboard.get_dashboard_stats(db, current_user)
    return ResponseSchema(
        success=True,
        data=stats,
        error=None,
        meta=None
    )

@router.get(
    "/pending-applications",
    response_model=ResponseSchema[List[DashboardPendingApplication]],
    summary="Lấy danh sách ứng viên cần xử lý"
)
def get_pending_applications(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_hr_role(current_user)
    applications = crud_dashboard.get_pending_applications(db, current_user, limit=limit)
    return ResponseSchema(
        success=True,
        data=applications,
        error=None,
        meta=None
    )

@router.get(
    "/upcoming-interviews",
    response_model=ResponseSchema[List[DashboardUpcomingInterview]],
    summary="Lấy danh sách lịch phỏng vấn sắp tới"
)
def get_upcoming_interviews(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_hr_role(current_user)
    interviews = crud_dashboard.get_upcoming_interviews(db, current_user, limit=limit)
    return ResponseSchema(
        success=True,
        data=interviews,
        error=None,
        meta=None
    )

@router.get(
    "/active-jobs",
    response_model=ResponseSchema[List[DashboardActiveJob]],
    summary="Lấy danh sách tin tuyển dụng đang hoạt động"
)
def get_active_jobs(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_hr_role(current_user)
    jobs = crud_dashboard.get_active_jobs(db, current_user, limit=limit)
    return ResponseSchema(
        success=True,
        data=jobs,
        error=None,
        meta=None
    )
