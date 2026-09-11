"""verify_teacher_class_access 测试（权限唯一真源：course_offering_classes 关联表）"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.api.deps import verify_teacher_class_access


def _teacher_with_offerings(session, class_names: list[str]):
    """创建教师、班级及授课教学班（course_offering_classes 关联派生可访问班级）

    返回 (teacher, classes)：classes 与 class_names 一一对应。
    """
    from app.models import (
        Class_, Course, CourseOffering, CourseOfferingClass, Semester, User,
    )
    from app.core.security import hash_password

    teacher = User(username="t1", name="教师1", role="teacher",
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                   total_weeks=20, is_current=True)
    course = Course(code="MATH1", name="高等数学")
    classes = [Class_(name=n, cohort_year="2026") for n in class_names]
    session.add(teacher)
    session.add(sem)
    session.add(course)
    session.add_all(classes)
    session.commit()
    offering = CourseOffering(
        course_id=course.id, semester_id=sem.id, teacher_id=teacher.id,
        teacher_name=teacher.name, status="active",
    )
    session.add(offering)
    session.commit()
    session.add_all([
        CourseOfferingClass(offering_id=offering.id, class_id=c.id)
        for c in classes
    ])
    session.commit()
    return teacher, classes


def test_admin_always_allowed(session):
    user = {"sub": "1", "role": "admin", "is_admin": True}
    # admin 不抛异常即为通过
    verify_teacher_class_access(user, 1, session)


def test_teacher_allowed_for_offering_class(session):
    teacher, classes = _teacher_with_offerings(session, ["1班", "2班"])
    user = {"sub": str(teacher.id), "role": "teacher"}
    verify_teacher_class_access(user, classes[0].id, session)


def test_teacher_denied_for_unassigned_class(session):
    from app.models import Class_
    teacher, _ = _teacher_with_offerings(session, ["1班"])
    other = Class_(name="2班", cohort_year="2026")
    session.add(other)
    session.commit()
    user = {"sub": str(teacher.id), "role": "teacher"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, other.id, session)
    assert exc_info.value.status_code == 403


def test_teacher_wildcard_when_no_association_rows(session):
    """offering 无关联行 = 面向全部班级（通配，Phase 6 决策过渡期语义）"""
    from app.models import Course, CourseOffering, Semester, User
    from app.core.security import hash_password

    teacher = User(username="t3", name="教师3", role="teacher",
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                   total_weeks=20, is_current=True)
    course = Course(code="ENG1", name="大学英语")
    session.add(teacher)
    session.add(sem)
    session.add(course)
    session.commit()
    session.add(CourseOffering(
        course_id=course.id, semester_id=sem.id, teacher_id=teacher.id,
        teacher_name=teacher.name, status="active",
    ))
    session.commit()
    user = {"sub": str(teacher.id), "role": "teacher"}
    # 任意 class_id 均放行（不抛异常即为通过）
    verify_teacher_class_access(user, 999, session)


def test_teacher_without_offerings_denied(session):
    from app.models import User
    from app.core.security import hash_password
    teacher = User(username="t2", name="教师2", role="teacher",
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    session.add(teacher)
    session.commit()
    user = {"sub": str(teacher.id), "role": "teacher"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, 1, session)
    assert exc_info.value.status_code == 403


def test_student_denied(session):
    user = {"sub": "S001", "role": "student"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, 1, session)
    assert exc_info.value.status_code == 403
