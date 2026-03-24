"""
签到相关 CRUD 操作
"""
from datetime import datetime, date
from typing import List, Optional
from sqlmodel import Session, select, func
from app.models import CheckinRecord, ClassSession, ScoreLog


def get_class_session(session: Session, teacher_id: int = None) -> Optional[ClassSession]:
    """获取上课状态
    
    如果提供 teacher_id，则返回该教师的活跃课堂
    否则返回全局活跃课堂（ID=1）
    """
    if teacher_id:
        query = select(ClassSession).where(
            ClassSession.teacher_id == teacher_id,
            ClassSession.active == True
        )
        return session.exec(query).first()
    return session.get(ClassSession, 1)


def get_class_session_by_class_name(session: Session, class_name: str) -> Optional[ClassSession]:
    """根据班级名称获取活跃课堂"""
    query = select(ClassSession).where(
        ClassSession.class_name == class_name,
        ClassSession.active == True
    )
    return session.exec(query).first()


def start_class(session: Session, class_name: str, teacher_id: int = None, teacher_name: str = None) -> ClassSession:
    """开始上课（支持多教师同时上课）"""
    # 先检查该教师是否已有活跃课堂
    existing = get_class_session(session, teacher_id)
    if existing:
        # 更新现有课堂
        existing.class_name = class_name
        existing.teacher_name = teacher_name
        existing.active = True
        existing.start_time = datetime.now()
        existing.updated_at = datetime.now()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    
    # 创建新课堂记录
    class_session = ClassSession(
        class_name=class_name, 
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        active=True, 
        start_time=datetime.now()
    )
    session.add(class_session)
    session.commit()
    session.refresh(class_session)
    return class_session


def end_class(session: Session, teacher_id: int = None) -> None:
    """结束上课（根据教师ID）"""
    if teacher_id:
        # 查找该教师的活跃课堂
        query = select(ClassSession).where(
            ClassSession.teacher_id == teacher_id,
            ClassSession.active == True
        )
        class_session = session.exec(query).first()
    else:
        # 兼容旧逻辑：结束id=1的课堂
        class_session = session.get(ClassSession, 1)
    
    if class_session:
        class_session.active = False
        class_session.updated_at = datetime.now()
        session.add(class_session)
        session.commit()
        class_session.start_time = None
        session.add(class_session)
        session.commit()


def get_today_checkins(session: Session, class_name: Optional[str] = None, session_start: Optional[datetime] = None) -> List[CheckinRecord]:
    """获取签到列表（支持按课堂开始时间筛选）"""
    from datetime import datetime, time
    
    if session_start:
        # 如果提供了课堂开始时间，只查询该时间之后的签到
        query_start = session_start
    else:
        # 否则查询今日开始
        query_start = datetime.combine(date.today(), time.min)
    
    query = select(CheckinRecord).where(CheckinRecord.checkin_time >= query_start)
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


def has_checked_in_today(session: Session, student_id: str, class_name: str = None, session_start: Optional[datetime] = None) -> bool:
    """检查是否已签到（支持按班级和课堂开始时间检查）"""
    from datetime import datetime, time
    
    if session_start:
        # 如果提供了课堂开始时间，只检查该时间之后的签到
        query_start = session_start
    else:
        # 否则检查今日开始
        query_start = datetime.combine(date.today(), time.min)
    
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
    return session.exec(query).all()
