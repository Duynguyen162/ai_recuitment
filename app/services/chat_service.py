import google.generativeai as genai
from langchain_chroma import Chroma
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import time
from pathlib import Path
from app.core.config import settings
from sqlalchemy.orm import Session
from app.models.ai_logs import AiLog
from app.models.chat_messages import ChatMessage
from app.core.enum import SenderEnum

# Cấu hình đường dẫn và tên collection (đồng bộ với rag_service.py)
VECTOR_DB_DIR = str(Path("chroma_db").resolve())
COLLECTION_NAME = "company_policies"

def get_ai_response(db: Session, company_id: int, message: str, session_id: int):
    # 0. Lưu tin nhắn của người dùng vào DB
    user_msg = ChatMessage(
        session_id=session_id,
        sender=SenderEnum.user,
        content=message
    )
    db.add(user_msg)
    db.commit()

    try:
        start_time = time.perf_counter()
        
        # 1. Khởi tạo Embeddings và Vector Store
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", 
            google_api_key=settings.GOOGLE_API_KEY,
        )
        vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=VECTOR_DB_DIR,
            client_settings=ChromaSettings(anonymized_telemetry=False),
        )

        # 2. Truy vấn dữ liệu liên quan (chỉ lọc theo company_id)
        docs = vector_store.similarity_search(
            message, 
            k=3, 
            filter={"company_id": company_id}
        )
        context = "\n\n".join([doc.page_content for doc in docs])

        # 3. Lấy lịch sử chat từ Database SQL (Dùng session_id)
        db_history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Định dạng lịch sử chat cho Gemini SDK (loại bỏ tin nhắn cuối cùng vừa thêm vì nó là 'input')
        formatted_history = []
        for msg in db_history[:-1]:
            role = "user" if msg.sender == SenderEnum.user else "model"
            formatted_history.append({"role": role, "parts": [msg.content]})

        # 4. Cấu hình Gemini SDK
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        system_instruction = f"""Bạn là trợ lý tuyển dụng ảo thông minh của công ty. 
Nhiệm vụ của bạn là giải đáp thắc mắc của ứng viên dựa trên tài liệu nội bộ được cung cấp.

TÀI LIỆU NỘI BỘ:
{context}

QUY TẮC BẮT BUỘC:
1. Chỉ trả lời dựa trên TÀI LIỆU NỘI BỘ ở trên. 
2. Nếu tài liệu không chứa câu trả lời, hãy nói: "Rất tiếc, tôi chưa được bộ phận Nhân sự cung cấp thông tin về vấn đề này. Bạn có thể liên hệ trực tiếp với HR để biết thêm chi tiết."
3. Tuyệt đối không tự bịa đặt thông tin (hallucination).
4. FORMAT CÂU TRẢ LỜI:
- Trả lời NGẮN GỌN, dễ đọc.
- Sử dụng bullet points (• hoặc -)
- Mỗi ý tối đa 1 dòng
- Không viết đoạn văn dài
5. CẤU TRÚC:
- Nếu có nhiều nhóm → chia thành các mục rõ ràng
- In đậm tiêu đề từng nhóm
6. Giữ tone thân thiện, chuyên nghiệp.
"""
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )

        # 5. Gọi AI
        chat_session = model.start_chat(history=formatted_history)
        response = chat_session.send_message(message)
        
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)
        usage = getattr(response, "usage_metadata", None)
        tokens = usage.total_token_count if usage else 0
        ai_reply = response.text
        
        # Log success
        ai_log = AiLog(
            service_type="chatbot",
            tokens_used=tokens,
            processing_time_ms=processing_time_ms,
            is_error=False
        )
        db.add(ai_log)

    except Exception as e:
        print(f"Lỗi AI Service: {str(e)}")
        ai_reply = "Xin lỗi, hệ thống AI đang gặp sự cố. Vui lòng thử lại sau."
        
        if 'start_time' in locals():
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            ai_log = AiLog(
                service_type="chatbot",
                processing_time_ms=processing_time_ms,
                is_error=True,
                error_message=str(e)[:1000]
            )
            db.add(ai_log)

    # 6. Lưu câu trả lời của AI vào DB
    ai_msg = ChatMessage(
        session_id=session_id,
        sender=SenderEnum.ai,
        content=ai_reply
    )
    db.add(ai_msg)
    db.commit()

    return ai_reply
