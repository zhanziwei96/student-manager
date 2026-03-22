"""
用户管理 API（管理员）- JWT 版本
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import require_admin, get_current_user
from app.crud import (
    get_user, get_user_by_username, get_users, create_user,
    update_user, reset_password, delete_user
)
from app.models import UserRoleConst
from app.models.constants import (
    ApiResponseConst, MessageConst, RoutePrefixConst
)

router = APIRouter(prefix=RoutePrefixConst.ADMIN, tags=["users"])


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    name: str = Field(..., min_length=1, description="姓名")
    role: str = Field(default=UserRoleConst.TEACHER, description="角色")
    assigned_classes: List[str] = Field(default=[], description="负责班级")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    assigned_classes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, description="新密码")


@router.get("/users")
async def list_users(
    request: Request,
    role: Optional[str] = Query(None, description="角色过滤"),
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """获取用户列表"""
    users = get_users(session, role)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [u.model_dump() for u in users]
    }


@router.post("/users")
async def add_user(
    request: Request,
    data: CreateUserRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """创建用户"""
    existing = get_user_by_username(session, data.username)
    if existing:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='用户名已存在')
    
    # 生成密码哈希
    from app.core.security import generate_password_hash
    password_hash, salt = generate_password_hash(data.password)
    
    user_obj = create_user(
        session,
        username=data.username,
        name=data.name,
        password_hash=password_hash,
        salt=salt,
        role=data.role,
        assigned_classes=data.assigned_classes
    )
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.USER_CREATED,
        ApiResponseConst.DATA: user_obj.model_dump()
    }


@router.put("/users/{user_id}")
async def update_user_info(
    request: Request,
    user_id: int,
    data: UpdateUserRequest,
    session: Session = Depends(get_session),
    current_user_id: str = Depends(require_admin)
):
    """更新用户信息"""
    user_obj = get_user(session, user_id)
    if not user_obj:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
    
    if data.name:
        user_obj.name = data.name
    if data.role:
        user_obj.role = data.role
    if data.assigned_classes is not None:
        import json
        user_obj.assigned_classes = json.dumps(data.assigned_classes, ensure_ascii=False)
    if data.is_active is not None:
        user_obj.is_active = data.is_active
    
    session.add(user_obj)
    session.commit()
    session.refresh(user_obj)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.USER_UPDATED,
        ApiResponseConst.DATA: user_obj.model_dump()
    }


@router.put("/users/{user_id}/reset-password")
async def reset_user_password_api(
    request: Request,
    user_id: str,
    data: ResetPasswordRequest,
    session: Session = Depends(get_session),
    current_user_id: str = Depends(require_admin)
):
    """重置用户密码，支持 user_id(数字) 或 username(学号/账号)"""
    from app.core.security import generate_password_hash
    password_hash, salt = generate_password_hash(data.new_password)
    
    # 尝试解析为整数(user_id)，失败则按 username 查找
    try:
        uid = int(user_id)
        user_obj = get_user(session, uid)
    except ValueError:
        user_obj = get_user_by_username(session, user_id)
    
    if not user_obj:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
    
    reset_password(session, user_obj, password_hash, salt)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.PASSWORD_RESET
    }


@router.delete("/users/{user_id}")
async def remove_user(
    request: Request,
    user_id: int,
    session: Session = Depends(get_session),
    current_user_id: str = Depends(require_admin)
):
    """删除用户"""
    # 检查是否尝试删除自己
    if str(user_id) == str(current_user_id):
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='不能删除当前登录账号')
    
    success = delete_user(session, user_id)
    if not success:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.USER_DELETED
    }
