from app.schemas.interview_schema import InterviewUpdateNote
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import crud_interview, crud_notification
from app.db.database import get_db
from app.models.user import User
from app.schemas.base_schema import ResponseSchema
from app.schemas.interview_schema import InterviewCreate, InterviewResponse, InterviewUpdate

router = APIRouter(tags=["Interview schedule"])


def _create_schedule_message(interview: InterviewResponse, action: str) -> tuple[str, str]:
    title = "Lịch phỏng vấn đã được cập nhật" if action == "updated" else "Bạn có lịch phỏng vấn mới"
    body = f"Lịch phỏng vấn cho hồ sơ #{interview.application_id} vào lúc {interview.interview_time.isoformat()}."
    return title, body


@router.post(
    "/schedules",
    response_model=ResponseSchema[InterviewResponse],
    summary="HR tạo lịch phỏng vấn và chuyển trạng thái hồ sơ sang interviewing",
)
def create_interview(
    detail_interview: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = crud_interview.create_interview(db, current_user, detail_interview)
        candidate_user_id = data.application.candidate_profile.user_id
        title, body = _create_schedule_message(data, "created")
        crud_notification.create_notification(db, candidate_user_id, title, body)
        db.commit()
        db.refresh(data)
        return ResponseSchema(success=True, data=data, error=None, meta=None)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi hệ thống")


@router.put(
    "/schedules/{candidate_id}",
    response_model=ResponseSchema[InterviewResponse],
    summary="HR cập nhật lại thời gian phỏng vấn và gửi thông báo mới",
)
def update_interview(
    candidate_id: int,
    payload: InterviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = crud_interview.update_interview(db, current_user, candidate_id, payload)
        return ResponseSchema(success=True, data=data, error=None, meta=None)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi hệ thống")


@router.get(
    "/schedules/{interview_id}",
    response_model=ResponseSchema[InterviewResponse],
    summary="Lấy chi tiết lịch phỏng vấn",
)
def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = crud_interview.get_interview_by_id(db, current_user, interview_id)
    return ResponseSchema(success=True, data=data, error=None, meta=None)


@router.get(
    "/application/{application_id}",
    response_model=ResponseSchema[List[InterviewResponse]],
    summary="Lấy danh sách lịch phỏng vấn theo hồ sơ",
)
def list_interviews_by_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = crud_interview.list_interviews_by_application(db, current_user, application_id)
    return ResponseSchema(success=True, data=data, error=None, meta=None)


@router.get(
    "/my-schedules",
    response_model=ResponseSchema[List[InterviewResponse]],
    summary="Lấy danh sách lịch phỏng vấn của tôi",
)
def list_my_interviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = crud_interview.list_my_interviews(db, current_user)
    return ResponseSchema(success=True, data=data, error=None, meta=None)

@router.put(
    "/schedules/{application_id}/note",
    response_model=ResponseSchema[InterviewResponse],
    summary="HR cập nhật ghi chú phỏng vấn",
)
def update_interview_note(
    application_id: int,
    payload: InterviewUpdateNote,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = crud_interview.update_interview_note(db, current_user, application_id, payload)
        return ResponseSchema(success=True, data=data, error=None, meta=None)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi hệ thống")