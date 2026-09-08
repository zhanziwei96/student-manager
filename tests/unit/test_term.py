"""学期上下文工具测试 - 周次计算单一真源"""
from datetime import date, timedelta

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
    start = get_term_start_date()
    assert get_current_week_number(today=start - timedelta(days=3)) == 0


def test_week_first_week_boundaries():
    """第 1 周：周一到周日"""
    start = get_term_start_date()
    assert get_current_week_number(today=start) == 1
    assert get_current_week_number(today=start + timedelta(days=6)) == 1


def test_week_second_week():
    start = get_term_start_date()
    assert get_current_week_number(today=start + timedelta(days=7)) == 2


def test_week_total_weeks_natural_value():
    """第 total_weeks 周自然值（周一与周日均不被封顶逻辑掩盖）"""
    start = get_term_start_date()
    total = get_term_total_weeks()
    last_week_monday = start + timedelta(weeks=total - 1)
    assert get_current_week_number(today=last_week_monday) == total
    assert get_current_week_number(today=last_week_monday + timedelta(days=6)) == total


def test_week_caps_at_total_weeks():
    """超过总周数返回总周数（学期末不会无限增长）"""
    start = get_term_start_date()
    total = get_term_total_weeks()
    assert get_current_week_number(today=start + timedelta(weeks=total)) == total


def test_get_current_week_number_with_custom_total_weeks():
    """注入 total_weeks 参数可覆盖配置上限"""
    start = get_term_start_date()
    assert get_current_week_number(
        today=start + timedelta(days=365), total_weeks=3
    ) == 3


def test_get_week_number_for_date_before_term():
    """指定日期周次计算：开学前返回 0"""
    start = get_term_start_date()
    assert get_week_number_for_date(start - timedelta(days=2)) == 0


def test_get_week_number_for_date_during_term():
    start = get_term_start_date()
    assert get_week_number_for_date(start + timedelta(days=14)) == 3


# ============ 数据库化测试（Phase 2a） ============

def test_get_current_semester_reads_db(session):
    """get_current_semester 从数据库读 is_current 行"""
    from app.core.term import get_current_semester, invalidate_semester_cache
    from app.models import Semester

    invalidate_semester_cache()
    sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7), total_weeks=20, is_current=True)
    session.add(sem)
    session.commit()

    result = get_current_semester(session)
    assert result is not None
    assert result.label == "2026-2027-1"
    assert result.is_current is True


def test_get_current_semester_id(session):
    from app.core.term import get_current_semester_id, invalidate_semester_cache
    from app.models import Semester

    invalidate_semester_cache()
    sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7), total_weeks=20, is_current=True)
    session.add(sem)
    session.commit()

    assert get_current_semester_id(session) == sem.id


def test_get_current_term_falls_back_to_config():
    """缓存失效且无 DB 行时 fallback 配置 label（模型 default_factory 场景）"""
    from app.core.term import get_current_term, invalidate_semester_cache

    invalidate_semester_cache()
    assert get_current_term() == "2026-2027-1"


def test_semester_cache_invalidate(session):
    """缓存命中后改 DB 仍返回旧值；invalidate 后返回新值"""
    from app.core.term import (
        get_current_semester, get_current_semester_id,
        invalidate_semester_cache,
    )
    from app.models import Semester
    from sqlmodel import update

    invalidate_semester_cache()
    sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7), total_weeks=20, is_current=True)
    session.add(sem)
    session.commit()

    assert get_current_semester_id(session) == sem.id

    # 切到新学期并 invalidate
    new_sem = Semester(label="2026-2027-2", start_date=date(2027, 2, 22), total_weeks=20, is_current=True)
    session.add(new_sem)
    session.execute(update(Semester).where(Semester.id == sem.id).values(is_current=False))
    session.commit()
    session.refresh(new_sem)

    invalidate_semester_cache()
    assert get_current_semester_id(session) == new_sem.id
