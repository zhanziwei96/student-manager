"""
老师班级管理 API 集成测试
"""
from sqlmodel import Session, select


def test_teacher_update_own_classes(teacher_client, test_engine):
    """老师自己更新教的班级列表"""
    resp = teacher_client.put(
        "/api/v1/teacher/classes",
        json={"class_names": ["一班", "二班", "三班"]}
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 验证 assigned_classes 已更新
    from app.models import User
    with Session(test_engine) as session:
        user_obj = session.exec(select(User).where(User.username == "teacher1")).first()
        assert user_obj.get_assigned_classes() == ["一班", "二班", "三班"]


def test_teacher_get_own_classes(teacher_client):
    """老师获取自己教的班级"""
    resp = teacher_client.get("/api/v1/teacher/classes")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)


def test_student_cannot_manage_teacher_classes(student_client):
    """学生不能管理班级"""
    resp = student_client.put(
        "/api/v1/teacher/classes",
        json={"class_names": ["一班"]}
    )
    assert resp.status_code == 403
