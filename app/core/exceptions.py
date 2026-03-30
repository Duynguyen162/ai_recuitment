from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Lỗi hệ thống tại {request.url.path}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": "Lỗi máy chủ nội bộ. Vui lòng thử lại sau.",
            "meta": None
        }
    )