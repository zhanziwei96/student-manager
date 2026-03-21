"""
课堂会话API控制器 - FastAPI版本
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field

from application.services.class_session_service import ClassSessionService
from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
from infrastructure.persistence.repositories.sqlite_checkin_repository import SQLiteCheckinRepository
from infrastructure.security.session import require_login, is_admin
from infrastructure.logging import logger


router = APIRouter(prefix="/api", tags=["class_session"])


# ============ Pydantic模型 ============

class ClassSessionRequest(BaseModel):
    class_name: str = Field(default="", description="班级名称（空字符串表示结束上课）")


# ============ API端点 ============

@router.get("/class-session", response_model=dict)
async def get_class_session(request: Request):
    """获取当前课堂会话状态（公开接口）"""
    try:
        cs = ClassSessionService.get_session(request)
        
        if cs and cs.active:
            return {
                'success': True,
                'data': {
                    'active': True,
                    'class_name': cs.class_name,
                    'started_at': cs.started_at
                }
            }
        
        return {
            'success': True,
            'data': {'active': False}
        }
        
    except Exception as e:
        logger.error(f"获取课堂会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/class-session", response_model=dict)
async def set_class_session(
    request: Request,
    data: ClassSessionRequest
):
    """设置当前课堂会话（老师）"""
    user_id = require_login(request)
    
    try:
        class_name = data.class_name.strip()
        
        if not class_name:
            # 空字符串表示结束上课
            ClassSessionService.clear_session(request)
            return {
                'success': True,
                'message': '已结束上课',
                'data': {'active': False}
            }
        
        # 设置新的课堂会话
        cs = ClassSessionService.set_session(
            request=request,
            class_name=class_name,
            user_id=user_id
        )
        
        return {
            'success': True,
            'message': f'开始上课：{class_name}',
            'data': {
                'active': True,
                'class_name': cs.class_name,
                'started_at': cs.started_at
            }
        }
        
    except Exception as e:
        logger.error(f"设置课堂会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class-session/students", response_model=dict)
async def get_class_session_students(request: Request):
    """获取当前课堂的学生列表及签到状态（公开接口）"""
    try:
        cs = ClassSessionService.get_session(request)
        
        if not cs or not cs.active:
            return {
                'success': True,
                'data': [],
                'stats': {
                    'total': 0,
                    'checked_in': 0,
                    'not_checked_in': 0,
                    'rate': 0
                }
            }
        
        # 获取班级所有学生
        db = Database()
        student_repo = SQLiteStudentRepository(db)
        checkin_repo = SQLiteCheckinRepository(db)
        
        students = student_repo.find_by_class(cs.class_name)
        
        # 获取今日签到记录
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        checkins = checkin_repo.find_by_filters(
            class_name=cs.class_name,
            date=today
        )
        
        # 构建签到状态映射
        checked_in_map = {c.student_id: c for c in checkins}
        
        # 构建学生列表（带签到状态）
        result = []
        for student in students:
            checkin = checked_in_map.get(student.student_id.value)
            result.append({
                'student_id': student.student_id.value,
                'name': student.name,
                'checked_in': checkin is not None,
                'checkin_time': checkin.checkin_time if checkin else None,
                'checkin_type': checkin.checkin_type.value if checkin else None
            })
        
        # 统计
        total = len(result)
        checked_in_count = sum(1 for s in result if s['checked_in'])
        
        return {
            'success': True,
            'data': result,
            'stats': {
                'total': total,
                'checked_in': checked_in_count,
                'not_checked_in': total - checked_in_count,
                'rate': round(checked_in_count / total * 100, 1) if total > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"获取课堂学生列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
