"""
签到相关 CRUD 操作
"""
from datetime import datetime, date
from typing import List, Optional
from sqlmodel import Session, select, func
from app.models import CheckinRecord
from app.core.class_cache import get_class_ids_by_names
from app.core.term import get_current_semester_id
from app.core.timezone import get_now


def get_checkins_by_session_id(session: Session, session_id: int) -> List[CheckinRecord]:
    """获取指定课堂会话的所有签到记录"""
    query = select(CheckinRecord).where(CheckinRecord.session_id == session_id)
    return list(session.exec(query).all())


def get_all_checkins(
    session: Session,
    limit: int = 200,
    class_ids: Optional[List[int]] = None,
) -> List[CheckinRecord]:
    """获取当前学期签到记录列表（按时间倒序，用于 admin 签到管理；可选按班级过滤）"""
    query = select(CheckinRecord).where(CheckinRecord.semester_id == get_current_semester_id(session))
    # 注意：用 is not None 而非 truthiness——空列表应过滤掉全部（fail-closed），
    # 而不是跳过过滤（否则无班级教师会看到全量记录）
    if class_ids is not None:
        query = query.where(CheckinRecord.class_id.in_(class_ids))
    query = query.order_by(CheckinRecord.checkin_time.desc()).limit(limit)
    return list(session.exec(query).all())


def get_today_checkins(
    session: Session, class_name: Optional[str] = None, session_start: Optional[datetime] = None
) -> List[CheckinRecord]:
    """获取签到列表（支持按课堂开始时间筛选）"""
    from datetime import time

    if session_start:
        query_start = session_start
    else:
        query_start = datetime.combine(date.today(), time.min).replace(tzinfo=get_now().tzinfo)

    query = select(CheckinRecord).where(
        CheckinRecord.checkin_time >= query_start,
        CheckinRecord.semester_id == get_current_semester_id(session),
    )
    if class_name:
        query = query.where(CheckinRecord.class_id.in_(get_class_ids_by_names(session, [class_name])))
    return list(session.exec(query).all())


def count_today_checkins(session: Session, class_name: Optional[str] = None) -> int:
    """使用 SQL COUNT 计算今日签到数（性能优化）"""
    from datetime import time

    today_start = datetime.combine(date.today(), time.min)

    query = select(func.count()).select_from(CheckinRecord).where(
        CheckinRecord.checkin_time >= today_start,
        CheckinRecord.semester_id == get_current_semester_id(session),
    )
    if class_name:
        query = query.where(CheckinRecord.class_id.in_(get_class_ids_by_names(session, [class_name])))

    result = session.exec(query)
    return result.one()


class DuplicateCheckinError(Exception):
    """重复签到异常"""
    pass


def create_checkin(
    session: Session, student_id: str, student_name: str,
    class_id: Optional[int], session_id: int, checkin_type: Optional[str] = None,
    device_id: Optional[str] = None, device_info: Optional[str] = None,
    qr_signature: Optional[str] = None, device_bound: bool = False
) -> CheckinRecord:
    """创建签到记录（在同一事务内完成重复检查与插入）"""
    from sqlalchemy.exc import IntegrityError
    from app.models.constants import CheckinTypeConst
    if checkin_type is None:
        checkin_type = CheckinTypeConst.SELF

    # 事务内重复检查，缩小竞态窗口
    if has_checked_in_session(session, student_id, session_id):
        raise DuplicateCheckinError("您已在本课堂签到")

    # 注：设备级代签防护已迁移到 DeviceBind 表（按学生维度隔离）
    # 不再使用全局设备检查，避免学生合法更换设备时被误拦截

    checkin = CheckinRecord(
        session_id=session_id,
        student_id=student_id,
        student_name=student_name,
        class_id=class_id,
        semester_id=get_current_semester_id(session),
        checkin_type=checkin_type,
        device_id=device_id,
        device_info=device_info,
        qr_signature=qr_signature,
        device_bound=device_bound
    )
    session.add(checkin)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise DuplicateCheckinError("您已在本课堂签到")
    session.refresh(checkin)
    return checkin


def has_checked_in_session(session: Session, student_id: str, session_id: int) -> bool:
    """检查学生是否已在指定课堂签到"""
    query = select(CheckinRecord).where(
        CheckinRecord.student_id == student_id,
        CheckinRecord.session_id == session_id
    )
    return session.exec(query).first() is not None


def has_checked_in_today(
    session: Session, student_id: str, class_name: Optional[str] = None,
    session_start: Optional[datetime] = None
) -> bool:
    """检查是否已签到（支持按班级和课堂开始时间检查）- 兼容旧逻辑"""
    from datetime import time

    if session_start:
        query_start = session_start
    else:
        query_start = datetime.combine(date.today(), time.min).replace(tzinfo=get_now().tzinfo)

    query = select(CheckinRecord).where(
        CheckinRecord.student_id == student_id,
        CheckinRecord.checkin_time >= query_start
    )
    if class_name:
        query = query.where(CheckinRecord.class_id.in_(get_class_ids_by_names(session, [class_name])))
    return session.exec(query).first() is not None


def count_checkins_by_session_id(session: Session, session_id: int) -> int:
    """统计指定课堂会话的签到数量"""
    query = select(func.count()).select_from(CheckinRecord).where(
        CheckinRecord.session_id == session_id
    )
    result = session.exec(query)
    return result.one()


def is_device_checked_in_session(session: Session, device_id: str, session_id: int) -> bool:
    """检查设备是否已在指定课堂签到过"""
    if not device_id:
        return False
    query = select(CheckinRecord).where(
        CheckinRecord.device_id == device_id,
        CheckinRecord.session_id == session_id
    )
    return session.exec(query).first() is not None
