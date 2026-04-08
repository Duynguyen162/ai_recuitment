import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.base_schema import ResponseSchema

router = APIRouter()

UPLOAD_ROOT = "uploads"

@router.post("/file", response_model=ResponseSchema[str])
async def upload_general_file(
    folder: str, # Ví dụ: 'logos', 'licenses', 'avatars'
    file: UploadFile = File(...)
):
    # 1. Tạo thư mục đích
    target_dir = os.path.join(UPLOAD_ROOT, folder)
    os.makedirs(target_dir, exist_ok=True)
    
    # 2. Đổi tên file để tránh trùng lặp bằng UUID
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(target_dir, unique_filename)
    
    # 3. Lưu file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Không thể lưu file")

    # Trả về đường dẫn để Frontend dùng cho API tiếp theo
    return ResponseSchema(success=True, data=file_path)