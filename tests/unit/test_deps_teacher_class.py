"""verify_teacher_class_access 测试（授课关系唯一真源：course_offerings）"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.api.deps import verify_teacher_class_access


def _teacher_with_offerings(session, class_scope: str):
    """创建教师及其授课教学班（class_scope 派生可访问班级）"""
    from app.models import Course, CourseOffering, Semester, User
    from app.core.security import hash_password

    teacher = User(username="t1", name="教师1", role="teacher",
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                   total_weeks=20, is_current=True)
    course = Course(code="MATH1", name="高等数学")
    session.add(teacher)
    session.add(sem)
    session.add(course)
    session.commit()
    session.add(CourseOffering(
        course_id=course.id, semester_id=sem.id, teacher_id=teacher.id,
        teacher_name=teacher.name, class_scope=class_scope, status="active",
    ))
    session.commit()
    return teacher


def test_admin_always_allowed(session):
    user = {"sub": "1", "role": "admin", "is_admin": True}
    # admin 不抛异常即为通过
    verify_teacher_class_access(user, "1班", session)


def test_teacher_allowed_for_offering_class(session):
    teacher = _teacher_with_offerings(session, "1班,2班")
    user = {"sub": str(teacher.id), "role": "teacher"}
    verify_teacher_class_access(user, "1班", session)


def test_teacher_denied_for_unassigned_class(session):
    teacher = _teacher_with_offerings(session, "1班")
    user = {"sub": str(teacher.id), "role": "teacher"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, "2班", session)
    assert exc_info.value.status_code == 403


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
        verify_teacher_class_access(user, "1班", session)
    assert exc_info.value.status_code == 403


def test_student_denied(session):
    user = {"sub": "S001", "role": "student"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, "1班", session)
    assert exc_info.value.status_code == 403
