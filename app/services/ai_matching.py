# app/services/ai_matching.py
import json
import os
import google.generativeai as genai
from sqlalchemy.orm import joinedload
from app.crud import crud_application
from app.db.database import SessionLocal
from app.models.applications import Application
from app.models.candidate_profiles import CandidateProfile

class GeminiKeyManager:
    def __init__(self, filepath="secrets/gemini_keys.txt"):
        self.filepath = filepath
        self.keys = self._load_keys()
        self.current_index = 0

    def _load_keys(self):
        # Đọc các dòng, bỏ dòng trống và xóa khoảng trắng thừa
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Không tìm thấy file {self.filepath}. Hãy tạo thư mục secrets và file này.")
        with open(self.filepath, "r") as f:
            keys = [line.strip() for line in f if line.strip()]
        if not keys:
            raise ValueError(f"File {self.filepath} đang trống! Hãy điền API Key vào.")
        print(f"Đã nạp thành công {len(keys)} API Keys vào hệ thống.")
        return keys

    def get_current_key(self):
        return self.keys[self.current_index]

    def rotate_key(self):
        """Chuyển sang key tiếp theo, nếu hết thì quay lại từ đầu"""
        self.current_index = (self.current_index + 1) % len(self.keys)
        print(f"[Key Manager] Đã xoay vòng sang API Key số {self.current_index + 1}...")

# Khởi tạo đối tượng quản lý Key (Chỉ khởi tạo 1 lần khi server chạy)
key_manager = GeminiKeyManager()


def run_ai_matching(application_id: int):
    db = SessionLocal()
    try:
        app_record = db.query(Application).options(
            joinedload(Application.job_posting),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.experiences),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.educations),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.certifications)
        ).filter(Application.id == application_id).first()

        if not app_record:
            return
            
        job = app_record.job_posting
        candidate = app_record.candidate_profile

        # 2. RÚT TRÍCH VÀ ĐỊNH DẠNG DỮ LIỆU THÀNH CHUỖI TEXT CHO AI ĐỌC DỄ DÀNG
        # Chuyển list object thành các dòng text
        exp_text = "\n".join([f"- {exp.job_title} tại {exp.company_name}: {exp.description}" for exp in candidate.experiences]) or "Không có thông tin kinh nghiệm."
        edu_text = "\n".join([f"- {edu.degree} chuyên ngành {edu.major} tại {edu.institution_name}" for edu in candidate.educations]) or "Không có thông tin học vấn."
        cert_text = "\n".join([f"- {cert.name} (Cấp bởi: {cert.issuer})" for cert in candidate.certifications]) or "Không có chứng chỉ."
        tags_text = ", ".join(candidate.skill_tags) if candidate.skill_tags else "Chưa cập nhật kỹ năng"

        prompt = f"""
        Bạn là một chuyên gia Tuyển dụng Nhân sự (HR) cấp cao. Hãy phân tích mức độ phù hợp của Hồ sơ Ứng viên so với Yêu cầu Công việc.
        
        [YÊU CẦU CÔNG VIỆC]
        - Tiêu đề: {job.title}
        - Từ khóa kỹ năng: {job.tags}
        - Yêu cầu chi tiết: {job.requirements}
        
        [HỒ SƠ ỨNG VIÊN]
        - Tên ứng viên: {candidate.full_name}
        - Giới thiệu bản thân: {candidate.bio}
        - Từ khóa kỹ năng ứng viên có: {tags_text}
        
        * KINH NGHIỆM LÀM VIỆC:
        {exp_text}
        
        * HỌC VẤN:
        {edu_text}
        
        * CHỨNG CHỈ:
        {cert_text}
        
        [NHIỆM VỤ]
        Dựa trên thông tin trên, hãy chấm điểm độ khớp (0-100) và phân tích điểm mạnh, điểm yếu của ứng viên đối với CÔNG VIỆC NÀY.
        
        BẠN BẮT BUỘC TRẢ VỀ DỮ LIỆU ĐỊNH DẠNG JSON NHƯ SAU, KHÔNG CÓ BẤT KỲ VĂN BẢN NÀO KHÁC:
        {{
            "score": <số thập phân từ 0 đến 100>,
            "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
            "weaknesses": ["Điểm thiếu hụt 1", "Điểm thiếu hụt 2"],
            "explanation": "<Đoạn văn ngắn (khoảng 2-3 câu) tóm tắt lý do chấm điểm>"
        }}
        CÂU TRẢ LỜI BẮT BUỘC PHẢI VIẾT TIẾNG VIỆT.
        """

        # 4. In ra xem Prompt đã gom đủ dữ liệu chưa (Khi debug)
        print("======== PROMPT GỬI LÊN AI ========")
        print(prompt)
        print("===================================")

        # 2. VÒNG LẶP GỌI AI VÀ TỰ ĐỘNG ĐỔI KEY
        max_retries = len(key_manager.keys)
        raw_json_string = None

        for attempt in range(max_retries):
            try:
                # Lấy key hiện tại và cấu hình cho Gemini
                current_api_key = key_manager.get_current_key()
                genai.configure(api_key=current_api_key)
                
                print(f"Bắt đầu gọi Google Gemini (Thử lần {attempt + 1}/{max_retries})...")
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.2 
                    )
                )
                
                # Nếu chạy đến đây là thành công, thoát khỏi vòng lặp
                raw_json_string = response.text
                print("Gemini đã trả lời thành công!")
                break 

            except Exception as e:
                error_msg = str(e).lower()
                # Kiểm tra xem lỗi có phải do hết Quota (429) hoặc Limit không
                if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg or "limit" in error_msg:
                    print(f"Key hiện tại đã hết Quota hoặc bị Limit. Lỗi: {e}")
                    key_manager.rotate_key() # Đổi sang key tiếp theo
                else:
                    # Nếu là lỗi khác (ví dụ: mất mạng, prompt sai), quăng lỗi luôn không thử lại
                    raise e
        
        # 3. Kiểm tra xem sau N lần thử có lấy được kết quả không
        if not raw_json_string:
            raise RuntimeError("Đã thử tất cả các API Key nhưng đều thất bại (Hết sạch Quota toàn bộ hệ thống).")

        # 4. Parse JSON và Lưu DB
        score_data = json.loads(raw_json_string)
        crud_application.create_ai_matching_score(db, application_id, score_data)
        
        print(f"Đã lưu điểm AI ({score_data['score']}%) cho đơn số {application_id} vào Database!")

    except Exception as e:
        print(f"Lỗi AI Matching: {e}")
    finally:
        db.close()