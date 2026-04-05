"""
API 依赖注入 - JWT 版本
"""
from typing import Optional
from fastapi import Request
from app.core.db import get_session
from app.core.jwt import (
    get_current_user as jwt_get_current_user,
    require_login as jwt_require_login,
    require_admin as jwt_require_admin,
)
from fastapi import HTTPException
from app.core.config import HttpStatus

# 数据库会话依赖
SessionDep = get_session


# JWT 依赖导出
get_current_user = jwt_get_current_user
require_login = jwt_require_login
require_admin = jwt_require_admin


def is_admin(request: Request) -> bool:
    """检查是否为管理员"""
    from fastapi import HTTPException
    try:
        user = jwt_get_current_user(request)
        return user.get("is_admin", False)
    except HTTPException:
        return False


def get_session_user_id(request: Request) -> Optional[str]:
    """获取会话中的用户ID"""
    try:
        user = jwt_get_current_user(request)
        return user.get("sub")
    except HTTPException:
        return None


async def require_admin_or_teacher(request: Request):
    """要求管理员或教师权限"""
    user = await jwt_get_current_user(request)
    role = user.get("role", "")
    if role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=HttpStatus.FORBIDDEN,
            detail="需要管理员或教师权限"
        )
    return user
