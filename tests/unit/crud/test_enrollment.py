"""选课成绩 CRUD 测试（TDD）"""
from datetime import date

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.models import (
    Cohort, Class_, Semester, Course, CourseOffering, Enrollment,
    EnrollmentScoreLog, Group, GroupMember, Student, User,
)


def _seed_enrollment(session, score=80.0, version=1):
    """造完整 FK 链：届/班/学期/课程/教学班/学生/选课，返回 enrollment"""
    session.add(Cohort(year="2026"))
    session.add(Semester(
        label="2026-2027-1", start_date=date(2026, 9, 7), total_weeks=20, is_current=True,
    ))
    session.add(Course(code="MATH1", name="高等数学"))
    session.flush()
    cls = Class_(name="一班", cohort_year="2026")
    session.add(cls)
    session.flush()
    sem = session.exec(select(Semester).where(Semester.label == "2026-2027-1")).one()
    course = session.exec(select(Course).where(Course.code == "MATH1")).one()
    session.add(User(username="t1", name="张老师", password_hash="x", role="teacher"))
    session.flush()
    offering = CourseOffering(
        course_id=course.id, semester_id=sem.id, teacher_id=1,
        teacher_name="张老师", class_scope="一班",
    )
    session.add(offering)
    session.flush()
    session.add(Student(student_id="S001", name="学生1", class_name="一班", class_id=cls.id, cohort_year="2026"))
    session.commit()
    enrollment = Enrollment(
        student_id="S001", offering_id=offering.id, semester_id=sem.id,
        status="enrolled", score=score, version=version,
    )
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment


def test_update_enrollment_score(session):
    """个人成绩加分：score/version 更新 + 日志写入"""
    from app.crud.enrollment import update_enrollment_score

    enrollment = _seed_enrollment(session, score=80.0)
    result = update_enrollment_score(session, enrollment.id, delta=5.0, reason="课堂表现", operator="张老师")

    assert result.score == 85.0
    assert result.version == 2
    log = session.exec(select(EnrollmentScoreLog).where(
        EnrollmentScoreLog.enrollment_id == enrollment.id)).one()
    assert log.old_score == 80.0
    assert log.new_score == 85.0
    assert log.delta == 5.0
    assert log.reason == "课堂表现"
    assert log.operator == "张老师"


def test_update_enrollment_score_conflict(session):
    """乐观锁：调用方持有旧版本时 CAS 失败抛 409"""
    from sqlmodel import update
    from app.crud.enrollment import update_enrollment_score

    enrollment = _seed_enrollment(session, score=80.0)
    # 模拟并发：外部已把 version 推到 2，调用方仍持有 version=1
    session.execute(update(Enrollment).where(Enrollment.id == enrollment.id).values(version=2))
    session.commit()

    with pytest.raises(HTTPException) as exc:
        update_enrollment_score(
            session, enrollment.id, delta=5.0, reason="x", operator="x",
            expected_version=1,
        )
    assert exc.value.status_code == 409


def test_update_enrollment_score_not_found(session):
    from app.crud.enrollment import update_enrollment_score

    assert update_enrollment_score(session, 999, delta=1.0, reason="x", operator="x") is None


def test_update_enrollment_score_clamps(session):
    """分数钳制在 [min_score, max_score] 范围内"""
    from app.core.config import get_settings
    from app.crud.enrollment import update_enrollment_score

    settings = get_settings()
    enrollment = _seed_enrollment(session, score=float(settings.score.max_score))
    result = update_enrollment_score(session, enrollment.id, delta=999, reason="x", operator="x")
    assert result.score == float(settings.score.max_score)


def test_set_final_score_individual(session):
    """期末成绩（试卷个人分）：直接赋值"""
    from app.crud.enrollment import set_final_score

    enrollment = _seed_enrollment(session)
    result = set_final_score(session, enrollment.id, final_score=90.0, operator="张老师")
    assert result.final_score == 90.0
    assert result.score == 80.0  # 个人成绩不受影响（期末独立）


def test_set_final_scores_for_group(session):
    """期末成绩（任务小组同分）：组员∩选课名单全部写同分"""
    from app.crud.enrollment import set_final_scores_for_group

    enrollment = _seed_enrollment(session)  # S001 在 offering 1
    s001 = session.get(Student, "S001")

    # 第二个学生 S002 同班同课
    session.add(Student(student_id="S002", name="学生2", class_name="一班",
                        class_id=s001.class_id, cohort_year="2026"))
    session.flush()
    e2 = Enrollment(student_id="S002", offering_id=enrollment.offering_id,
                    semester_id=enrollment.semester_id, status="enrolled", score=70.0)
    session.add(e2)
    # 小组：组员 S001/S002
    offering = session.get(CourseOffering, enrollment.offering_id)
    group = Group(class_id=s001.class_id, name="第一组", leader_student_id="S001",
                  course_id=offering.course_id, semester_id=enrollment.semester_id)
    session.add(group)
    session.flush()
    session.add(GroupMember(group_id=group.id, student_id="S001"))
    session.add(GroupMember(group_id=group.id, student_id="S002"))
    # 非组员选课 S003（不在小组）
    session.add(Student(student_id="S003", name="学生3", class_name="一班",
                        class_id=s001.class_id, cohort_year="2026"))
    session.flush()
    e3 = Enrollment(student_id="S003", offering_id=enrollment.offering_id,
                    semester_id=enrollment.semester_id, status="enrolled", score=60.0)
    session.add(e3)
    session.commit()

    affected = set_final_scores_for_group(
        session, offering_id=enrollment.offering_id, group_id=group.id,
        final_score=88.0, operator="张老师",
    )
    assert affected == 2  # 组员∩选课 = S001/S002

    session.refresh(enrollment)
    session.refresh(e2)
    session.refresh(e3)
    assert enrollment.final_score == 88.0
    assert e2.final_score == 88.0
    assert e3.final_score is None  # 非组员不受影响


def test_get_student_enrollments(session):
    """我的成绩：返回选课列表（课程名/教师名/范围/score/final_score）"""
    from app.crud.enrollment import get_student_enrollments

    _seed_enrollment(session)
    rows = get_student_enrollments(session, "S001", session.exec(
        select(Semester).where(Semester.label == "2026-2027-1")).one().id)
    assert len(rows) == 1
    assert rows[0]["course_name"] == "高等数学"
    assert rows[0]["teacher_name"] == "张老师"
    assert rows[0]["class_scope"] == "一班"
    assert rows[0]["score"] == 80.0
    assert rows[0]["final_score"] is None
    assert rows[0]["status"] == "enrolled"
