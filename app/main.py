from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.exceptions import global_exception_handler
from app.core.logger import logger
import app.db.base_import_class
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Hệ thống quản lý tuyển dụng",
    description="API cho hệ thống quản lý tuyển dụng, bao gồm quản lý người dùng, đăng tin tuyển dụng, bóc tách CV, và matching ứng viên.",
    version="1.0.0"
)
origins = [
    "http://localhost:3000",
]
#thiết lập CORS để cho phép frontend truy cập API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Ở môi trường dev thì để "*", lên production sẽ điền domain thật
    allow_credentials=True,
    allow_methods=["*"],# Cho phép mọi method (GET, POST, PUT, DELETE)
    allow_headers=["*"],# Cho phép mọi header
)
# Hàm xử lí lỗi toàn cục
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def read_root():
    logger.info("Truy cập thành công")
    return {
        "success": True,
        "data": "Chào mừng bạn đến với API quản lý tuyển dụng!",
        "error": None,
        "meta": None
    }