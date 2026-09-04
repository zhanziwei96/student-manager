"""verify_teacher_class_access 测试"""
import pytest
from fastapi import HTTPException
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
