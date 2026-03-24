"""
签到相关 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus
from app.crud import (
    get_class_session, start_class, end_class,
    get_today_checkins, create_checkin, has_checked_in_today
)
from app.api.deps import require_login
from app.models.constants import (
    ApiResponseConst, MessageConst, RoutePrefixConst
)

router = APIRouter(prefix=RoutePrefixConst.API, tags=["checkin"])


class CheckinRequest(BaseModel):
    student_id: str = Field(..., description="学号")
    student_name: str = Field(..., description="姓名")


class StartClassRequest(BaseModel):
    class_name: str = Field(..., description="班级名称")


@router.get("/class-session")
def get_current_session(
    request: Request,
    session: Session = Depends(get_session)
):
    """获取当前上课状态"""
    class_session = get_class_session(session)
    if class_session:
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'active': class_session.active,
                'class_name': class_session.class_name,
                'start_time': class_session.start_time
            }
        }
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {'active': False}
    }


@router.post("/class-session/start")
async def begin_class(
    request: Request,
    data: StartClassRequest,
    session: Session = Depends(get_session)
):
    """开始上课"""
    await require_login(request)
    
    class_session = start_class(session, data.class_name)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_STARTED,
        ApiResponseConst.DATA: class_session.model_dump()
    }


@router.post("/class-session/end")
async def finish_class(
    request: Request,
    session: Session = Depends(get_session)
):
    """结束上课"""
    await require_login(request)
    
    end_class(session)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_ENDED
    }


@router.post("/checkin")
def do_checkin(
    request: Request,
    data: CheckinRequest,
    session: Session = Depends(get_session)
):
    """学生签到"""
    # 检查是否正在上课
    class_session = get_class_session(session)
    if not class_session or not class_session.active:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='当前未在上课')
    
    # 验证学生
    from app.crud import get_student
    student = get_student(session, data.student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    # 检查是否已签到
    if has_checked_in_today(session, data.student_id):
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='今日已签到')
    
    # 创建签到记录（如果前端未提供姓名，使用数据库中的姓名）
    checkin = create_checkin(
        session,
        data.student_id,
        data.student_name or student.name,
        class_session.class_name
    )
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CHECKIN_SUCCESS,
        ApiResponseConst.DATA: checkin.model_dump()
    }


@router.get("/checkins/today")
def get_today_checkin_list(
    request: Request,
    class_name: Optional[str] = Query(None, description="班级名称"),
    session: Session = Depends(get_session)
):
    """获取今日签到列表"""
    checkins = get_today_checkins(session, class_name)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [c.model_dump() for c in checkins]
    }


@router.get("/checkins/stats")
def get_checkin_stats(
    request: Request,
    session: Session = Depends(get_session)
):
    """获取签到统计"""
    class_session = get_class_session(session)
    if not class_session or not class_session.active:
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'active': False,
                'total': 0,
                'checked_in': 0,
                'not_checked_in': 0,
                'rate': 0
            }
        }
    
    from app.crud import get_students_by_class
    students = get_students_by_class(session, class_session.class_name)
    checkins = get_today_checkins(session, class_session.class_name)
    
    total = len(students)
    checked_in = len(checkins)
    not_checked_in = total - checked_in
    rate = round(checked_in / total * 100, 1) if total > 0 else 0
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'active': True,
            'class_name': class_session.class_name,
            'total': total,
            'checked_in': checked_in,
            'not_checked_in': not_checked_in,
            'rate': rate
        }
    }
