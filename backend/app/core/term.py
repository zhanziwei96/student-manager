"""
学期上下文工具 - 单一真源

第二学期引入：集中管理学期标识与教学周次计算，
替代此前散落在 schedules.py / course_sessions.py / 前端 date.ts
中互相矛盾的硬编码周次实现。
"""
from datetime import date
from typing import Optional

from app.core.config import get_settings
from app.core.timezone import get_now


def get_current_term() -> str:
    """获取当前学期标识（如 '2026-2027-1'）"""
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
