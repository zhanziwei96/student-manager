"""
签到相关 CRUD 操作
"""
from datetime import datetime, date
from typing import List, Optional
import uuid
from zoneinfo import ZoneInfo
from sqlmodel import Session, select, func
from app.models import CheckinRecord, ClassSession, ScoreLog

# 上海时区
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def get_class_session(session: Session, teacher_id: Optional[int] = None) -> Optional[ClassSession]:
    """获取上课状态
    
    如果提供 teacher_id，则返回该教师的活跃课堂
    """
    if teacher_id:
        query = select(ClassSession).where(
            ClassSession.teacher_id == teacher_id,
            ClassSession.active .is_(True)
        )
        return session.exec(query).first()
    return None


def get_class_session_by_class_name(session: Session, class_name: str) -> Optional[ClassSession]:
    """根据班级名称获取活跃课堂"""
    query = select(ClassSession).where(
        ClassSession.class_name == class_name,
        ClassSession.active .is_(True)
    )
    return session.exec(query).first()


def start_class(session: Session, class_name: str, teacher_id: Optional[int] = None,
                teacher_name: Optional[str] = None, course_name: Optional[str] = None) -> ClassSession:
    """开始上课 - 每次调用创建新的课堂记录"""
    # 结束该教师之前的活跃课堂
    end_class(session, teacher_id)

    # 创建新课堂记录，生成唯一 session_code
    session_code = str(uuid.uuid4())[:8].upper()
    class_session = ClassSession(
        session_code=session_code,
        course_name=course_name,
        class_name=class_name,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        active=True,
        start_time=datetime.now(SHANGHAI_TZ)
    )
    session.add(class_session)
    session.commit()
    session.refresh(class_session)
    return class_session


def end_class(session: Session, teacher_id: Optional[int] = None) -> None:
    """结束上课（根据教师ID）"""
    if teacher_id:
        # 查找该教师的活跃课堂
        query = select(ClassSession).where(
            ClassSession.teacher_id == teacher_id,
            ClassSession.active .is_(True)
        )
        class_session = session.exec(query).first()
    else:
        return
    
    if class_session:
        class_session.active = False
        class_session.end_time = datetime.now(SHANGHAI_TZ)
        class_session.updated_at = datetime.now(SHANGHAI_TZ)
        session.add(class_session)
        session.commit()


def get_today_checkins(session: Session, class_name: Optional[str] = None, session_start: Optional[datetime] = None) -> List[CheckinRecord]:
    """获取签到列表（支持按课堂开始时间筛选）"""
    from datetime import time
    
    if session_start:
        # 如果提供了课堂开始时间，只查询该时间之后的签到
        query_start = session_start
    else:
        # 否则查询今日开始
        query_start = datetime.combine(date.today(), time.min).replace(tzinfo=SHANGHAI_TZ)
    
    query = select(CheckinRecord).where(CheckinRecord.checkin_time >= query_start)
    if class_name:
        query = query.where(CheckinRecord.class_name == class_name)
    return list(session.exec(query).all())


def count_today_checkins(session: Session, class_name: Optional[str] = None) -> int:
    """使用 SQL COUNT 计算今日签到数（性能优化）
    
    相比 get_today_checkins() + len()，此函数使用数据库聚合查询，
    不加载完整对象，内存占用更少，执行更快。
    
    Args:
        session: 数据库会话
        class_name: 可选的班级名称筛选
        
    Returns:
        int: 今日签到数
    """
    from sqlalchemy import func
    from datetime import time
    
    today_start = datetime.combine(date.today(), time.min)
    
    query = select(func.count()).select_from(CheckinRecord).where(
        CheckinRecord.checkin_time >= today_start
    )
    
    if class_name:
        query = query.where(CheckinRecord.class_name == class_name)
    
    result = session.exec(query)
    return result.one()


def create_checkin(session: Session, student_id: str, student_name: str,
                   class_name: str, session_id: int, checkin_type: str = None,
                   device_id: str = None, device_info: str = None) -> CheckinRecord:
    """创建签到记录 - 关联到具体课堂 session_id，包含设备信息"""
    from app.models.constants import CheckinTypeConst
    if checkin_type is None:
        checkin_type = CheckinTypeConst.SELF
    checkin = CheckinRecord(
        session_id=session_id,
        student_id=student_id,
        student_name=student_name,
        class_name=class_name,
        checkin_type=checkin_type,
        device_id=device_id,
        device_info=device_info
    )
    session.add(checkin)
    session.commit()
    session.refresh(checkin)
    return checkin


def has_checked_in_session(session: Session, student_id: str, session_id: int) -> bool:
    """检查学生是否已在指定课堂签到"""
    query = select(CheckinRecord).where(
        CheckinRecord.student_id == student_id,
        CheckinRecord.session_id == session_id
    )
    return session.exec(query).first() is not None


def has_checked_in_today(session: Session, student_id: str, class_name: str = None, session_start: Optional[datetime] = None) -> bool:
    """检查是否已签到（支持按班级和课堂开始时间检查）- 兼容旧逻辑"""
    from datetime import time
    
    if session_start:
        # 如果提供了课堂开始时间，只检查该时间之后的签到
        query_start = session_start
    else:
        # 否则检查今日开始
        query_start = datetime.combine(date.today(), time.min).replace(tzinfo=SHANGHAI_TZ)
    
    query = select(CheckinRecord).where(
        CheckinRecord.student_id == student_id,
        CheckinRecord.checkin_time >= query_start
    )
    if class_name:
        query = query.where(CheckinRecord.class_name == class_name)
    return session.exec(query).first() is not None


def get_student_score_logs(session: Session, student_id: str, limit: int = None) -> List[ScoreLog]:
    """获取学生分数日志"""
    if limit is None:
        from app.core.config import get_settings
        limit = get_settings().pagination.score_log_default_limit
    query = select(ScoreLog).where(ScoreLog.student_id == student_id).order_by(ScoreLog.created_at.desc()).limit(limit)
    return list(session.exec(query).all())


def is_device_checked_in_session(session: Session, device_id: str, session_id: int) -> bool:
    """检查设备是否已在指定课堂签到过"""
    if not device_id:
        return False
    query = select(CheckinRecord).where(
        CheckinRecord.device_id == device_id,
        CheckinRecord.session_id == session_id
    )
    return session.exec(query).first() is not None
