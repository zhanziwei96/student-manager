"""
越权负向测试：未授权角色调用敏感接口必须 403

对应 P0 安全修复（students 路由越权）：
- 学生不可改分/加学生/看他人详情与他人分数
- 教师不可查看非负责班级学生详情
- 学生详情响应不得泄露 password_hash
- 学生不可查看学生列表/导入学生
- 学生列表响应不得泄露 password_hash
"""
import pytest
from sqlmodel import Session

from app.models import Student


@pytest.fixture
def other_student_id(test_engine):
    """创建其他学生（非登录学生 S001，二班）并返回其学号"""
    with Session(test_engine) as session:
        student = Student(
            student_id="S002",
            name="其他学生",
            class_name="二班",
            score=75.0,
        )
        student_id = student.student_id
        session.add(student)
        session.commit()
    return student_id


@pytest.fixture
def other_class_student_id(test_engine):
    """创建三班学生（教师未负责班级）并返回其学号"""
    with Session(test_engine) as session:
        student = Student(
            student_id="S030",
            name="三班学生",
            class_name="三班",
            score=70.0,
        )
        student_id = student.student_id
        session.add(student)
        session.commit()
    return student_id


def test_student_cannot_update_score(student_client, other_student_id):
    """学生不能修改任意学生（含他人）的分数"""
    resp = student_client.put(
        f"/api/v1/students/{other_student_id}/score",
        json={"score_change": 10, "reason": "越权测试"},
    )
    assert resp.status_code == 403


def test_student_cannot_update_own_score(student_client, student_user):
    """学生也不能修改自己的分数"""
    resp = student_client.put(
        "/api/v1/students/S001/score",
        json={"score_change": 10, "reason": "越权测试"},
    )
    assert resp.status_code == 403


def test_student_cannot_add_student(student_client):
    """学生不能添加学生"""
    resp = student_client.post(
        "/api/v1/students",
        json={"student_id": "HACK001", "name": "越权学生", "class_name": "1班"},
    )
    assert resp.status_code == 403


def test_teacher_cannot_view_other_class_student(teacher_client, other_class_student_id):
    """教师不能查看非负责班级的学生详情"""
    resp = teacher_client.get(f"/api/v1/students/{other_class_student_id}")
    assert resp.status_code == 403


def test_student_detail_has_no_password_hash(admin_client, student_user):
    """学生详情响应不含 password_hash"""
    resp = admin_client.get("/api/v1/students/S001")
    assert resp.status_code == 200
    assert "password_hash" not in resp.json()["data"]


def test_student_cannot_read_other_student_scores(student_client, other_student_id):
    """学生不能查看他人分数历史"""
    resp = student_client.get(f"/api/v1/students/{other_student_id}/scores")
    assert resp.status_code == 403


def test_student_cannot_list_students(student_client, student_user):
    """学生不能查看学生列表"""
    resp = student_client.get("/api/v1/students")
    assert resp.status_code == 403


def test_student_list_has_no_password_hash(admin_client, student_user):
    """学生列表响应不含 password_hash（遍历返回的学生对象断言）"""
    resp = admin_client.get("/api/v1/students")
    assert resp.status_code == 200
    students = resp.json()["data"]
    assert any(s["student_id"] == "S001" for s in students), "列表应包含 S001 学生"
    for student in students:
        assert "password_hash" not in student


def test_student_cannot_import_students(student_client):
    """学生不能导入学生"""
    resp = student_client.post(
        "/api/v1/students/import",
        files={"file": ("students.xlsx", b"fake-content", "application/octet-stream")},
    )
    assert resp.status_code == 403


def test_teacher_can_view_assigned_class_student_detail(teacher_client, student_user):
    """教师可以查看负责班级学生的详情（正向控制，防止权限收紧误伤）"""
    resp = teacher_client.get("/api/v1/students/S001")
    assert resp.status_code == 200
    assert resp.json()["data"]["student_id"] == "S001"
