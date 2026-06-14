import json
from app.services.ai_matching import _gemini_json_response

def generate_job_posting_with_ai(prompt: str, db=None) -> dict:
    """Gọi Gemini AI để sinh ra nội dung Job Posting dựa trên prompt ngắn gọn."""
    system_prompt = f"""
    Bạn là một chuyên gia Tuyển dụng Nhân sự (HR).
    Nhiệm vụ của bạn là dựa vào một vài yêu cầu tuyển dụng ngắn gọn của HR để viết ra một tin tuyển dụng hoàn chỉnh, chuyên nghiệp.
    Kết quả trả về phải là một chuỗi JSON hợp lệ, tuân thủ chặt chẽ cấu trúc sau, KHÔNG thêm bất kỳ văn bản nào khác ngoài JSON.
    
    LƯU Ý QUAN TRỌNG:
    - KHÔNG sử dụng bất kỳ thẻ HTML nào (như <ul>, <li>, <p>, <br>...) trong nội dung.
    - Để tạo danh sách, hãy sử dụng dấu gạch ngang (-) hoặc hoa thị (*).
    - Để ngắt dòng, hãy sử dụng ký tự newline (\\n).

    {{
      "title": "Tên chức danh công việc",
      "description": "Mô tả công việc chi tiết, chuyên nghiệp, hấp dẫn. Dùng \\n để xuống dòng, KHÔNG dùng thẻ HTML.",
      "requirements": "Yêu cầu chi tiết. Dùng \\n để xuống dòng, dấu '-' cho các mục. KHÔNG dùng thẻ HTML.",
      "location": "Địa chỉ làm việc cụ thể nếu có, hoặc để trống",
      "tags": ["Từ khóa 1", "Từ khóa 2", "Từ khóa 3"],
      "salary_min": <Số nguyên, mức lương tối thiểu (nếu có đề cập), hoặc null>,
      "salary_max": <Số nguyên, mức lương tối đa (nếu có đề cập), hoặc null>,
      "years_of_experience": <Số nguyên, số năm kinh nghiệm yêu cầu, hoặc null>,
      "job_type": "full_time" hoặc "part_time" hoặc "remote"
    }}

    Yêu cầu đầu vào của HR:
    "{prompt}"
    """
    
    # Gọi hàm _gemini_json_response đã có sẵn với service_type="job_generation"
    generated_json = _gemini_json_response(
        prompt=system_prompt,
        model_name="gemini-2.5-flash",
        db=db,
        service_type="job_generation"
    )
    
    return generated_json
