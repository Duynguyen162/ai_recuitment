import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

print(type(asyncio.get_event_loop()))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.exceptions import global_exception_handler
from app.core.logger import logger
import app.db.base_import_class
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Hệ thống quản lý tuyển dụng",
    description="API cho hệ thống quản lý tuyển dụng",
    version="1.0.0"
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
 
# Then include routers
app.include_router(api_router, prefix="/api/v1")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
 
@app.get("/")
def read_root():
    logger.info("Truy cập thành công")
    return {
        "success": True,
        "data": "Chào mừng bạn đến với API quản lý tuyển dụng!",
        "error": None,
        "meta": None
    }