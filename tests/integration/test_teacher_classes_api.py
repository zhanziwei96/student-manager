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


def test_teacher_get_available_classes(teacher_client, test_engine):
    """老师获取全部可用班级，应包含未负责的班级"""
    from app.models import Student
    with Session(test_engine) as session:
        session.add(Student(student_id="S007", name="学生7", class_name="一班", score=80.0))
        session.add(Student(student_id="S008", name="学生8", class_name="二班", score=80.0))
        session.add(Student(student_id="S009", name="学生9", class_name="三班", score=80.0))
        session.commit()

    resp = teacher_client.get("/api/v1/teacher/classes/available")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    data = resp.json()["data"]
    assert isinstance(data, list)
    # 老师负责的班级为 一班、二班，三班未负责但应出现在可用列表中
    assert "三班" in data


def test_student_cannot_manage_teacher_classes(student_client):
    """学生不能管理班级"""
    resp = student_client.put(
        "/api/v1/teacher/classes",
        json={"class_names": ["一班"]}
    )
    assert resp.status_code == 403
