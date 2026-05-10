from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.notifications import Notification


def create_notification(db: Session, user_id: int, title: str, body: str) -> Notification:
    notification = Notification(user_id=user_id, title=title, body=body)
    db.add(notification)
    db.flush()
    return notification


def list_my_notifications(db: Session, user_id: int) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.id.desc())
        .all()
    )


def mark_as_read(db: Session, user_id: int, notification_id: int) -> Notification:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Khong tim thay thong bao")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_as_read(db: Session, user_id: int) -> int:
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .all()
    )
    for notification in notifications:
        notification.is_read = True
    db.commit()
    return len(notifications)
