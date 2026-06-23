from datetime import datetime
from app.core.enum import SenderEnum
from app.models.chat_messages import ChatMessage
from app.services import chat_service
from app.schemas.chat_schema import ChatResponse
from app.models.job_posting import JobPosting
from app.api.deps import get_current_candidate_profile
from app.models.chat_sessions import ChatSession
from app.models.candidate_profiles import CandidateProfile
from app.models.user import User
from app.db.database import get_db
from app.schemas.base_schema import ResponseSchema
from app.schemas.chat_schema import ChatRequest
from app.api.v1.endpoints.admin_dashboard import router
from app import services
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(tags=["Chatbot"])

from app.services.ai_quota_service import check_ai_quota
from app.api.deps import get_current_user

@router.post(
    "/chat", 
    response_model=ResponseSchema[ChatResponse],
    tags=["Chatbot"],
    summary="api chat với AI"
)
def candidate_chat(
    request_in: ChatRequest,
    db: Session = Depends(get_db),
    candidate_profile: CandidateProfile = Depends(get_current_candidate_profile),
    current_user: User = Depends(get_current_user)
):
    """API cho ứng viên chat với AI của công ty"""
    
    # Check quota
    check_ai_quota(db, current_user)

    # 1. Tìm thông tin Job và Company
    job = db.query(JobPosting).filter(JobPosting.id == request_in.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tuyển dụng")
        
    company_id = job.company_id
    
    # 2. Tìm hoặc tạo ChatSession
    session = db.query(ChatSession).filter(
        ChatSession.candidate_id == candidate_profile.id,
        ChatSession.job_id == request_in.job_id
    ).first()
    
    if not session:
        session = ChatSession(
            candidate_id=candidate_profile.id,
            job_id=request_in.job_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # 3. Gọi Chat Service
    try:
        bot_reply = chat_service.get_ai_response(
            db=db,
            company_id=company_id,
            message=request_in.message,
            session_id=session.id,
            user=current_user
        )
        
        return ResponseSchema(
            success=True,
            data=ChatResponse(
                id=str(int(datetime.now().timestamp() * 1000)),
                sender="ai", 
                text=bot_reply,
                timestamp=datetime.now()
            )
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Chat Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trợ lý AI đang bận: {str(e)}")

@router.get(
    "/history_chat", 
    response_model=ResponseSchema[list[ChatResponse]],
    tags=["Chatbot"], 
    summary="API lấy lịch sử chat với AI"
)
def candidate_chat_history(
    job_id: int,
    db: Session = Depends(get_db),
    candidate_profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """API cho ứng viên lấy lịch sử chat với AI của công ty"""
    
    # 1. Tìm thông tin Job và Company
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tuyển dụng")
        
    company_id = job.company_id
    
    # 2. Tìm hoặc tạo ChatSession
    session = db.query(ChatSession).filter(
        ChatSession.candidate_id == candidate_profile.id,
        ChatSession.job_id == job_id
    ).first()
    
    if not session:
        session = ChatSession(
            candidate_id=candidate_profile.id,
            job_id=job_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # 3. Lấy lịch sử chat từ Database SQL (Dùng session_id)
    db_history = db.query(ChatMessage).filter(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Định dạng lịch sử chat cho Frontend (user/ai và text)
    formatted_history = []
    for msg in db_history:
        sender = SenderEnum.user if msg.sender == SenderEnum.user else SenderEnum.ai
        formatted_history.append(ChatResponse(
            id=str(msg.id),
            sender=sender, 
            text=msg.content,
            timestamp=msg.created_at
        ))
    
    return ResponseSchema(
        success=True,
        data=formatted_history
    )