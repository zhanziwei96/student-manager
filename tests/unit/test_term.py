"""学期上下文工具测试 - 周次计算单一真源"""
from datetime import date
from app.core.term import (
    get_current_term,
    get_term_start_date,
    get_term_total_weeks,
    get_current_week_number,
    get_week_number_for_date,
)


def test_get_current_term():
    assert get_current_term() == "2026-2027-1"


def test_get_term_start_date():
    assert get_term_start_date() == date(2026, 9, 7)


def test_get_term_total_weeks():
    assert get_term_total_weeks() == 20


def test_week_before_term_start_returns_0():
    """开学前返回 0（前端显示未开学）"""
    assert get_current_week_number(today=date(2026, 9, 4)) == 0


def test_week_first_week_boundaries():
    """第 1 周：周一到周日"""
    assert get_current_week_number(today=date(2026, 9, 7)) == 1
    assert get_current_week_number(today=date(2026, 9, 13)) == 1


def test_week_second_week():
    assert get_current_week_number(today=date(2026, 9, 14)) == 2


def test_week_caps_at_total_weeks():
    """超过总周数返回总周数（学期末不会无限增长）"""
    assert get_current_week_number(today=date(2027, 1, 25)) == 20


def test_get_week_number_for_date_before_term():
    """指定日期周次计算：开学前返回 0"""
    assert get_week_number_for_date(date(2026, 9, 5)) == 0


def test_get_week_number_for_date_during_term():
    assert get_week_number_for_date(date(2026, 9, 21)) == 3
