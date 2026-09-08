"""届模型测试"""
from app.models import Cohort, CohortCreate, CohortResponse


class TestCohortModel:
    def test_cohort_creation(self):
        c = Cohort(year="2026", label="2026届", entry_semester_id=1)
        assert c.year == "2026"
        assert c.label == "2026届"
        assert c.entry_semester_id == 1

    def test_cohort_default_values(self):
        c = Cohort(year="2026")
        assert c.label == ""
        assert c.status == "active"
        assert c.entry_semester_id is None


class TestCohortSchemas:
    def test_cohort_create(self):
        req = CohortCreate(year="2026", label="2026届")
        assert req.year == "2026"
        assert req.label == "2026届"

    def test_cohort_response(self):
        resp = CohortResponse(year="2026", label="2026届", status="active", entry_semester_id=1)
        assert resp.year == "2026"
        assert resp.entry_semester_id == 1
