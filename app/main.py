import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api.v1.router import api_router
from app.core.exceptions import global_exception_handler
from app.core.logger import logger
import app.db.base_import_class

load_dotenv()

openapi_tags = [
    {
        "name": "Auth",
        "description": "Đăng ký , đăng nhập và xác thực người dùng",
    },
    {
        "name": "Public Jobs",
        "description": "Các aPI công khai để tra cứu và hiển thị danh sách việc làm",
    },
    {
        "name": "Candidate Profile",
        "description": "Quản lý hồ sơ cá nhân, CV, học vấn, kinh nghiệm và chứng chỉ của ứng viên",
    },
    {
        "name": "Candidate Jobs",
        "description": "Các thao tác của ứng viên với job như lưu job, ứng tuyển và xem lịch sử apply.",
    },
    {
        "name": "HR Companies",
        "description": "Các API để HR đăng ký và quản lý công ty của mình.",
    },
    {
        "name": "HR Jobs",
        "description": "Các API để HR tạo job, sửa draft và chuyển trạng thái job.",
    },
    {
        "name": "HR Applications",
        "description": "Cac API de HR xem danh sách ung viên, xem CV và xử lý đơn ứng tuyển.",
    },
    {
        "name": "Upload",
        "description": "Upload file dung cho CV, tài liệu và các tài nguyên liên quan.",
    },
    {
        "name": "Admin Companies",
        "description": "Các API để admin duyệt, từ chối, khóa hoặc mở khóa công ty.",
    },
    {
        "name": "Interview schedule",
        "description": "Các API về lịch phỏng vấn.",
    },
    {
        "name": "Notifications",
        "description": "Thông báo in-app cho ứng viên và HR.",
    },
    {
        "name":"Chatbot",
        "description":"API cho chat với AI"
    }
]

app = FastAPI(
    title="Hệ thống quản lý tuyển dụng",
    description="API cho hệ thống quản lý tuyển dụng",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)

app.include_router(api_router, prefix="/api/v1")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", tags=["Auth"], summary="Kiểm tra API hoạt động")
def read_root():
    logger.info("Truy cập thành công")
    return {
        "success": True,
        "data": "Chào mừng bạn đến với API quản lý tuyển dụng!",
        "error": None,
        "meta": None,
    }
