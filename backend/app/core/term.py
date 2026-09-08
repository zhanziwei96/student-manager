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

from app.core.config import get_settings
from app.core.timezone import get_now

# 进程级当前学期缓存（60 秒 TTL；invalidate 供学期切换后清除）
_current_semester_cache = None  # type: Optional[Semester]
_current_semester_ts: float = 0.0
_CACHE_TTL = 60.0


def get_current_semester(session: Session):
    """从数据库读当前学期（is_current=true，进程级 TTL 缓存）"""
    global _current_semester_cache, _current_semester_ts
    now = time.time()
    if _current_semester_cache is not None and (now - _current_semester_ts) < _CACHE_TTL:
        return _current_semester_cache
    from app.models import Semester
    sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).first()
    if sem is not None:
        _current_semester_cache = sem
        _current_semester_ts = now
    return sem


def get_current_semester_id(session: Session) -> Optional[int]:
    """当前学期 ID（无当前学期行时返回 None）"""
    sem = get_current_semester(session)
    return sem.id if sem else None


def invalidate_semester_cache() -> None:
    """清除当前学期缓存（学期切换后调用）"""
    global _current_semester_cache, _current_semester_ts
    _current_semester_cache = None
    _current_semester_ts = 0.0


def get_current_term() -> str:
    """获取当前学期标识（如 '2026-2027-1'）

    优先返回 DB 缓存的当前学期 label；缓存未加载（模型 default_factory 等
    无 session 场景）时 fallback 配置值。"""
    if _current_semester_cache is not None:
        return _current_semester_cache.label
    return get_settings().term.label


def get_term_start_date() -> date:
    """获取当前学期开始日期（第 1 周周一）"""
    return get_settings().term.start_date


def get_term_total_weeks() -> int:
    """获取当前学期总周数"""
    return get_settings().term.total_weeks


def get_current_week_number(
    today: Optional[date] = None,
    total_weeks: Optional[int] = None,
) -> int:
    """计算当前教学周次。

    以学期开始日期（周一）为基准：
    - 开学前返回 0（前端显示"未开学"）
    - 学期中返回 1..total_weeks
    - 超过总周数返回 total_weeks

    Args:
        today: 指定日期（测试用），默认今天
        total_weeks: 周数上限，默认取配置 TERM_CFG__TOTAL_WEEKS
    """
    if today is None:
        today = get_now().date()
    if total_weeks is None:
        total_weeks = get_term_total_weeks()

    start = get_term_start_date()
    if today < start:
        return 0

    days_since_start = (today - start).days
    week = days_since_start // 7 + 1
    return min(week, total_weeks)


def get_week_number_for_date(target_date: date) -> int:
    """计算指定日期所在的教学周次（开学前返回 0）"""
    return get_current_week_number(today=target_date)
