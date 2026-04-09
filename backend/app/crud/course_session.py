"""
CourseSession CRUD 操作
"""
from datetime import datetime
from typing import List, Optional
import uuid
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.models import CourseSession

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def get_course_session(session: Session, session_id: int) -> Optional[CourseSession]:
    """根据ID获取课程会话"""
    return session.get(CourseSession, session_id)


def get_active_course_session_by_class_name(session: Session, class_name: str) -> Optional[CourseSession]:
    """根据班级名称获取活跃课程会话"""
    query = select(CourseSession).where(
        CourseSession.class_name == class_name,
        CourseSession.status == "active"
    )
    return session.exec(query).first()


def get_teacher_active_course_sessions(session: Session, teacher_id: int) -> List[CourseSession]:
    """获取教师所有活跃课程会话（不包含 scheduled）"""
    query = select(CourseSession).where(
        CourseSession.teacher_id == teacher_id,
        CourseSession.status == "active"  # 只返回 active，不包含 scheduled
    )
    return list(session.exec(query).all())


def get_teacher_scheduled_course_sessions(session: Session, teacher_id: int) -> List[CourseSession]:
    """获取教师所有已安排但未开始的课程"""
    query = select(CourseSession).where(
        CourseSession.teacher_id == teacher_id,
        CourseSession.status == "scheduled"
    )
    return list(session.exec(query).all())


def get_course_sessions_by_schedule_and_week(
    session: Session, schedule_id: int, week_number: int
) -> Optional[CourseSession]:
    """根据课表ID和周次获取课程会话"""
    query = select(CourseSession).where(
        CourseSession.schedule_id == schedule_id,
        CourseSession.week_number == week_number
    )
    return session.exec(query).first()


def start_course_session(
    session: Session,
    class_name: str,
    teacher_id: int,
    teacher_name: Optional[str] = None,
    course_name: Optional[str] = None,
    schedule_id: Optional[int] = None,
    week_number: Optional[int] = None,
    classroom: Optional[str] = None,
    source_type: str = "manual"
) -> CourseSession:
    """开始上课 - 创建新的课程会话记录"""
    session_code = str(uuid.uuid4())[:8].upper()
    course_session = CourseSession(
        session_code=session_code,
        schedule_id=schedule_id,
        course_name=course_name,
        class_name=class_name,
        classroom=classroom,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        status="active",
        start_time=datetime.now(SHANGHAI_TZ),
        week_number=week_number,
        source_type=source_type,
    )
    session.add(course_session)
    session.commit()
    session.refresh(course_session)
    return course_session


def end_course_session(
    session: Session,
    teacher_id: int,
    class_name: Optional[str] = None
) -> List[CourseSession]:
    """结束上课"""
    query = select(CourseSession).where(
        CourseSession.teacher_id == teacher_id,
        CourseSession.status == "active"
    )
    if class_name:
        query = query.where(CourseSession.class_name == class_name)

    sessions = session.exec(query).all()
    ended_sessions = []
    for cs in sessions:
        cs.status = "ended"
        cs.end_time = datetime.now(SHANGHAI_TZ)
        cs.updated_at = datetime.now(SHANGHAI_TZ)
        session.add(cs)
        ended_sessions.append(cs)

    if ended_sessions:
        session.commit()

    return ended_sessions


def get_teacher_course_sessions(
    session: Session, teacher_id: int, status: Optional[str] = None
) -> List[CourseSession]:
    """获取教师的课程会话列表（支持按状态筛选）"""
    query = select(CourseSession).where(CourseSession.teacher_id == teacher_id)
    if status:
        query = query.where(CourseSession.status == status)
    return list(session.exec(query.order_by(CourseSession.start_time.desc())).all())
