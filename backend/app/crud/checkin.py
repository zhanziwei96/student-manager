"""
签到相关 CRUD 操作
"""
from datetime import datetime, date
from typing import List, Optional
from sqlmodel import Session, select, func
from app.models import CheckinRecord, ClassSession, ScoreLog


def get_class_session(session: Session) -> Optional[ClassSession]:
    """获取上课状态"""
    return session.get(ClassSession, 1)


def start_class(session: Session, class_name: str) -> ClassSession:
    """开始上课"""
    class_session = session.get(ClassSession, 1)
    if not class_session:
        class_session = ClassSession(id=1, class_name=class_name, active=True, start_time=datetime.now())
    else:
        class_session.class_name = class_name
        class_session.active = True
        class_session.start_time = datetime.now()
    session.add(class_session)
    session.commit()
    session.refresh(class_session)
    return class_session


def end_class(session: Session) -> None:
    """结束上课"""
    class_session = session.get(ClassSession, 1)
    if class_session:
        class_session.active = False
        class_session.class_name = None
        class_session.start_time = None
        session.add(class_session)
        session.commit()


def get_today_checkins(session: Session, class_name: Optional[str] = None) -> List[CheckinRecord]:
    """获取今日签到列表"""
    from datetime import datetime, time
    today_start = datetime.combine(date.today(), time.min)
    
    query = select(CheckinRecord).where(CheckinRecord.checkin_time >= today_start)
    if class_name:
        query = query.where(CheckinRecord.class_name == class_name)
    return session.exec(query).all()


def create_checkin(session: Session, student_id: str, student_name: str, 
                   class_name: str, checkin_type: str = None) -> CheckinRecord:
    """创建签到记录"""
    from app.models.constants import CheckinTypeConst
    if checkin_type is None:
        checkin_type = CheckinTypeConst.SELF
    checkin = CheckinRecord(
        student_id=student_id,
        student_name=student_name,
        class_name=class_name,
        checkin_type=checkin_type
    )
    session.add(checkin)
    session.commit()
    session.refresh(checkin)
    return checkin


def has_checked_in_today(session: Session, student_id: str) -> bool:
    """检查今日是否已签到"""
    from datetime import datetime, time
    today_start = datetime.combine(date.today(), time.min)
    
    query = select(CheckinRecord).where(
        CheckinRecord.student_id == student_id,
        CheckinRecord.checkin_time >= today_start
    )
    return session.exec(query).first() is not None


def get_student_score_logs(session: Session, student_id: str, limit: int = None) -> List[ScoreLog]:
    """获取学生分数日志"""
    if limit is None:
        from app.core.config import get_settings
        limit = get_settings().pagination.score_log_default_limit
    query = select(ScoreLog).where(ScoreLog.student_id == student_id).order_by(ScoreLog.created_at.desc()).limit(limit)
    return session.exec(query).all()
