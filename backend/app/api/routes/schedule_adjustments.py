"""
课表调整 API
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user
from app.models import CourseSchedule
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse
from app.crud.schedule_adjustment import (
    get_adjustments, create_adjustment, has_active_session, has_ended_session
)
from app.crud.course_session import start_course_session

router = APIRouter(tags=["schedule_adjustments"])


class CreateAdjustmentRequest(BaseModel):
    schedule_id: int
    week_number: int
    type: str
    reason: Optional[str] = None
    new_date: Optional[date] = None
    new_start_time: Optional[str] = None
    new_end_time: Optional[str] = None
    new_classroom: Optional[str] = None


class AdjustmentResponse(ApiResponse[list[dict]]):
    pass


@router.post("/schedule-adjustments", response_model=ApiSuccessResponse)
def create_schedule_adjustment(
    data: CreateAdjustmentRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """创建课表调整记录"""
    role = user.get("role", "")
    if role not in ("teacher", "admin"):
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权调整此课程")

    user_id = int(user.get("sub", 0))

    schedule = session.get(CourseSchedule, data.schedule_id)
    if not schedule:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课表不存在")
    if role == "teacher" and schedule.teacher_id != user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权调整此课程")

    if data.type == "cancel":
        # 修复：自动处理已存在的活跃或已安排的课堂
        from app.crud.course_session import get_course_sessions_by_schedule_and_week
        existing_session = get_course_sessions_by_schedule_and_week(
            session, data.schedule_id, data.week_number
        )
        if existing_session:
            if existing_session.status in ["active", "scheduled"]:
                # 自动结束活跃课堂或取消已安排的课堂
                existing_session.status = "cancelled"
                from app.core.timezone import get_now
                existing_session.end_time = get_now()
                session.add(existing_session)
            elif existing_session.status == "ended":
                raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已结束的课程不能停课")
            elif existing_session.status == "cancelled":
                raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已取消的课程不能再次停课")

    if data.type == "modify":
        if has_ended_session(session, data.schedule_id, data.week_number):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已结束的课程不能调课")

    generated_session_id = None
    if data.type == "makeup":
        if not data.new_date:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="补课必须指定日期")

        # 修复：创建 scheduled 状态的课堂（而非 active）
        from datetime import datetime
        from zoneinfo import ZoneInfo

        # 构建补课的开始和结束时间
        makeup_start = None
        makeup_end = None
        if data.new_start_time:
            time_parts = data.new_start_time.split(":")
            makeup_start = datetime.combine(
                data.new_date,
                datetime.strptime(data.new_start_time, "%H:%M").time()
            ).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        if data.new_end_time:
            makeup_end = datetime.combine(
                data.new_date,
                datetime.strptime(data.new_end_time, "%H:%M").time()
            ).replace(tzinfo=ZoneInfo("Asia/Shanghai"))

        course_session = start_course_session(
            session=session,
            class_name=schedule.class_name,
            teacher_id=schedule.teacher_id or user_id,
            teacher_name=schedule.teacher_name,
            course_name=schedule.course_name,
            schedule_id=data.schedule_id,
            week_number=data.week_number,
            classroom=data.new_classroom or schedule.classroom,
            source_type="makeup",
        )
        # 设置为 scheduled 状态并设置正确的时间
        course_session.status = "scheduled"
        if makeup_start:
            course_session.start_time = makeup_start
        if makeup_end:
            course_session.end_time = makeup_end
        session.add(course_session)
        session.commit()
        session.refresh(course_session)
        generated_session_id = course_session.id

    create_adjustment(
        session=session,
        schedule_id=data.schedule_id,
        week_number=data.week_number,
        adjustment_type=data.type,
        created_by=user_id,
        reason=data.reason,
        new_date=data.new_date,
        new_start_time=data.new_start_time,
        new_end_time=data.new_end_time,
        new_classroom=data.new_classroom,
        generated_session_id=generated_session_id,
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "调整记录已创建"
    }


@router.get("/schedule-adjustments", response_model=AdjustmentResponse)
def list_schedule_adjustments(
    schedule_id: Optional[int] = Query(None),
    week_number: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """查询课表调整记录"""
    adjustments = get_adjustments(session, schedule_id=schedule_id, week_number=week_number)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "id": a.id,
                "schedule_id": a.schedule_id,
                "week_number": a.week_number,
                "type": a.type,
                "reason": a.reason,
                "new_date": str(a.new_date) if a.new_date else None,
                "new_start_time": a.new_start_time,
                "new_end_time": a.new_end_time,
                "new_classroom": a.new_classroom,
                "generated_session_id": a.generated_session_id,
                "created_by": a.created_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in adjustments
        ]
    }
