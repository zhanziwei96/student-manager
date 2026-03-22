"""
全局异常处理
统一 API 错误响应格式
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.models.constants import ApiResponseConst


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    处理 FastAPI HTTPException
    将默认的 {"detail": "..."} 转换为统一的 {"success": false, "message": "..."}
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            ApiResponseConst.SUCCESS: False,
            ApiResponseConst.MESSAGE: exc.detail
        }
    )
