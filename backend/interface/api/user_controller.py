"""
用户API控制器 - FastAPI版本
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_user_repository import SQLiteUserRepository
from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
from infrastructure.security.rate_limiter import login_limit
from infrastructure.security.session import require_login, require_admin, get_session_user_id, is_admin
from infrastructure.logging import logger
from infrastructure.config import AuthConfig, HttpStatus
from application.services.user_app_service import UserAppService
from application.dto.user_dto import CreateUserDTO, UpdateUserDTO
from domain.value_objects.password import Password


router = APIRouter(prefix="/api", tags=["users"])


# ============ Pydantic模型 ============

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH)
    password: str = Field(..., min_length=AuthConfig.NAME_MIN_LENGTH)
    role: str = Field(default="admin")


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
    role: Optional[str] = None,
    service: UserAppService = Depends(get_user_service)
):
    """获取所有用户（管理员）
    
    Args:
        role: 可选，按角色过滤（teacher/admin）
    """
    require_admin(request)
    
    users = service.get_all_users()
    
    # 按角色过滤
    if role:
        users = [u for u in users if u.role.value == role]
    
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


def authenticate_student(student_id: str, password: str) -> Optional[dict]:
    """验证学生登录
    
    Args:
        student_id: 学号
        password: 明文密码
        
    Returns:
        验证成功返回学生信息字典，失败返回None
    """
    db = Database()
    repo = SQLiteStudentRepository(db)
    
    # 获取学生密码信息
    password_info = repo.find_password(student_id)
    if not password_info:
        return None
    
    stored_hash, salt = password_info
    password_obj = Password.from_hash(stored_hash, salt)
    
    if not password_obj.verify(password):
        return None
    
    # 获取学生信息
    from domain.value_objects.student_id import StudentId
    student = repo.find_by_id(StudentId(student_id))
    if not student:
        return None
    
    return {
        'id': str(student.student_id),
        'username': str(student.student_id),
        'name': student.name,
        'role': 'student',
        'class_name': student.class_name
    }


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
        # 学生登录单独处理
        if data.role == 'student':
            student = authenticate_student(
                data.username.strip(),
                data.password.strip()
            )
            
            if not student:
                raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='学号或密码错误')
            
            # 防止会话固定攻击
            request.session.clear()
            
            # 写入session
            request.session['user_id'] = student['id']
            request.session['username'] = student['username']
            request.session['role'] = 'student'
            request.session['is_admin'] = False
            
            return {
                'success': True,
                'message': '登录成功',
                'user': student
            }
        
        # 管理员/教师登录
        user = service.authenticate_user(
            data.username.strip(),
            data.password.strip(),
            request.client.host
        )
        
        if user:
            # 验证角色是否匹配
            if user.role.value != data.role:
                raise HTTPException(
                    status_code=HttpStatus.FORBIDDEN, 
                    detail=f'该账号不是{data.role}账号，请选择正确的角色类型'
                )
            
            # 防止会话固定攻击：清除旧session，创建新session
            request.session.clear()
            
            # 写入新session数据
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['role'] = user.role.value
            request.session['is_admin'] = user.is_admin()
            
            return {
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role,
                    'is_admin': user.is_admin()
                }
            }
        else:
            raise HTTPException(status_code=HttpStatus.UNAUTHORIZED, detail='用户名或密码错误')
            
    except ValueError as e:
        error_msg = str(e)
        # 密码错误返回 401，账号禁用/锁定返回 403
        if "密码错误" in error_msg:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=HttpStatus.UNAUTHORIZED,
                content={'success': False, 'message': error_msg}
            )
        else:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail=error_msg)


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
    role = request.session.get('role')
    
    # 学生角色从学生表查询
    if role == 'student':
        db = Database()
        repo = SQLiteStudentRepository(db)
        from domain.value_objects.student_id import StudentId
        student = repo.find_by_id(StudentId(user_id))
        if student:
            return {
                'success': True,
                'data': {
                    'id': str(student.student_id),
                    'username': str(student.student_id),
                    'name': student.name,
                    'role': 'student',
                    'is_admin': False,
                    'assigned_classes': [student.class_name]
                }
            }
    else:
        # 管理员/教师从用户表查询
        user = service.get_user_by_id(user_id)
        if user:
            return {
                'success': True,
                'data': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role,
                    'is_admin': user.role == 'admin',
                    'assigned_classes': user.assigned_classes
                }
            }
    
    raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='用户不存在')
