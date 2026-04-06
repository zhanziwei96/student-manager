"""
签到相关 API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Body, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus
from app.crud import (
    get_today_checkins, create_checkin,
    get_students_by_class
)
from app.crud.course_session import (
    get_active_course_session_by_class_name,
    get_teacher_active_course_sessions,
)
from app.crud.checkin import has_checked_in_session, is_device_checked_in_session
from app.core.jwt import get_current_user
from app.models.constants import (
    ApiResponseConst, MessageConst,
    ApiResponse, ApiSuccessResponse
)
from app.models import CourseSession

router = APIRouter(tags=["checkin"])


class CheckinRequest(BaseModel):
    student_id: str = Field(..., description="学号")
    student_name: str = Field(..., description="姓名")
    device_id: Optional[str] = Field(default=None, description="设备指纹ID")
    device_info: Optional[str] = Field(default=None, description="设备信息JSON")


class CheckinData(BaseModel):
    """签到数据"""
    id: int
    student_id: str
    student_name: str
    class_name: str
    checkin_time: datetime
    checkin_type: str
    session_id: int


class CheckinStatsData(BaseModel):
    """签到统计数据"""
    active: bool
    course_name: Optional[str] = None
    class_name: Optional[str] = None
    total: int
    checked_in: int
    not_checked_in: int
    rate: float


class ActiveSessionData(BaseModel):
    """活跃课堂数据"""
    course_name: Optional[str] = None
    class_name: Optional[str] = None
    teacher_id: int
    teacher_name: Optional[str] = None
    start_time: Optional[datetime] = None


class StudentSessionData(BaseModel):
    """学生端课堂数据"""
    id: Optional[int] = None
    session_code: Optional[str] = None
    active: bool = True
    course_name: Optional[str] = None
    class_name: Optional[str] = None
    teacher_name: Optional[str] = None
    start_time: Optional[datetime] = None


class CheckinResponse(ApiResponse[CheckinData]):
    """签到响应"""
    pass


class CheckinListResponse(ApiResponse[list[CheckinData]]):
    """签到列表响应"""
    pass


class CheckinStatsResponse(ApiResponse[CheckinStatsData]):
    """签到统计响应"""
    pass


class ActiveSessionsResponse(ApiResponse[list[ActiveSessionData]]):
    """活跃课堂列表响应"""
    pass


class StudentSessionResponse(ApiResponse[StudentSessionData]):
    """学生端课堂响应"""
    pass


@router.post("/checkin", response_model=CheckinResponse)
def do_checkin(
    request: Request,
    data: CheckinRequest,
    db_session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """学生签到"""
    # 验证学生
    from app.crud import get_student
    student = get_student(db_session, data.student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    # 检查学生所在班级是否有活跃课堂
    cs = get_active_course_session_by_class_name(db_session, student.class_name)
    if not cs or cs.status != "active":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='当前未在上课')

    # 检查是否在当前课堂已签到
    if has_checked_in_session(db_session, data.student_id, cs.id):
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='您已在本课堂签到')

    # 验证设备唯一性（如果提供了设备ID）
    if data.device_id:
        if is_device_checked_in_session(db_session, data.device_id, cs.id):
            raise HTTPException(status_code=HttpStatus.CONFLICT, detail='该设备已签到')

    # 创建签到记录
    checkin = create_checkin(
        db_session,
        data.student_id,
        data.student_name or student.name,
        cs.class_name,
        cs.id,
        device_id=data.device_id,
        device_info=data.device_info
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CHECKIN_SUCCESS,
        ApiResponseConst.DATA: checkin.model_dump()
    }


@router.get("/checkins/today", response_model=CheckinListResponse)
def get_today_checkin_list(
    request: Request,
    class_name: Optional[str] = Query(None, description="班级名称"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取今日签到列表（只返回当前课堂开始后的签到）"""
    # 根据班级名称获取活跃课堂
    cs = get_active_course_session_by_class_name(session, class_name) if class_name else None

    # 只查询当前课堂开始时间之后的签到（如果课堂活跃）
    if cs and cs.status == "active":
        checkins = get_today_checkins(session, class_name, cs.start_time)
    elif class_name:
        # 指定了班级但没有活跃课堂，返回今日该班级所有签到（用于历史查看）
        checkins = get_today_checkins(session, class_name)
    else:
        # 没有指定班级，返回今日所有签到
        checkins = get_today_checkins(session)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [c.model_dump() for c in checkins]
    }


@router.get("/checkins/stats", response_model=CheckinStatsResponse)
def get_checkin_stats(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取签到统计（当前教师的活跃课堂）"""
    teacher_id = int(user.get("sub", 0))
    course_sessions = get_teacher_active_course_sessions(session, teacher_id)

    if not course_sessions:
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

    cs = course_sessions[0]
    students = get_students_by_class(session, cs.class_name)
    # 只统计当前课堂开始后的签到
    checkins = get_today_checkins(session, cs.class_name, cs.start_time)

    total = len(students)
    checked_in = len(checkins)
    not_checked_in = total - checked_in
    rate = round(checked_in / total * 100, 1) if total > 0 else 0

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'active': True,
            'course_name': cs.course_name,
            'class_name': cs.class_name,
            'total': total,
            'checked_in': checked_in,
            'not_checked_in': not_checked_in,
            'rate': rate
        }
    }


@router.get("/course-sessions/active", response_model=ActiveSessionsResponse)
def get_active_course_sessions(
    request: Request,
    session: Session = Depends(get_session)
):
    """获取所有活跃课堂列表"""
    from sqlmodel import select
    query = select(CourseSession).where(CourseSession.status == "active")
    active_sessions = session.exec(query).all()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                'course_name': s.course_name,
                'class_name': s.class_name,
                'teacher_id': s.teacher_id,
                'teacher_name': s.teacher_name,
                'start_time': s.start_time
            }
            for s in active_sessions
        ]
    }


@router.get("/course-sessions/class/{class_name}", response_model=StudentSessionResponse)
async def get_course_session_for_student(
    class_name: str,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取指定班级的活跃课堂状态（学生端使用）"""
    # 用户认证已通过 Depends(get_current_user) 完成

    cs = get_active_course_session_by_class_name(session, class_name)

    if cs and cs.status == "active":
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'id': cs.id,
                'session_code': cs.session_code,
                'active': True,
                'course_name': cs.course_name,
                'class_name': cs.class_name,
                'teacher_name': cs.teacher_name,
                'start_time': cs.start_time
            }
        }

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {'active': False}
    }
