"""
用户API控制器 - FastAPI版本
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_user_repository import SQLiteUserRepository
from infrastructure.security.rate_limiter import login_limit
from infrastructure.security.session import require_login, require_admin, get_session_user_id, is_admin
from infrastructure.logging import logger
from infrastructure.config import AuthConfig, HttpStatus
from application.services.user_app_service import UserAppService
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO


router = APIRouter(prefix="/api", tags=["users"])


# ============ Pydantic模型 ============

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH)
    password: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH)


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=AuthConfig.USERNAME_MIN_LENGTH)
    password: str = Field(..., min_length=AuthConfig.PASSWORD_MIN_LENGTH)
    name: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH)
    role: str = Field(default="teacher")
    assigned_classes: List[str] = Field(default_factory=list)


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    assigned_classes: Optional[List[str]] = None
    status: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=AuthConfig.PASSWORD_MIN_LENGTH)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH)
    new_password: str = Field(..., min_length=AuthConfig.PASSWORD_MIN_LENGTH)


# ============ 依赖注入 ============

def get_user_service():
    """获取用户应用服务"""
    db = Database()
    repo = SQLiteUserRepository(db)
    return UserAppService(repo)


# ============ API端点 ============

@router.get("/admin/users", response_model=dict)
async def get_users(
    request: Request,
    service: UserAppService = Depends(get_user_service)
):
    """获取所有用户（管理员）"""
    require_admin(request)
    
    users = service.get_all_users()
    return {
        'success': True,
        'data': [u.__dict__ for u in users]
    }


@router.post("/admin/users", response_model=dict)
async def create_user(
    request: Request,
    data: CreateUserRequest,
    service: UserAppService = Depends(get_user_service)
):
    """创建用户（管理员）"""
    require_admin(request)
    
    try:
        dto = CreateUserDTO(
            username=data.username.strip(),
            password=data.password.strip(),
            name=data.name.strip(),
            role=data.role,
            assigned_classes=data.assigned_classes
        )
        user = service.create_user(dto)
        
        return {
            'success': True,
            'message': '用户创建成功',
            'data': user.__dict__
        }
    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail=str(e))


@router.put("/admin/users/{user_id}", response_model=dict)
async def update_user(
    request: Request,
    user_id: int,
    data: UpdateUserRequest,
    service: UserAppService = Depends(get_user_service)
):
    """更新用户（管理员）"""
    require_admin(request)
    
    try:
        dto = UpdateUserDTO(
            name=data.name,
            role=data.role,
            assigned_classes=data.assigned_classes,
            status=data.status
        )
        user = service.update_user(user_id, dto)
        
        return {
            'success': True,
            'message': '用户更新成功',
            'data': user.__dict__
        }
    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail=str(e))


@router.delete("/admin/users/{user_id}", response_model=dict)
async def delete_user(
    request: Request,
    user_id: int,
    service: UserAppService = Depends(get_user_service)
):
    """删除用户（管理员）"""
    require_admin(request)
    
    # 不能删除自己
    if user_id == request.session.get('user_id'):
        raise HTTPException(status_code=400, detail='不能删除当前登录账号')
    
    service.delete_user(user_id)
    return {'success': True, 'message': '用户删除成功'}


@router.post("/admin/users/{user_id}/reset-password", response_model=dict)
async def reset_password(
    request: Request,
    user_id: int,
    data: ResetPasswordRequest,
    service: UserAppService = Depends(get_user_service)
):
    """重置密码（管理员）"""
    require_admin(request)
    
    try:
        service.reset_password(user_id, data.new_password.strip())
        return {'success': True, 'message': '密码重置成功'}
    except Exception as e:
        logger.error(f"密码重置失败: {e}", exc_info=True)
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.post("/admin/users/{user_id}/unlock", response_model=dict)
async def unlock_user(
    request: Request,
    user_id: int,
    service: UserAppService = Depends(get_user_service)
):
    """解锁用户（管理员）"""
    require_admin(request)
    
    try:
        service.unlock_user(user_id)
        return {'success': True, 'message': '账号已解锁'}
    except Exception as e:
        logger.error(f"解锁用户失败: {e}", exc_info=True)
        raise HTTPException(status_code=HttpStatus.INTERNAL_ERROR, detail=str(e))


@router.post(
    "/login", 
    response_model=dict,
    dependencies=[Depends(login_limit())]
)
async def login(
    request: Request,
    data: LoginRequest,
    service: UserAppService = Depends(get_user_service)
):
    """用户登录（限流: 5次/分钟）"""
    try:
        user = service.authenticate_user(
            data.username.strip(),
            data.password.strip(),
            request.client.host
        )
        
        if user:
            # 防止会话固定攻击：清除旧session，创建新session
            old_session_data = dict(request.session)
            request.session.clear()
            
            # 写入新session数据（Starlette会自动生成新的session ID）
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['is_admin'] = user.is_admin()
            
            return {
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role.value,
                    'is_admin': user.is_admin()
                }
            }
        else:
            raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')
            
    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail=str(e))


@router.post("/logout", response_model=dict)
async def logout(request: Request):
    """用户登出"""
    request.session.clear()
    return {'success': True, 'message': '登出成功'}


@router.post("/change-password", response_model=dict)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    service: UserAppService = Depends(get_user_service)
):
    """修改密码"""
    user_id = require_login(request)
    
    success = service.change_password(
        user_id,
        data.old_password.strip(),
        data.new_password.strip()
    )
    
    if success:
        return {'success': True, 'message': '密码修改成功'}
    else:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='旧密码错误')


@router.get("/me", response_model=dict)
async def get_current_user(
    request: Request,
    service: UserAppService = Depends(get_user_service)
):
    """获取当前登录用户信息"""
    user_id = require_login(request)
    
    user = service.get_user_by_id(user_id)
    if user:
        return {
            'success': True,
            'data': {
                'id': user.id,
                'username': user.username,
                'name': user.name,
                'role': user.role,
                'is_admin': user.is_admin
            }
        }
    raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
