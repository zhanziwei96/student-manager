"""学生-班级-学期归属桥接表模型测试"""
from app.models import StudentClassSemester, StudentClassSemesterResponse


class TestStudentClassSemesterModel:
    def test_creation(self):
        scs = StudentClassSemester(student_id="S001", class_id=1, semester_id=1)
        assert scs.student_id == "S001"
        assert scs.class_id == 1
        assert scs.semester_id == 1


class TestStudentClassSemesterSchemas:
    def test_response(self):
        resp = StudentClassSemesterResponse(
            id=1, student_id="S001", class_id=1, semester_id=1,
        )
        assert resp.id == 1
        assert resp.student_id == "S001"
