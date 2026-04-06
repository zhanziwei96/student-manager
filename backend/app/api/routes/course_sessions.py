"""
课程会话 API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user
from app.models import CourseSession, CourseSchedule
from app.models.constants import ApiResponseConst, MessageConst, ApiResponse, ApiSuccessResponse
from app.crud.course_session import (
    get_teacher_active_course_sessions,
    get_active_course_session_by_class_name,
    start_course_session,
    get_teacher_course_sessions,
)
from app.crud.schedule_adjustment import get_adjustment

router = APIRouter(tags=["course_sessions"])


class StartCourseSessionRequest(BaseModel):
    class_name: str
    course_name: Optional[str] = None
    schedule_id: Optional[int] = None


class CourseSessionData(BaseModel):
    id: int
    active: bool
    course_name: Optional[str] = None
    class_name: str
    start_time: Optional[datetime] = None
    status: str
    session_code: str
    schedule_id: Optional[int] = None
    week_number: Optional[int] = None
    source_type: str


class CourseSessionListResponse(ApiResponse[list[CourseSessionData]]):
    pass


class CourseSessionResponse(ApiResponse[CourseSessionData]):
    pass


@router.get("/course-sessions", response_model=CourseSessionListResponse)
def get_course_sessions(
    request: Request,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取当前教师的课程会话列表"""
    teacher_id = int(user.get("sub", 0))
    if status:
        sessions = get_teacher_course_sessions(session, teacher_id, status=status)
    else:
        sessions = get_teacher_active_course_sessions(session, teacher_id)

    data = []
    for cs in sessions:
        data.append({
            "id": cs.id,
            "active": cs.status == "active",
            "course_name": cs.course_name,
            "class_name": cs.class_name,
            "start_time": cs.start_time,
            "end_time": cs.end_time,
            "status": cs.status,
            "session_code": cs.session_code,
            "schedule_id": cs.schedule_id,
            "week_number": cs.week_number,
            "source_type": cs.source_type,
        })

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: data
    }


@router.post("/course-sessions/start", response_model=CourseSessionResponse)
def begin_course_session(
    request: Request,
    data: StartCourseSessionRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """开始上课"""
    existing = get_active_course_session_by_class_name(session, data.class_name)
    if existing:
        teacher_name = existing.teacher_name or "其他教师"
        raise HTTPException(
            status_code=HttpStatus.CONFLICT,
            detail=f"该班级正在被 {teacher_name} 老师上课，无法开始新课堂"
        )

    teacher_id = int(user.get("sub", 0))
    teacher_name = user.get("name", "")

    schedule_id = data.schedule_id
    week_number = None
    classroom = None
    source_type = "manual"

    if schedule_id:
        schedule = session.get(CourseSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课表不存在")
        if schedule.class_name != data.class_name:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="班级与课表不匹配")
        if data.course_name and schedule.course_name != data.course_name:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="课程名称与课表不匹配")
        week_number = _get_current_week_number()
        classroom = schedule.classroom
        source_type = "scheduled"
        if not data.course_name:
            data.course_name = schedule.course_name

    course_session = start_course_session(
        session=session,
        class_name=data.class_name,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        course_name=data.course_name,
        schedule_id=schedule_id,
        week_number=week_number,
        classroom=classroom,
        source_type=source_type,
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_STARTED,
        ApiResponseConst.DATA: {
            "id": course_session.id,
            "active": True,
            "course_name": course_session.course_name,
            "class_name": course_session.class_name,
            "start_time": course_session.start_time,
            "status": course_session.status,
            "session_code": course_session.session_code,
            "schedule_id": course_session.schedule_id,
            "week_number": course_session.week_number,
            "source_type": course_session.source_type,
        }
    }


@router.post("/course-sessions/{session_id}/end", response_model=ApiSuccessResponse)
def finish_course_session(
    session_id: int,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """结束指定课程会话"""
    teacher_id = int(user.get("sub", 0))
    cs = session.get(CourseSession, session_id)
    if not cs or cs.teacher_id != teacher_id:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课堂不存在")
    if cs.status != "active":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="课堂未在活跃状态")

    cs.status = "ended"
    from app.core.timezone import get_now
    cs.end_time = get_now()
    cs.updated_at = get_now()
    session.add(cs)
    session.commit()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_ENDED
    }


@router.get("/course-sessions/class/{class_name}", response_model=ApiResponse[dict])
async def get_course_session_for_class(
    class_name: str,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取指定班级的活跃课程会话（学生端使用）"""
    cs = get_active_course_session_by_class_name(session, class_name)
    if cs and cs.status == "active":
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                "id": cs.id,
                "session_code": cs.session_code,
                "active": True,
                "course_name": cs.course_name,
                "class_name": cs.class_name,
                "teacher_name": cs.teacher_name,
                "start_time": cs.start_time,
            }
        }

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"active": False}
    }


def _get_current_week_number() -> int:
    """获取当前教学周次（与前端 getCurrentWeek 保持一致）"""
    from datetime import datetime
    now = datetime.now()
    semester_start = datetime(now.year, 2, 1)
    if now < semester_start:
        semester_start = datetime(now.year - 1, 2, 1)
    delta = now - semester_start
    week = delta.days // 7 + 1
    return max(1, week)
