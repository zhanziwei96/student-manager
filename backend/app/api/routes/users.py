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
    update_user, update_user_info as crud_update_user_info, reset_password, delete_user
)
from app.models import UserRoleConst
from app.models.constants import (
    ApiResponseConst, MessageConst, RoutePrefixConst,
    ApiResponse, ApiSuccessResponse, ApiListResponse
)

router = APIRouter(tags=["users"])


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    name: str = Field(..., min_length=1, description="姓名")
    role: str = Field(default=UserRoleConst.TEACHER, description="角色")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_account_enabled: Optional[bool] = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, description="新密码")


# 响应模型定义
class UserData(BaseModel):
    """用户数据结构"""
    id: int
    username: str
    name: str
    role: str
    is_account_enabled: bool
    created_at: Optional[str] = None


class UserListResponse(ApiListResponse[UserData]):
    """用户列表响应"""
    pass


class UserDetailResponse(ApiResponse[UserData]):
    """用户详情响应"""
    pass


@router.get("/users", response_model=UserListResponse)
async def list_users(
    request: Request,
    role: Optional[str] = Query(None, description="角色过滤"),
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """获取用户列表"""
    users = get_users(session, role)
    result = []
    for u in users:
        user_data = u.model_dump()
        # 将 datetime 转换为字符串
        if user_data.get('created_at') and hasattr(user_data['created_at'], 'isoformat'):
            user_data['created_at'] = user_data['created_at'].isoformat()
        if user_data.get('last_login') and hasattr(user_data['last_login'], 'isoformat'):
            user_data['last_login'] = user_data['last_login'].isoformat()
        result.append(user_data)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: result
    }


@router.post("/users", response_model=UserDetailResponse)
async def add_user(
    request: Request,
    data: CreateUserRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """创建用户 - SEC-003: 使用简化密码哈希接口"""
    existing = get_user_by_username(session, data.username)
    if existing:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='用户名已存在')
    
    # 生成密码哈希（bcrypt 自动处理盐值）
    from app.core.security import hash_password
    password_hash = hash_password(data.password)
    
    user_obj = create_user(
        session,
        username=data.username,
        name=data.name,
        password_hash=password_hash,
        role=data.role,
    )

    user_data = user_obj.model_dump()
    # 将 datetime 转换为字符串
    if user_data.get('created_at') and hasattr(user_data['created_at'], 'isoformat'):
        user_data['created_at'] = user_data['created_at'].isoformat()
    if user_data.get('last_login') and hasattr(user_data['last_login'], 'isoformat'):
        user_data['last_login'] = user_data['last_login'].isoformat()
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.USER_CREATED,
        ApiResponseConst.DATA: user_data
    }


@router.put("/users/{user_id}", response_model=UserDetailResponse)
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
    
    # 调用CRUD层函数，业务逻辑封装在CRUD层（架构分层修复）
    updated_user = crud_update_user_info(
        session=session,
        user=user_obj,
        name=data.name,
        role=data.role,
        is_account_enabled=data.is_account_enabled
    )

    user_data = updated_user.model_dump()
    # 将 datetime 转换为字符串 - 使用 mode='json' 确保正确序列化
    from datetime import datetime
    for field in ['created_at', 'last_login', 'locked_until']:
        value = user_data.get(field)
        if isinstance(value, datetime):
            user_data[field] = value.isoformat()
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.USER_UPDATED,
        ApiResponseConst.DATA: user_data
    }


@router.put("/users/{user_id}/reset-password", response_model=ApiSuccessResponse)
async def reset_user_password_api(
    request: Request,
    user_id: str,
    data: ResetPasswordRequest,
    session: Session = Depends(get_session),
    current_user_id: str = Depends(require_admin)
):
    """重置用户密码，支持 user_id(数字) 或 username(学号/账号) - SEC-003: 使用简化密码哈希接口"""
    from app.core.security import hash_password
    password_hash = hash_password(data.new_password)
    
    # 尝试解析为整数(user_id)，失败则按 username 查找
    try:
        uid = int(user_id)
        user_obj = get_user(session, uid)
    except ValueError:
        user_obj = get_user_by_username(session, user_id)
    
    if not user_obj:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
    
    reset_password(session, user_obj, password_hash)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.PASSWORD_RESET
    }


@router.delete("/users/{user_id}", response_model=ApiSuccessResponse)
async def remove_user(
    request: Request,
    user_id: int,
    session: Session = Depends(get_session),
    current_user_id: str = Depends(require_admin)
):
    """删除用户"""
    # 检查是否尝试删除自己（统一使用 int 比较避免类型不一致问题）
    try:
        if user_id == int(current_user_id):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='不能删除当前登录账号')
    except (ValueError, TypeError):
        # 如果 current_user_id 无法转换为 int，记录错误但继续执行（保守策略）
        from app.core.logging import logger
        logger.warning(f"无法将 current_user_id 转换为 int: {current_user_id}")
    
    success = delete_user(session, user_id)
    if not success:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.USER_DELETED
    }
