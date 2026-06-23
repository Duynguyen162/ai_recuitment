import os
import uuid
import shutil
from enum import Enum
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.base_schema import ResponseSchema
from app.core.config import settings

router = APIRouter(tags=["Upload"])

UPLOAD_ROOT = "uploads"

class UploadFolderEnum(str, Enum):
    logos = "logos"
    licenses = "licenses"
    avatars = "avatars"
    documents = "documents"

# BASE_URL = "http://localhost:8000"  

@router.post("/file", response_model=ResponseSchema[str])
async def upload_general_file(
    folder: UploadFolderEnum,
    file: UploadFile = File(...)
):
    folder_name = folder.value
    # Tạo thư mục đích
    target_dir = os.path.join(UPLOAD_ROOT, folder_name)
    os.makedirs(target_dir, exist_ok=True)
    
    # Đổi tên file để tránh trùng lặp bằng UUID
    ext = os.path.splitext(file.filename)[1].lower()
    forbidden_extensions = [".exe", ".sh", ".bat", ".php", ".js"]
    if ext in forbidden_extensions:
         raise HTTPException(status_code=400, detail="Định dạng file không được phép")
    
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(target_dir, unique_filename)
    file_url = f"{settings.BASE_URL}/{file_path.replace(os.sep, '/')}"
    
    # Lưu file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Không thể lưu file")

    # Trả về đường dẫn để Frontend dùng cho API tiếp theo
    return ResponseSchema(success=True, data=file_url)
