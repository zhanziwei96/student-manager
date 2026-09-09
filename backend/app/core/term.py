"""
学期上下文工具 - 单一真源

第二学期引入：集中管理学期标识与教学周次计算，
替代此前散落在 schedules.py / course_sessions.py / 前端 date.ts
中互相矛盾的硬编码周次实现。

Phase 2：学期实体化 — get_current_semester 从数据库读（进程级 TTL 缓存），
get_current_term 保持兼容（模型 default_factory 无 session 场景）。
"""
import time
from datetime import date
from typing import Optional

from sqlmodel import Session, select

from app.core.timezone import get_now

# 进程级当前学期缓存（60 秒 TTL；invalidate 供学期切换后清除）。
# 只缓存简单值（id/label），ORM 对象按 session 现取——避免 detached 对象
# 跨 session 生命周期问题（如模型 default_factory 实例化场景）。
_current_semester_id: Optional[int] = None
_current_semester_label: Optional[str] = None
_current_semester_ts: float = 0.0
_CACHE_TTL = 60.0


def get_current_semester(session: Session):
    """从数据库读当前学期（is_current=true，进程级 TTL 缓存）"""
    global _current_semester_id, _current_semester_label, _current_semester_ts
    from app.models import Semester

    now = time.time()
    if _current_semester_id is not None and (now - _current_semester_ts) < _CACHE_TTL:
        return session.get(Semester, _current_semester_id)
    sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).first()
    if sem is not None:
        _current_semester_id = sem.id
        _current_semester_label = sem.label
        _current_semester_ts = now
    return sem


def get_current_semester_id(session: Session) -> Optional[int]:
    """当前学期 ID（无当前学期行时返回 None）"""
    sem = get_current_semester(session)
    return sem.id if sem else None


def invalidate_semester_cache() -> None:
    """清除当前学期缓存（学期切换后调用）"""
    global _current_semester_id, _current_semester_label, _current_semester_ts
    _current_semester_id = None
    _current_semester_label = None
    _current_semester_ts = 0.0


def get_current_term() -> str:
    """获取当前学期标识（如 '2026-2027-1'）

    返回 DB 缓存的当前学期 label；缓存未加载（模型 default_factory 无
    session 场景）时返回空串（冗余 semester 列，过渡期保留）。"""
    return _current_semester_label or ""


def get_current_week_number(
    session: Session,
    today: Optional[date] = None,
    total_weeks: Optional[int] = None,
) -> int:
    """计算当前教学周次（从 semesters 表读当前学期）。

    以学期开始日期（周一）为基准：
    - 无当前学期或开学前返回 0（前端显示"未开学"）
    - 学期中返回 1..total_weeks
    - 超过总周数返回 total_weeks

    Args:
        session: 数据库会话
        today: 指定日期（测试用），默认今天
        total_weeks: 周数上限，默认取当前学期 total_weeks
    """
    sem = get_current_semester(session)
    if sem is None:
        return 0
    if today is None:
        today = get_now().date()
    if total_weeks is None:
        total_weeks = sem.total_weeks

    if today < sem.start_date:
        return 0

    days_since_start = (today - sem.start_date).days
    week = days_since_start // 7 + 1
    return min(week, total_weeks)


def get_week_number_for_date(session: Session, target_date: date) -> int:
    """计算指定日期所在的教学周次（开学前返回 0）"""
    return get_current_week_number(session, today=target_date)
