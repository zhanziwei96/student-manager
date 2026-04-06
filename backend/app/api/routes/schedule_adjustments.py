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
    user_id = int(user.get("sub", 0))
    role = user.get("role", "")

    schedule = session.get(CourseSchedule, data.schedule_id)
    if not schedule:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课表不存在")
    if role == "teacher" and schedule.teacher_id != user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权调整此课程")

    if data.type == "cancel":
        if has_active_session(session, data.schedule_id, data.week_number):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="进行中的课程不能停课")

    if data.type == "modify":
        if has_ended_session(session, data.schedule_id, data.week_number):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已结束的课程不能调课")

    generated_session_id = None
    if data.type == "makeup":
        if not data.new_date:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="补课必须指定日期")
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
