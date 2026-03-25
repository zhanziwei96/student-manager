"""
学生管理 API - JWT 版本
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query, UploadFile, File, Body
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus, get_settings
from app.core.jwt import require_login, require_admin, get_current_user
from app.crud import (
    get_student, get_students, get_students_by_class,
    create_student, update_student_score, delete_student, get_all_classes, reset_student_password
)
from app.crud.checkin import get_class_session, get_today_checkins
from app.models.constants import (
    ApiResponseConst, MessageConst, RoutePrefixConst
)

router = APIRouter(prefix=RoutePrefixConst.API, tags=["students"])


class CreateStudentRequest(BaseModel):
    student_id: str = Field(..., min_length=1, description="学号")
    name: str = Field(..., min_length=1, description="姓名")
    class_name: Optional[str] = Field(None, description="班级")


class UpdateScoreRequest(BaseModel):
    score_change: float = Field(..., description="分数变动值")
    reason: str = Field(..., min_length=1, description="变动原因")


@router.get("/students")
async def get_students_list(
    request: Request,
    class_name: Optional[str] = Query(None, description="班级名称"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生列表（管理员看所有，教师看负责班级）"""
    # 使用 CRUD 层的权限控制函数，将业务逻辑从 API 层分离
    from app.crud.student import get_students_by_permission
    
    students, error = get_students_by_permission(session, user, class_name)
    if error:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail=error)
    
    # 获取当前课堂会话
    class_session = get_class_session(session)
    current_class = class_session.class_name if class_session and class_session.active else None
    
    # 只获取当前课堂的签到记录（如果没有活跃课堂，则无人活跃）
    if current_class:
        checkins = get_today_checkins(session, current_class)
    else:
        checkins = []
    checked_in_students = set(c.student_id for c in checkins)
    
    # 构建带签到状态的学生列表
    students_with_status = []
    for student in students:
        student_dict = student.model_dump()
        # 只有在当前课堂签到才算活跃
        student_dict['status'] = 'active' if student.student_id in checked_in_students else 'inactive'
        students_with_status.append(student_dict)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: students_with_status
    }


@router.get("/students/{student_id}")
async def get_student_info(
    request: Request,
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生信息（学生只能查看自己）"""
    from app.models import UserRoleConst
    
    is_admin = user.get("is_admin", False)
    role = user.get("role", '')
    user_id = user.get("sub", '')
    
    # 学生只能查看自己的信息
    if role == UserRoleConst.STUDENT and student_id != user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='无权查看其他学生信息')
    
    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: student.model_dump()
    }


@router.post("/students")
async def add_student(
    request: Request,
    data: CreateStudentRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """添加学生"""
    existing = get_student(session, data.student_id)
    if existing:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='学号已存在')
    
    student = create_student(
        session, 
        data.student_id, 
        data.name, 
        data.class_name or "未分班"
    )
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.STUDENT_CREATED,
        ApiResponseConst.DATA: student.model_dump()
    }


@router.put("/students/{student_id}/score")
async def update_score(
    request: Request,
    student_id: str,
    data: UpdateScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """更新学生分数"""
    username = user.get("username", '')
    
    student = update_student_score(session, student_id, data.score_change, data.reason, username)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.STUDENT_SCORE_UPDATED,
        ApiResponseConst.DATA: {
            'student_id': student.student_id,
            'name': student.name,
            'class_name': student.class_name,
            'score': student.score,
            'is_active': student.is_active
        }
    }


@router.delete("/students/{student_id}")
async def remove_student(
    request: Request,
    student_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """删除学生"""
    success = delete_student(session, student_id)
    if not success:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.STUDENT_DELETED
    }


@router.get("/classes")
async def get_classes(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取班级列表（管理员看所有，教师看负责班级）"""
    # 使用 CRUD 层的权限控制函数，将业务逻辑从 API 层分离
    from app.crud.student import get_classes_by_permission
    
    class_names, error = get_classes_by_permission(session, user)
    if error:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail=error)
    
    # 获取当前课堂会话状态
    class_session = get_class_session(session)
    current_class = class_session.class_name if class_session and class_session.active else None
    
    # 返回带状态的班级列表
    classes_with_status = [
        {
            'name': class_name,
            'status': 'active' if class_name == current_class else 'inactive'
        }
        for class_name in class_names
    ]
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: classes_with_status
    }


@router.post("/students/import")
async def import_students(
    request: Request,
    file: UploadFile = File(..., description="Excel文件 (.xlsx/.xls)"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """导入学生（Excel）- SEC-001: 安全文件上传"""
    from app.core.upload import save_upload_file_securely, cleanup_file
    from app.core.logging import logger
    
    settings = get_settings()
    file_path = None
    
    try:
        # SEC-001: 安全保存文件
        # - 验证文件扩展名白名单
        # - 验证MIME类型
        # - 检查文件大小
        # - 使用UUID重命名
        file_path, original_filename = await save_upload_file_securely(
            file,
            allowed_extensions=settings.upload.allowed_extensions,
            allowed_content_types=settings.upload.allowed_content_types,
            max_size_mb=settings.upload.max_file_size_mb,
            use_uuid=settings.upload.use_uuid_filename,
            upload_directory=settings.upload.directory
        )
        
        # TODO: 实现Excel解析和学生导入逻辑
        # 这里应该调用导入服务解析Excel并导入学生数据
        # 目前仅演示安全上传功能
        
        logger.info(f"学生导入文件已接收: {original_filename} (上传者: {user.get('username')})")
        
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.MESSAGE: f"文件 '{original_filename}' 上传成功，导入功能开发中"
        }
        
    except HTTPException:
        # 重新抛出HTTP异常（来自save_upload_file_securely）
        raise
    except Exception as e:
        logger.error(f"学生导入失败: {e}")
        raise HTTPException(
            status_code=HttpStatus.INTERNAL_ERROR,
            detail=f"导入失败: {str(e)}"
        )
    finally:
        # SEC-001: 清理临时文件
        if file_path:
            cleanup_file(file_path)


@router.get("/students/{student_id}/scores")
async def get_student_scores(
    request: Request,
    student_id: str,
    limit: int = Query(None, description="数量限制"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生分数历史"""
    from app.crud import get_student_score_logs
    logs = get_student_score_logs(session, student_id, limit)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [log.model_dump() for log in logs]
    }


class ResetStudentPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=1, description="新密码")


@router.put("/students/{student_id}/reset-password")
async def reset_student_password_api(
    request: Request,
    student_id: str,
    data: ResetStudentPasswordRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """重置学生密码"""
    from app.core.security import generate_password_hash
    password_hash, salt = generate_password_hash(data.new_password)
    
    student = reset_student_password(session, student_id, password_hash, salt)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.PASSWORD_RESET
    }
