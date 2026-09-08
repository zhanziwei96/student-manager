"""学期模型测试"""
from datetime import date

from app.models import Semester, SemesterCreate, SemesterResponse


class TestSemesterModel:
    def test_semester_creation(self):
        sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 1), total_weeks=20)
        assert sem.label == "2026-2027-1"
        assert sem.start_date == date(2026, 9, 1)
        assert sem.total_weeks == 20

    def test_semester_default_values(self):
        sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 1), total_weeks=20)
        assert sem.is_current is False
        assert sem.status == "active"


class TestSemesterSchemas:
    def test_semester_create(self):
        req = SemesterCreate(label="2026-2027-1", start_date=date(2026, 9, 1), total_weeks=20)
        assert req.label == "2026-2027-1"
        assert req.total_weeks == 20

    def test_semester_response(self):
        resp = SemesterResponse(
            id=1, label="2026-2027-1", start_date=date(2026, 9, 1),
            total_weeks=20, is_current=True, status="active",
        )
        assert resp.id == 1
        assert resp.is_current is True
