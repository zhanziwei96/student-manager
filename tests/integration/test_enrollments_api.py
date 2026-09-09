"""选课成绩 API 集成测试"""
from datetime import date

import pytest
from sqlmodel import Session, select

from app.models import (
    Cohort, Class_, Semester, Course, CourseOffering, Enrollment,
    Group, GroupMember, Student, User,
)


@pytest.fixture
def enrollment_chain(session, teacher_user, student_user):
    """造完整 FK 链：届/班/学期/课程/教学班（teacher_user 授课）/选课，
    返回 (enrollment, offering)——学生复用 student_user（S001），教师为登录教师"""
    session.add(Cohort(year="2026"))
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                         total_weeks=20, is_current=True))
    session.add(Course(code="MATH1", name="高等数学"))
    session.flush()
    cls = Class_(name="一班", cohort_year="2026")
    session.add(cls)
    session.flush()
    offering = CourseOffering(
        course_id=session.exec(select(Course).where(Course.code == "MATH1")).one().id,
        semester_id=session.exec(select(Semester).where(Semester.label == "2026-2027-1")).one().id,
        teacher_id=teacher_user.id, teacher_name=teacher_user.name, class_scope="一班",
    )
    session.add(offering)
    session.flush()
    enrollment = Enrollment(
        student_id=student_user.student_id, offering_id=offering.id,
        semester_id=offering.semester_id, status="enrolled", score=80.0,
    )
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment, offering


def test_student_views_own_enrollments(student_client, enrollment_chain):
    """学生查看自己的成绩"""
    enrollment, _ = enrollment_chain
    resp = student_client.get("/api/v1/students/S001/enrollments")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["course_id"] is not None
    assert data[0]["course_name"] == "高等数学"
    assert data[0]["score"] == 80.0
    assert data[0]["final_score"] is None


def test_teacher_updates_enrollment_score(teacher_client, enrollment_chain, session):
    """授课教师给教学班学生加减分"""
    enrollment, _ = enrollment_chain
    resp = teacher_client.put(
        f"/api/v1/enrollments/{enrollment.id}/score",
        json={"score_change": 5, "reason": "课堂表现"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["score"] == 85.0

    # 乐观锁 version 已推进（expire 后重新加载，避免 identity map 旧对象）
    from app.models import Enrollment
    session.expire_all()
    fresh = session.get(Enrollment, enrollment.id)
    assert fresh.version == 2


def test_teacher_sets_final_score_individual(teacher_client, enrollment_chain):
    """期末成绩（试卷个人分）"""
    enrollment, _ = enrollment_chain
    resp = teacher_client.put(
        f"/api/v1/enrollments/{enrollment.id}/final-score",
        json={"final_score": 92.0},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["final_score"] == 92.0


def test_teacher_sets_group_final_scores(teacher_client, enrollment_chain, session):
    """期末成绩（任务小组同分）"""
    enrollment, offering = enrollment_chain
    cls_id = session.exec(select(Class_).where(Class_.name == "一班")).one().id
    session.add(Student(student_id="S002", name="学生2", class_name="一班",
                        class_id=cls_id, cohort_year="2026"))
    session.flush()
    e2 = Enrollment(student_id="S002", offering_id=offering.id,
                    semester_id=offering.semester_id, status="enrolled", score=70.0)
    session.add(e2)
    group = Group(class_name="一班", name="第一组", leader_student_id="S001",
                  course_id=offering.course_id, semester_id=offering.semester_id)
    session.add(group)
    session.flush()
    session.add(GroupMember(group_id=group.id, student_id="S001"))
    session.add(GroupMember(group_id=group.id, student_id="S002"))
    session.commit()

    resp = teacher_client.put(
        f"/api/v1/offerings/{offering.id}/final-scores/group",
        json={"group_id": group.id, "final_score": 88.0},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["affected"] == 2

    session.refresh(enrollment)
    session.refresh(e2)
    assert enrollment.final_score == 88.0
    assert e2.final_score == 88.0
