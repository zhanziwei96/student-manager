"""
API 依赖注入
"""
from typing import Generator, Optional
from fastapi import Request, HTTPException, Depends
from sqlmodel import Session
from app.core.db import get_session
from app.crud import get_user_by_username
from app.core.config import HttpStatus
from app.models.constants import SessionKeyConst


# 数据库会话依赖
SessionDep = Depends(get_session)


def get_current_user(request: Request):
    """获取当前登录用户（用于依赖注入）"""
    user_id = request.session.get(SessionKeyConst.USER_ID)
    if not user_id:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='请先登录')
    return user_id


def require_login(request: Request) -> int:
    """要求登录"""
    user_id = request.session.get(SessionKeyConst.USER_ID)
    if not user_id:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='请先登录')
    return user_id


def require_admin(request: Request) -> int:
    """要求管理员权限"""
    user_id = request.session.get(SessionKeyConst.USER_ID)
    if not user_id:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='请先登录')
    if not request.session.get(SessionKeyConst.IS_ADMIN):
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='需要管理员权限')
    return user_id


def is_admin(request: Request) -> bool:
    """检查是否为管理员"""
    return request.session.get(SessionKeyConst.IS_ADMIN, False)


def get_session_user_id(request: Request) -> Optional[int]:
    """获取会话中的用户ID"""
    return request.session.get(SessionKeyConst.USER_ID)
