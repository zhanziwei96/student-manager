"""学期上下文工具测试 - 周次计算（semesters 表单一真源）"""
from datetime import date, timedelta

from app.models import Semester
from app.core.term import (
    get_current_term,
    get_current_semester,
    get_current_week_number,
    get_week_number_for_date,
    invalidate_semester_cache,
)


def _seed_semester(session, start=date(2026, 9, 7), total_weeks=20):
    sem = Semester(label="2026-2027-1", start_date=start,
                   total_weeks=total_weeks, is_current=True)
    session.add(sem)
    session.commit()
    invalidate_semester_cache()
    get_current_semester(session)  # 填充进程缓存（get_current_term 依赖）
    return sem


def test_get_current_term(session):
    _seed_semester(session)
    assert get_current_term() == "2026-2027-1"


def test_week_before_term_start_returns_0(session):
    """开学前返回 0（前端显示未开学）"""
    sem = _seed_semester(session)
    assert get_current_week_number(session, today=sem.start_date - timedelta(days=3)) == 0


def test_week_first_week_boundaries(session):
    """第 1 周：周一到周日"""
    sem = _seed_semester(session)
    assert get_current_week_number(session, today=sem.start_date) == 1
    assert get_current_week_number(session, today=sem.start_date + timedelta(days=6)) == 1


def test_week_second_week(session):
    sem = _seed_semester(session)
    assert get_current_week_number(session, today=sem.start_date + timedelta(days=7)) == 2


def test_week_number_for_date(session):
    sem = _seed_semester(session)
    assert get_week_number_for_date(session, sem.start_date + timedelta(days=14)) == 3


def test_week_clamped_to_total_weeks(session):
    sem = _seed_semester(session)
    assert get_current_week_number(session, today=sem.start_date + timedelta(days=400)) == 20


def test_no_current_semester_returns_0(session):
    """无当前学期时周次返回 0"""
    assert get_current_week_number(session) == 0
