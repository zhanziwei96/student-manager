"""
登录相关 API - JWT 版本
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus, get_settings
from app.core.logging import logger
from app.core.rate_limit import check_rate_limit
from app.core.jwt import (
    create_access_token, set_token_cookie, clear_token_cookie,
    get_current_user
)
from app.crud import get_user_by_username, record_login_success, record_login_failure
from app.models import UserRoleConst
from app.models.constants import (
    ApiResponseConst, MessageConst,
    ApiResponse, ApiSuccessResponse
)

router = APIRouter(tags=["login"])

settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = UserRoleConst.ADMIN


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class LoginUserData(BaseModel):
    """登录响应的用户数据结构"""
    id: str | int
    username: str
    name: str
    role: str
    class_name: Optional[str] = None
    is_admin: Optional[bool] = None


class LoginResponse(ApiResponse[LoginUserData]):
    """登录响应模型"""
    pass


class MeResponse(ApiResponse[dict]):
    """获取当前用户信息响应模型"""
    pass


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,  # 新增：用于设置 Cookie
    data: LoginRequest,
    session: Session = Depends(get_session)
):
    """用户登录 - JWT 版本"""
    username = data.username.strip()
    password = data.password.strip()

    # 限流检查（基于用户名）
    allowed = await check_rate_limit(request, username, key_prefix="login", limiter_attr="limiter")
    if not allowed:
        raise HTTPException(
            status_code=HttpStatus.TOO_MANY_REQUESTS,  # 429 请求过多
            detail='请求过于频繁，请稍后再试'
        )
    
    # 学生登录单独处理
    if data.role == UserRoleConst.STUDENT:
        from app.crud import (
            get_student, record_student_login_failure, reset_student_login_lock
        )

        student = get_student(session, username)
        if not student:
            raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')

        # 检查账号状态（与教师/管理员登录同逻辑）
        if student.locked_until and student.locked_until > datetime.now():
            logger.warning(f"登录失败，学生账号已锁定: {username}")
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='账号已被锁定，请稍后再试')

        if not student.is_account_enabled:
            logger.warning(f"登录失败，学生账号已禁用: {username}")
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='账号已被禁用')

        # 验证密码 (SEC-003: 使用新的 verify_password 接口)
        from app.core.security import verify_password
        if not verify_password(password, student.password_hash):
            is_locked = record_student_login_failure(session, student)
            if is_locked:
                logger.warning(f"学生账号因多次失败被锁定: {username}")
                raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='账号已被锁定，请稍后再试')
            remaining = settings.security.max_login_failures - student.login_fail_count
            logger.info(f"学生登录密码错误: {username}, 剩余次数: {remaining}")
            raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')

        # 登录成功：重置失败计数与锁定状态
        reset_student_login_lock(session, student)

        # 生成 JWT Token
        token_data = {
            "sub": str(student.student_id),
            "username": str(student.student_id),
            "name": student.name,
            "role": UserRoleConst.STUDENT,
            "is_admin": False,
            "class_name": student.class_name,
        }
        access_token = create_access_token(token_data)
        set_token_cookie(response, access_token)
        
        logger.info(f"学生登录成功: {student.student_id}")
        
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.MESSAGE: MessageConst.LOGIN_SUCCESS,
            ApiResponseConst.DATA: {
                'id': str(student.student_id),
                'username': str(student.student_id),
                'name': student.name,
                'role': UserRoleConst.STUDENT,
                'class_name': student.class_name
            }
        }
    
    # 管理员/教师登录
    user = get_user_by_username(session, username)
    if not user:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')
    
    # 检查账号状态
    if user.locked_until and user.locked_until > datetime.now():
        logger.warning(f"登录失败，账号已锁定: {username}")
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='账号已被锁定，请稍后再试')
    
    if not user.is_account_enabled:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='账号已被禁用')
    
    # 验证密码 (SEC-003: 使用新的 verify_password 接口)
    from app.core.security import verify_password
    if not verify_password(password, user.password_hash):
        is_locked = record_login_failure(session, user)
        if is_locked:
            logger.warning(f"账号因多次失败被锁定: {username}")
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='账号已被锁定，请稍后再试')
        remaining = settings.security.max_login_failures - user.login_fail_count
        logger.info(f"登录密码错误: {username}, 剩余次数: {remaining}")
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, 
                          detail=f'密码错误（还剩 {remaining} 次机会）')
    
    # 验证角色
    if user.role != data.role:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')
    
    # 登录成功
    client_host = request.client.host if request.client else "unknown"
    record_login_success(session, user, client_host)
    logger.info(f"用户登录成功: {username}, 角色: {user.role}")
    
    # 生成 JWT Token
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "name": user.name,
        "role": user.role,
        "is_admin": user.is_admin(),
    }
    access_token = create_access_token(token_data)
    set_token_cookie(response, access_token)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.LOGIN_SUCCESS,
        ApiResponseConst.DATA: {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'role': user.role,
            'is_admin': user.is_admin()
        }
    }


@router.post("/logout", response_model=ApiSuccessResponse)
def logout(response: Response):
    """用户登出 - 清除 Cookie"""
    clear_token_cookie(response)
    logger.info("用户登出")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.LOGOUT_SUCCESS
    }


@router.post("/change-password", response_model=ApiSuccessResponse)
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)  # 使用 JWT 获取用户
):
    """修改密码"""
    user_id = user.get("sub")
    role = user.get("role")
    
    if not user_id:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='请先登录')
    
    if role == UserRoleConst.STUDENT:
        from app.crud import get_student
        user_obj = get_student(session, str(user_id))
    else:
        from app.crud import get_user
        user_obj = get_user(session, int(user_id))
    
    if not user_obj:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
    
    # 验证旧密码 (SEC-003: 使用新的 verify_password 接口)
    from app.core.security import verify_password
    if not verify_password(data.old_password, user_obj.password_hash):
        logger.info(f"修改密码失败，旧密码错误: {user_id}")
        return {
            ApiResponseConst.SUCCESS: False,
            ApiResponseConst.MESSAGE: MessageConst.OLD_PASSWORD_WRONG
        }
    
    # 设置新密码 - 使用CRUD层函数（架构分层修复）
    from app.crud import update_user_password
    update_user_password(session, user_obj, data.new_password)
    
    logger.info(f"密码修改成功: {user_id}")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.PASSWORD_CHANGED
    }


@router.get("/me", response_model=MeResponse)
async def get_me(user: dict = Depends(get_current_user)):
    """获取当前用户信息 - 从 JWT 解析"""
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: user
    }
