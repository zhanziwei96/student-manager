"""班级模型测试"""
from app.models import Class_, ClassCreate, ClassResponse


class TestClassModel:
    def test_class_creation(self):
        cls = Class_(name="1班", major="计算机", cohort_year="2026")
        assert cls.name == "1班"
        assert cls.major == "计算机"
        assert cls.cohort_year == "2026"

    def test_class_default_values(self):
        cls = Class_(name="1班", cohort_year="2026")
        assert cls.major == ""
        assert cls.id is None


class TestClassSchemas:
    def test_class_create(self):
        req = ClassCreate(name="1班", major="计算机", cohort_year="2026")
        assert req.name == "1班"

    def test_class_response(self):
        resp = ClassResponse(id=1, name="1班", major="计算机", cohort_year="2026", display_name="2026届1班")
        assert resp.id == 1
        assert resp.display_name == "2026届1班"
