"""verify_teacher_class_access 测试"""
from datetime import date

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.api.deps import verify_teacher_class_access


def test_admin_always_allowed(session):
    user = {"sub": "1", "role": "admin", "is_admin": True}
    # admin 不抛异常即为通过
    verify_teacher_class_access(user, "1班", session)


def test_teacher_allowed_for_assigned_class(session):
    from app.models import User
    from app.core.security import hash_password
    teacher = User(username="t1", name="教师1", role="teacher",
                   assigned_classes='["1班", "2班"]',
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    session.add(teacher)
    session.commit()
    user = {"sub": str(teacher.id), "role": "teacher"}
    verify_teacher_class_access(user, "1班", session)


def test_teacher_denied_for_unassigned_class(session):
    from app.models import User
    from app.core.security import hash_password
    teacher = User(username="t1", name="教师1", role="teacher",
                   assigned_classes='["1班"]',
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    session.add(teacher)
    session.commit()
    user = {"sub": str(teacher.id), "role": "teacher"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, "2班", session)
    assert exc_info.value.status_code == 403


def test_student_denied(session):
    user = {"sub": "TEST001", "role": "student"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, "1班", session)
    assert exc_info.value.status_code == 403


def test_teacher_not_found_in_db_denied(session):
    """教师账号已删除但 token 未过期（fail-closed）"""
    user = {"sub": "99999", "role": "teacher"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, "1班", session)
    assert exc_info.value.status_code == 403


# ============ offerings 派生路径测试（Phase 2a） ============

def _derive_setup(session):
    """造教师 + 教学班（无 assigned_classes），返回 (user, class_name)"""
    from app.models import Course, CourseOffering, Semester, User, UserRoleConst
    from app.core.security import hash_password

    teacher = User(
        username="derive_teacher", name="派生教师",
        password_hash=hash_password("pass123"), role=UserRoleConst.TEACHER,
        assigned_classes="[]",
    )
    session.add(teacher); session.flush()
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7), total_weeks=20, is_current=True))
    session.add(Course(code="C1", name="高等数学"))
    session.flush()
    course = session.exec(select(Course).where(Course.code == "C1")).one()
    sem = session.exec(select(Semester).where(Semester.label == "2026-2027-1")).one()
    session.add(CourseOffering(
        course_id=course.id, semester_id=sem.id,
        teacher_id=teacher.id, teacher_name="派生教师", class_scope="计科1班, 计科2班",
    ))
    session.commit()
    return teacher


def test_verify_derives_access_from_offerings(session):
    """assigned_classes 为空时，offerings 派生的班级可通过校验"""
    from fastapi import HTTPException
    from app.api.deps import verify_teacher_class_access

    teacher = _derive_setup(session)
    verify_teacher_class_access(
        {"role": "teacher", "sub": str(teacher.id)}, "计科1班", session,
    )  # 不抛异常即通过


def test_verify_derived_access_rejects_unrelated_class(session):
    """offerings 派生：无关班级仍拒绝"""
    from fastapi import HTTPException
    from app.api.deps import verify_teacher_class_access

    teacher = _derive_setup(session)
    with pytest.raises(HTTPException, match="无权操作该班级"):
        verify_teacher_class_access(
            {"role": "teacher", "sub": str(teacher.id)}, "无关班", session,
        )
