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


# ========== 签到路由越权负向测试（Task 11） ==========

@pytest.fixture
def some_session_id(test_engine):
    """创建活跃课堂会话并返回其 id（签到越权测试数据）"""
    from app.crud.course_session import start_course_session
    with Session(test_engine) as session:
        cs = start_course_session(
            session=session,
            class_name="一班",
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学",
        )
        return cs.id


@pytest.fixture
def anon_client(client):
    """未登录客户端（无任何身份，等价匿名访问）"""
    return client


def test_student_cannot_list_all_checkins(student_client):
    """学生不能获取全部签到记录列表"""
    resp = student_client.get("/api/v1/checkins")
    assert resp.status_code == 403


def test_student_cannot_read_session_checkins(student_client, some_session_id):
    """学生不能获取指定课堂会话的签到列表"""
    resp = student_client.get(f"/api/v1/checkins/session/{some_session_id}")
    assert resp.status_code == 403


def test_student_cannot_read_checkin_stats(student_client, some_session_id):
    """学生不能获取签到统计"""
    resp = student_client.get("/api/v1/checkins/stats", params={"session_id": some_session_id})
    assert resp.status_code == 403


def test_active_course_sessions_requires_login(anon_client):
    """未登录不可枚举活跃课堂"""
    resp = anon_client.get("/api/v1/course-sessions/active")
    assert resp.status_code == 401


# ========== 教师无负责班级的签到列表 fail-closed ==========

@pytest.fixture
def teacher_without_classes_client(test_engine):
    """已登录且无负责班级的教师客户端（assigned_classes 用默认值 '[]'）

    同时造一条"一班"签到记录：若空班级列表被跳过过滤（旧 bug），
    该记录会泄漏给教师，本用例将失败——用于验证 fail-closed。
    """
    from fastapi.testclient import TestClient
    from main import app
    from app.core.db import get_session
    from app.core.security import generate_password_hash
    from app.models import CheckinRecord, User, UserRoleConst

    with Session(test_engine) as session:
        password_hash, salt = generate_password_hash("teacher123")
        teacher = User(
            username="teacher_noclass",
            name="无班级教师",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.TEACHER,
            is_active=True,
            # 不传 assigned_classes，使用模型默认值 "[]"（未分班）
        )
        session.add(teacher)
        session.add(CheckinRecord(
            student_id="S001", student_name="学生1", class_name="一班"
        ))
        session.commit()

    def get_session_override():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app, cookies={}) as c:
        response = c.post("/api/v1/login", json={
            "username": "teacher_noclass",
            "password": "teacher123",
            "role": "teacher",
        })
        assert response.status_code == 200, f"Teacher login failed: {response.json()}"
        yield c
    app.dependency_overrides.clear()


def test_teacher_without_classes_sees_empty_checkin_list(client, teacher_without_classes_client):
    """无负责班级的教师不应看到任何签到记录（fail-closed）"""
    resp = teacher_without_classes_client.get("/api/v1/checkins")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


# ========== 失物招领越权负向测试（Task 12） ==========

@pytest.fixture
def teacher2_user(test_engine):
    """创建第二个教师账号（不共享物品所有权）"""
    from app.core.security import generate_password_hash
    from app.models import User, UserRoleConst

    with Session(test_engine) as session:
        password_hash, salt = generate_password_hash("teacher123")
        user = User(
            username="teacher2",
            name="教师2",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.TEACHER,
            assigned_classes='["一班", "二班"]',
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def teacher2_client(test_engine, teacher2_user):
    """第二个教师（teacher2）的已登录客户端，独立实例避免 cookie 冲突"""
    from fastapi.testclient import TestClient
    from main import app
    from app.core.db import get_session

    def get_session_override():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app, cookies={}) as c:
        response = c.post("/api/v1/login", json={
            "username": "teacher2",
            "password": "teacher123",
            "role": "teacher",
        })
        assert response.status_code == 200, f"Teacher2 login failed: {response.json()}"
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def teacher2_item_id(teacher2_client):
    """教师2 发布的失物招领物品 id（对他人的越权测试目标）"""
    resp = teacher2_client.post("/api/v1/teacher/lost-found", data={
        "title": "教师2的物品",
        "description": "属于教师2的物品",
        "location": "教室",
    })
    assert resp.status_code == 200, f"Teacher2 create item failed: {resp.json()}"
    return resp.json()["data"]["item_id"]


def test_teacher_cannot_delete_others_lost_found_item(teacher_client, teacher2_client, teacher2_item_id):
    """教师不能删除他人发布的物品"""
    resp = teacher_client.delete(f"/api/v1/teacher/lost-found/{teacher2_item_id}")
    assert resp.status_code == 403


def test_teacher_cannot_update_others_lost_found_item(teacher_client, teacher2_client, teacher2_item_id):
    """教师不能编辑他人发布的物品"""
    resp = teacher_client.put(
        f"/api/v1/teacher/lost-found/{teacher2_item_id}",
        data={"title": "篡改"},
    )
    assert resp.status_code == 403


def test_teacher_cannot_confirm_others_lost_found_claim(teacher_client, teacher2_client, teacher2_item_id):
    """教师不能确认他人发布物品的认领（任取 claim_id：所有权校验先于认领校验）"""
    resp = teacher_client.put(
        f"/api/v1/teacher/lost-found/{teacher2_item_id}/claims/1/confirm"
    )
    assert resp.status_code == 403


def test_teacher_cannot_reject_others_lost_found_claim(teacher_client, teacher2_client, teacher2_item_id):
    """教师不能拒绝他人发布物品的认领"""
    resp = teacher_client.put(
        f"/api/v1/teacher/lost-found/{teacher2_item_id}/claims/1/reject"
    )
    assert resp.status_code == 403
