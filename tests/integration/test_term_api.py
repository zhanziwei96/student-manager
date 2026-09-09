"""term API 集成测试"""
from datetime import date
from sqlmodel import select
from sqlmodel import Session
from app.models import Semester
from app.core.term import invalidate_semester_cache


def _seed_current_semester(test_engine):
    with Session(test_engine) as session:
        if session.exec(select(Semester).where(Semester.is_current.is_(True))).first() is None:
            session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                                 total_weeks=20, is_current=True))
            session.commit()
    invalidate_semester_cache()


def test_get_current_term_info(client, test_engine):
    """返回当前学期标识、开始日期、当前周次、总周数"""
    _seed_current_semester(test_engine)
    resp = client.get("/api/v1/term/current")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["term"] == "2026-2027-1"
    assert data["start_date"] == "2026-09-07"
    assert data["total_weeks"] == 20
    # current_week: 0..total_weeks 范围内（取决于运行当天，不再要求具体值）
    assert 0 <= data["current_week"] <= 20
