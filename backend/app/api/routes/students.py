"""
学生管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query, UploadFile, File, Body
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus, get_settings
from app.crud import (
    get_student, get_students, get_students_by_class,
    create_student, update_student_score, delete_student, get_all_classes, reset_student_password
)
from app.api.deps import require_login, require_admin, is_admin, get_session_user_id, SessionKeyConst
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
def get_students_list(
    request: Request,
    class_name: Optional[str] = Query(None, description="班级名称"),
    session: Session = Depends(get_session)
):
    """获取学生列表（管理员看所有，教师看负责班级）"""
    user_id = require_login(request)
    is_admin = request.session.get(SessionKeyConst.IS_ADMIN, False)
    
    if is_admin:
        # 管理员可以查看所有学生
        if class_name:
            students = get_students_by_class(session, class_name)
        else:
            students = get_students(session)
    else:
        # 教师只能查看负责班级的学生
        from app.crud import get_user
        user = get_user(session, user_id)
        assigned_classes = user.get_assigned_classes() if user else []
        
        # 如果指定了班级，检查是否有权限
        if class_name:
            if class_name not in assigned_classes:
                raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='无权查看该班级学生')
            students = get_students_by_class(session, class_name)
        else:
            # 获取所有负责班级的学生
            students = []
            for cls in assigned_classes:
                students.extend(get_students_by_class(session, cls))
            # 去重（防止同一学生在多个班级的情况）
            seen = set()
            unique_students = []
            for s in students:
                if s.student_id not in seen:
                    seen.add(s.student_id)
                    unique_students.append(s)
            students = unique_students
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [s.model_dump() for s in students]
    }


@router.post("/students")
def add_student(
    request: Request,
    data: CreateStudentRequest,
    session: Session = Depends(get_session)
):
    """添加学生"""
    require_login(request)
    
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
def update_score(
    request: Request,
    student_id: str,
    data: UpdateScoreRequest,
    session: Session = Depends(get_session)
):
    """更新学生分数"""
    user_id = require_login(request)
    username = request.session.get(SessionKeyConst.USERNAME, '')
    
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
def remove_student(
    request: Request,
    student_id: str,
    session: Session = Depends(get_session)
):
    """删除学生"""
    require_admin(request)
    
    success = delete_student(session, student_id)
    if not success:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.STUDENT_DELETED
    }


@router.get("/classes")
def get_classes(
    request: Request,
    session: Session = Depends(get_session)
):
    """获取班级列表"""
    require_login(request)
    classes = get_all_classes(session)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: classes
    }


@router.post("/students/import")
def import_students(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """导入学生（Excel）"""
    require_login(request)
    # TODO: 实现导入逻辑
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.IMPORT_PENDING
    }


@router.get("/students/{student_id}/scores")
def get_student_scores(
    request: Request,
    student_id: str,
    limit: int = Query(None, description="数量限制"),
    session: Session = Depends(get_session)
):
    """获取学生分数历史"""
    require_login(request)
    
    from app.crud import get_student_score_logs
    logs = get_student_score_logs(session, student_id, limit)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [log.model_dump() for log in logs]
    }


class ResetStudentPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=1, description="新密码")


@router.put("/students/{student_id}/reset-password")
def reset_student_password_api(
    request: Request,
    student_id: str,
    data: ResetStudentPasswordRequest,
    session: Session = Depends(get_session)
):
    """重置学生密码"""
    require_admin(request)
    
    from app.core.security import generate_password_hash
    password_hash, salt = generate_password_hash(data.new_password)
    
    student = reset_student_password(session, student_id, password_hash, salt)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.PASSWORD_RESET
    }
