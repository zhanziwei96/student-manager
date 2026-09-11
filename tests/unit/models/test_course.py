"""课程线模型测试"""
from sqlmodel import Session, select

from app.models import (
    Course, CourseCreate, CourseResponse,
    CourseOffering, CourseOfferingCreate, CourseOfferingResponse,
    CourseOfferingClass,
    Enrollment, EnrollmentResponse,
)


class TestCourseModel:
    def test_course_creation(self):
        c = Course(code="MATH1001", name="高等数学A", department="数学系")
        assert c.code == "MATH1001"
        assert c.name == "高等数学A"
        assert c.department == "数学系"

    def test_course_default_values(self):
        c = Course(code="MATH1001", name="高等数学A")
        assert c.department == ""
        assert c.status == "active"


class TestCourseSchemas:
    def test_course_create(self):
        req = CourseCreate(code="MATH1001", name="高等数学A", department="数学系")
        assert req.code == "MATH1001"

    def test_course_response(self):
        resp = CourseResponse(id=1, code="MATH1001", name="高等数学A", department="数学系", status="active")
        assert resp.id == 1


class TestCourseOfferingModel:
    def test_offering_creation(self):
        o = CourseOffering(
            course_id=1, semester_id=1, teacher_id=2, teacher_name="张老师",
            capacity=60,
        )
        assert o.course_id == 1
        assert o.capacity == 60

    def test_offering_default_values(self):
        o = CourseOffering(course_id=1, semester_id=1)
        assert o.teacher_id is None  # 可空：先排课后定教师
        assert o.teacher_name == ""
        assert o.capacity is None
        assert o.status == "active"


class TestCourseOfferingSchemas:
    def test_offering_create(self):
        req = CourseOfferingCreate(course_id=1, semester_id=1, teacher_id=2)
        assert req.teacher_name == ""

    def test_offering_response(self):
        resp = CourseOfferingResponse(
            id=1, course_id=1, semester_id=1, teacher_id=2, teacher_name="张老师",
            class_scope="计科1班", capacity=None, status="active",
        )
        assert resp.id == 1

    def test_offering_response_class_scope_default(self):
        # class_scope 为响应字段（Task 7 由关联表拼装），默认空串
        resp = CourseOfferingResponse(
            id=1, course_id=1, semester_id=1, teacher_id=2, teacher_name="张老师",
            capacity=None, status="active",
        )
        assert resp.class_scope == ""


class TestCourseOfferingClassModel:
    """course_offering_classes 关联表（Phase 6 Task 3：替代 class_scope 自由文本）"""

    def test_creation(self):
        link = CourseOfferingClass(offering_id=1, class_id=2)
        assert link.offering_id == 1
        assert link.class_id == 2

    def test_link_and_query(self, session: Session, seed_refs):
        """教学班关联两个班级后可按 offering_id 查询"""
        course = Course(code="TEST1001", name="测试课程")
        session.add(course)
        session.commit()
        session.refresh(course)

        offering = CourseOffering(course_id=course.id, semester_id=seed_refs["semester_id"])
        session.add(offering)
        session.commit()
        session.refresh(offering)

        session.add_all([
            CourseOfferingClass(offering_id=offering.id, class_id=seed_refs["一班"]),
            CourseOfferingClass(offering_id=offering.id, class_id=seed_refs["二班"]),
        ])
        session.commit()

        links = session.exec(
            select(CourseOfferingClass).where(CourseOfferingClass.offering_id == offering.id)
        ).all()
        assert {link.class_id for link in links} == {seed_refs["一班"], seed_refs["二班"]}


class TestEnrollmentModel:
    def test_enrollment_creation(self):
        e = Enrollment(student_id="S001", offering_id=1, semester_id=1)
        assert e.student_id == "S001"
        assert e.offering_id == 1

    def test_enrollment_default_values(self):
        e = Enrollment(student_id="S001", offering_id=1, semester_id=1)
        assert e.status == "enrolled"
        assert e.score == 0.0
        assert e.final_score is None  # 期末成绩独立，可空
        assert e.version == 1


class TestEnrollmentSchemas:
    def test_enrollment_response(self):
        resp = EnrollmentResponse(
            id=1, student_id="S001", offering_id=1, semester_id=1,
            status="enrolled", score=85.0, final_score=90.0, version=2,
        )
        assert resp.id == 1
        assert resp.final_score == 90.0
        assert resp.version == 2
