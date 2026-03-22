"""
登录相关 API
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus, get_settings
from app.core.logging import logger
from app.crud import get_user_by_username, record_login_success, record_login_failure
from app.models import User, UserRoleConst
from app.models.constants import (
    SessionKeyConst, ApiResponseConst, MessageConst, RoutePrefixConst
)

router = APIRouter(prefix=RoutePrefixConst.API, tags=["login"])

settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str = UserRoleConst.ADMIN


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


async def check_rate_limit(request: Request, identifier: str) -> bool:
    """
    检查限流
    
    Args:
        request: FastAPI请求对象
        identifier: 限流标识（如用户名或IP）
    
    Returns:
        True: 允许请求
        False: 触发限流
    """
    if not settings.rate_limit.enabled:
        return True
    
    try:
        limiter = getattr(request.app.state, 'limiter', None)
        if limiter:
            # 使用 pyrate_limiter 检查限流（非阻塞模式）
            key = f"login:{identifier}"
            success = await limiter.try_acquire_async(key, blocking=False)
            return success
    except Exception as e:
        logger.warning(f"限流检查失败: {e}")
    
    return True


@router.post("/login")
async def login(
    request: Request,
    data: LoginRequest,
    session: Session = Depends(get_session)
):
    """用户登录"""
    username = data.username.strip()
    password = data.password.strip()
    
    # 限流检查（基于用户名）
    allowed = await check_rate_limit(request, username)
    if not allowed:
        raise HTTPException(
            status_code=HttpStatus.SERVICE_UNAVAILABLE,
            detail='请求过于频繁，请稍后再试'
        )
    
    # 学生登录单独处理
    if data.role == UserRoleConst.STUDENT:
        from app.crud import get_student
        from app.models import Student
        
        student = get_student(session, username)
        if not student:
            raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')
        
        # 验证密码
        from app.core.security import verify_password_hash
        if not verify_password_hash(password, student.password_hash, student.salt):
            raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')
        
        request.session.clear()
        request.session[SessionKeyConst.USER_ID] = student.student_id
        request.session[SessionKeyConst.USERNAME] = str(student.student_id)
        request.session[SessionKeyConst.ROLE] = UserRoleConst.STUDENT
        request.session[SessionKeyConst.IS_ADMIN] = False
        
        logger.info(f"学生登录成功: {student.student_id}")
        
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.MESSAGE: MessageConst.LOGIN_SUCCESS,
            ApiResponseConst.DATA: {
                'id': str(student.student_id),
                SessionKeyConst.USERNAME: str(student.student_id),
                'name': student.name,
                SessionKeyConst.ROLE: UserRoleConst.STUDENT,
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
    
    if not user.is_active:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='账号已被禁用')
    
    # 验证密码
    from app.core.security import verify_password_hash
    if not verify_password_hash(password, user.password_hash, user.salt):
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
    record_login_success(session, user, request.client.host)
    logger.info(f"用户登录成功: {username}, 角色: {user.role}")
    
    request.session.clear()
    request.session[SessionKeyConst.USER_ID] = user.id
    request.session[SessionKeyConst.USERNAME] = user.username
    request.session[SessionKeyConst.ROLE] = user.role
    request.session[SessionKeyConst.IS_ADMIN] = user.is_admin()
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.LOGIN_SUCCESS,
        ApiResponseConst.DATA: {
            'id': user.id,
            SessionKeyConst.USERNAME: user.username,
            'name': user.name,
            SessionKeyConst.ROLE: user.role,
            SessionKeyConst.IS_ADMIN: user.is_admin()
        }
    }


@router.post("/logout")
def logout(request: Request):
    """用户登出"""
    user_id = request.session.get(SessionKeyConst.USER_ID)
    request.session.clear()
    logger.info(f"用户登出: {user_id}")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.LOGOUT_SUCCESS
    }


@router.post("/change-password")
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    session: Session = Depends(get_session)
):
    """修改密码"""
    user_id = request.session.get(SessionKeyConst.USER_ID)
    if not user_id:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='请先登录')
    
    role = request.session.get(SessionKeyConst.ROLE)
    
    if role == UserRoleConst.STUDENT:
        from app.crud import get_student
        user = get_student(session, str(user_id))
    else:
        from app.crud import get_user
        user = get_user(session, user_id)
    
    if not user:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
    
    # 验证旧密码
    from app.core.security import verify_password_hash
    if not verify_password_hash(data.old_password, user.password_hash, user.salt):
        logger.info(f"修改密码失败，旧密码错误: {user_id}")
        return {
            ApiResponseConst.SUCCESS: False,
            ApiResponseConst.MESSAGE: MessageConst.OLD_PASSWORD_WRONG
        }
    
    # 设置新密码
    from app.core.security import generate_password_hash
    user.password_hash, user.salt = generate_password_hash(data.new_password)
    session.add(user)
    session.commit()
    
    logger.info(f"密码修改成功: {user_id}")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.PASSWORD_CHANGED
    }


@router.get("/me")
def get_current_user(request: Request, session: Session = Depends(get_session)):
    """获取当前用户信息"""
    user_id = request.session.get(SessionKeyConst.USER_ID)
    role = request.session.get(SessionKeyConst.ROLE)
    
    if not user_id:
        raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='请先登录')
    
    if role == UserRoleConst.STUDENT:
        from app.crud import get_student, get_students, get_students_by_class
        student = get_student(session, str(user_id))
        if student:
            # 计算排名
            all_students = get_students(session)
            class_students = get_students_by_class(session, student.class_name)
            
            # 按分数降序排序
            all_sorted = sorted(all_students, key=lambda s: s.score, reverse=True)
            class_sorted = sorted(class_students, key=lambda s: s.score, reverse=True)
            
            # 计算排名（从1开始）
            school_rank = next((i for i, s in enumerate(all_sorted, 1) if s.student_id == student.student_id), len(all_sorted))
            class_rank = next((i for i, s in enumerate(class_sorted, 1) if s.student_id == student.student_id), len(class_sorted))
            
            return {
                ApiResponseConst.SUCCESS: True,
                ApiResponseConst.DATA: {
                    'id': str(student.student_id),
                    SessionKeyConst.USERNAME: str(student.student_id),
                    'name': student.name,
                    SessionKeyConst.ROLE: UserRoleConst.STUDENT,
                    SessionKeyConst.IS_ADMIN: False,
                    'assigned_classes': [student.class_name],
                    'score': student.score,
                    'school_rank': school_rank,
                    'class_rank': class_rank,
                    'total_students': len(all_sorted),
                    'class_total': len(class_sorted)
                }
            }
    else:
        from app.crud import get_user
        user = get_user(session, user_id)
        if user:
            return {
                ApiResponseConst.SUCCESS: True,
                ApiResponseConst.DATA: {
                    'id': user.id,
                    SessionKeyConst.USERNAME: user.username,
                    'name': user.name,
                    SessionKeyConst.ROLE: user.role,
                    SessionKeyConst.IS_ADMIN: user.is_admin(),
                    'assigned_classes': user.assigned_classes
                }
            }
    
    raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
