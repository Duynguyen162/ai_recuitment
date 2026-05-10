from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import crud_notification
from app.db.database import get_db
from app.models.user import User
from app.schemas.base_schema import ResponseSchema
from app.schemas.notification_schema import NotificationResponse

router = APIRouter(tags=["Notifications"])


@router.get(
    "/my",
    response_model=ResponseSchema[List[NotificationResponse]],
    summary="Lay danh sach thong bao cua toi",
)
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = crud_notification.list_my_notifications(db, current_user.id)
    return ResponseSchema(success=True, data=data, error=None, meta=None)


@router.patch(
    "/{notification_id}/read",
    response_model=ResponseSchema[NotificationResponse],
    summary="Danh dau da doc mot thong bao",
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = crud_notification.mark_as_read(db, current_user.id, notification_id)
    return ResponseSchema(success=True, data=data, error=None, meta=None)


@router.patch(
    "/read-all",
    response_model=ResponseSchema[dict],
    summary="Danh dau da doc tat ca thong bao",
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = crud_notification.mark_all_as_read(db, current_user.id)
    return ResponseSchema(success=True, data={"updated": updated}, error=None, meta=None)
