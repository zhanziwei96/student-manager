"""
课表调整记录 CRUD 操作
"""
from datetime import date
from typing import List, Optional
from sqlmodel import Session, select
from app.models import ScheduleAdjustment


def get_adjustment(
    session: Session, schedule_id: int, week_number: int
) -> Optional[ScheduleAdjustment]:
    """获取指定课表和周次的调整记录"""
    query = select(ScheduleAdjustment).where(
        ScheduleAdjustment.schedule_id == schedule_id,
        ScheduleAdjustment.week_number == week_number
    )
    return session.exec(query).first()


def get_adjustments(
    session: Session,
    schedule_id: Optional[int] = None,
    week_number: Optional[int] = None,
    class_name: Optional[str] = None,
) -> List[ScheduleAdjustment]:
    """查询调整记录列表"""
    query = select(ScheduleAdjustment)
    if schedule_id is not None:
        query = query.where(ScheduleAdjustment.schedule_id == schedule_id)
    if week_number is not None:
        query = query.where(ScheduleAdjustment.week_number == week_number)
    if class_name is not None:
        from app.core.class_cache import get_class_ids_by_names
        from app.models import CourseSchedule
        query = query.join(CourseSchedule).where(
            CourseSchedule.class_id.in_(get_class_ids_by_names(session, [class_name])))
    return list(session.exec(query.order_by(ScheduleAdjustment.created_at.desc())).all())


def create_adjustment(
    session: Session,
    schedule_id: int,
    week_number: int,
    adjustment_type: str,
    created_by: int,
    reason: Optional[str] = None,
    new_date: Optional[date] = None,
    new_start_time: Optional[str] = None,
    new_end_time: Optional[str] = None,
    new_classroom: Optional[str] = None,
    generated_session_id: Optional[int] = None,
) -> ScheduleAdjustment:
    """创建调整记录（semester_id 继承课表所属学期）"""
    from app.models import CourseSchedule

    schedule = session.get(CourseSchedule, schedule_id)
    adjustment = ScheduleAdjustment(
        schedule_id=schedule_id,
        semester_id=schedule.semester_id,
        week_number=week_number,
        type=adjustment_type,
        reason=reason,
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time,
        new_classroom=new_classroom,
        generated_session_id=generated_session_id,
        created_by=created_by,
    )
    session.add(adjustment)
    session.commit()
    session.refresh(adjustment)
    return adjustment


def has_active_session(
    session: Session, schedule_id: int, week_number: int
) -> bool:
    """检查指定课表和周次是否有活跃课堂"""
    from app.crud.course_session import get_course_sessions_by_schedule_and_week
    cs = get_course_sessions_by_schedule_and_week(session, schedule_id, week_number)
    return cs is not None and cs.status == "active"


def has_ended_session(
    session: Session, schedule_id: int, week_number: int
) -> bool:
    """检查指定课表和周次是否有已结束课堂"""
    from app.crud.course_session import get_course_sessions_by_schedule_and_week
    cs = get_course_sessions_by_schedule_and_week(session, schedule_id, week_number)
    return cs is not None and cs.status == "ended"
