"""
全局异常处理 - 统一 API 错误响应格式
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

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


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    处理 FastAPI 请求体验证错误（RequestValidationError）
    将详细的验证错误转换为统一格式
    """
    # 提取错误信息
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = " -> ".join(str(x) for x in first_error["loc"])
        msg = first_error["msg"]
        message = f"{field}: {msg}"
    else:
        message = "请求参数验证失败"
    
    # 构建详细的错误信息列表
    error_details = []
    for error in errors:
        field = " -> ".join(str(x) for x in error["loc"])
        error_details.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=422,
        content={
            ApiResponseConst.SUCCESS: False,
            ApiResponseConst.MESSAGE: message,
            "errors": error_details  # 额外提供详细错误列表
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    处理所有未捕获的异常
    生产环境只返回通用错误，不暴露内部信息
    """
    # 检查是否是生产环境
    from app.core.config import get_settings
    settings = get_settings()
    
    if settings.is_development:
        message = f"服务器内部错误: {str(exc)}"
    else:
        message = "服务器内部错误，请稍后重试"
    
    return JSONResponse(
        status_code=500,
        content={
            ApiResponseConst.SUCCESS: False,
            ApiResponseConst.MESSAGE: message
        }
    )
