"""
课堂会话/活跃课堂 权限范围回归测试

覆盖三处越权修复（2026-09-21）：
- POST /course-sessions/start：原仅 get_current_user（学生也能开课、教师可为任意班级开课）
- GET  /course-sessions/class/{class_id}：原任何人可拿任意班级的 session_code
- GET  /course-sessions/active：原返回全校活跃课堂（含班级/教师名）

学生端签到页每 10 秒轮询 /course-sessions/class/{class_id}，
「学生查自己班 → 200 且响应结构不变」是必须保持的基线。
"""
import pytest
from sqlmodel import Session


@pytest.fixture
def seeded_students(seed_refs, test_engine):
    """一班/二班/三班各 1 名启用学生（开课校验要求班级有启用学生）"""
    from app.models import Student

    with Session(test_engine) as session:
        for i, name in enumerate(("一班", "二班", "三班")):
            session.add(Student(
                student_id=f"SC{i:03d}",
                name=f"范围学生{i}",
                class_id=seed_refs[name],
            ))
        session.commit()
    return seed_refs


def _start_session(test_engine, class_id, teacher_id=1, course_name="范围测试课程"):
    """直接用 CRUD 造活跃课堂（绕过 API 权限，便于构造越权场景）"""
    from app.crud.course_session import start_course_session

    with Session(test_engine) as session:
        return start_course_session(
            session=session,
            class_id=class_id,
            teacher_id=teacher_id,
            teacher_name="张老师",
            course_name=course_name,
        )


class TestStudentSessionScope:
    """学生：只能访问自己班级的课堂状态"""

    def test_student_can_read_own_class_session(self, student_client, test_engine, seed_refs):
        """学生查自己班 → 200 且响应结构不变（签到页 10s 轮询基线，必须保持）"""
        cs = _start_session(test_engine, seed_refs["一班"])

        response = student_client.get(
            f"/api/v1/course-sessions/class/{seed_refs['一班']}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] is True
        assert data["data"]["session_code"] == cs.session_code
        assert data["data"]["class_name"] == "2026届一班"

    def test_student_own_class_no_active_session(self, student_client, seed_refs):
        """学生查自己班且无活跃课堂 → 200 + active=False（不是 403）"""
        response = student_client.get(
            f"/api/v1/course-sessions/class/{seed_refs['一班']}")

        assert response.status_code == 200
        assert response.json()["data"]["active"] is False

    def test_student_cannot_read_other_class_session(self, student_client, test_engine, seed_refs):
        """学生查其他班 → 403，且不泄露 session_code"""
        _start_session(test_engine, seed_refs["三班"])

        response = student_client.get(
            f"/api/v1/course-sessions/class/{seed_refs['三班']}")

        assert response.status_code == 403
        assert "session_code" not in response.text

    def test_student_active_list_only_own_class(self, student_client, test_engine, seed_refs):
        """学生活跃课堂列表只含本班（修复前返回全校）"""
        _start_session(test_engine, seed_refs["一班"], course_name="本班课程")
        _start_session(test_engine, seed_refs["三班"], course_name="他班课程")

        response = student_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["course_name"] == "本班课程"
        assert data[0]["class_name"] == "2026届一班"

    def test_student_cannot_start_course_session(self, student_client, seeded_students):
        """学生不能开课（原依赖仅校验登录）→ 403"""
        response = student_client.post("/api/v1/course-sessions/start", json={
            "class_id": seeded_students["一班"],
            "course_name": "学生开课",
        })

        assert response.status_code == 403


class TestTeacherSessionScope:
    """教师：只能访问授课班级（course_offering_classes 关联一班/二班）"""

    def test_teacher_can_read_own_class_session(self, teacher_client, test_engine, seed_refs):
        """教师查自己授课班级 → 200"""
        cs = _start_session(test_engine, seed_refs["一班"])

        response = teacher_client.get(
            f"/api/v1/course-sessions/class/{seed_refs['一班']}")

        assert response.status_code == 200
        assert response.json()["data"]["session_code"] == cs.session_code

    def test_teacher_cannot_read_other_class_session(self, teacher_client, test_engine, seed_refs):
        """教师查非授课班级 → 403（原可拿到 session_code 进而绕过验证码控制）"""
        _start_session(test_engine, seed_refs["三班"])

        response = teacher_client.get(
            f"/api/v1/course-sessions/class/{seed_refs['三班']}")

        assert response.status_code == 403
        assert "session_code" not in response.text

    def test_teacher_cannot_start_out_of_scope_class(self, teacher_client, seeded_students):
        """教师为非授课班级开课 → 403（原可为任意班级开课并绑定 session_code）"""
        response = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_id": seeded_students["三班"],
            "course_name": "越权开课",
        })

        assert response.status_code == 403

    def test_teacher_can_start_own_class(self, teacher_client, seeded_students):
        """正向对照：教师为自己授课班级开课仍 200（防止修复过度收紧）"""
        response = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_id": seeded_students["一班"],
            "course_name": "正常开课",
        })

        assert response.status_code == 200
        assert response.json()["data"]["active"] is True

    def test_teacher_active_list_only_accessible_classes(self, teacher_client, test_engine, seed_refs):
        """教师活跃课堂列表只含授课班级（修复前返回全校）"""
        _start_session(test_engine, seed_refs["一班"], course_name="我的课程")
        _start_session(test_engine, seed_refs["三班"], course_name="别人的课程")

        response = teacher_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["course_name"] == "我的课程"


class TestNoScopeTeacherFailClosed:
    """无教学班关联的教师按无权限处理（fail-closed）"""

    @pytest.fixture
    def no_scope_teacher_client(self, client, test_engine, seeded_students):
        """无任何教学班的教师（只使用 client 夹具，避免与其它客户端夹具互相清理 override）"""
        from app.core.security import generate_password_hash
        from app.models import User, UserRoleConst

        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("noscope123")
            session.add(User(
                username="noscope_teacher",
                name="无班教师",
                password_hash=password_hash,
                salt=salt,
                role=UserRoleConst.TEACHER,
                is_active=True,
            ))
            session.commit()

        resp = client.post("/api/v1/login", json={
            "username": "noscope_teacher",
            "password": "noscope123",
            "role": "teacher",
        })
        assert resp.status_code == 200, resp.json()
        return client

    def test_active_list_empty(self, no_scope_teacher_client, test_engine, seed_refs):
        """无教学班教师看到空活跃列表，而不是全校课堂"""
        _start_session(test_engine, seed_refs["一班"])

        response = no_scope_teacher_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_cannot_start_any_class(self, no_scope_teacher_client, seeded_students):
        """无教学班教师不能开课 → 403"""
        response = no_scope_teacher_client.post("/api/v1/course-sessions/start", json={
            "class_id": seeded_students["一班"],
            "course_name": "越权开课",
        })

        assert response.status_code == 403

    def test_cannot_read_any_class_session(self, no_scope_teacher_client, test_engine, seed_refs):
        """无教学班教师读任意班级课堂状态 → 403（不泄露 session_code）"""
        _start_session(test_engine, seed_refs["一班"])

        response = no_scope_teacher_client.get(
            f"/api/v1/course-sessions/class/{seed_refs['一班']}")

        assert response.status_code == 403
        assert "session_code" not in response.text


class TestAdminSessionScope:
    """管理员不受班级范围限制"""

    def test_admin_active_list_sees_all(self, admin_client, test_engine, seed_refs):
        """管理员活跃课堂列表返回全校"""
        _start_session(test_engine, seed_refs["一班"], course_name="课程A")
        _start_session(test_engine, seed_refs["三班"], course_name="课程B")

        response = admin_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        names = {s["course_name"] for s in response.json()["data"]}
        assert names == {"课程A", "课程B"}

    def test_admin_can_read_any_class_session(self, admin_client, test_engine, seed_refs):
        """管理员可读任意班级的活跃课堂（含 session_code）"""
        cs = _start_session(test_engine, seed_refs["三班"])

        response = admin_client.get(
            f"/api/v1/course-sessions/class/{seed_refs['三班']}")

        assert response.status_code == 200
        assert response.json()["data"]["session_code"] == cs.session_code

    def test_admin_can_start_any_class(self, admin_client, seeded_students):
        """管理员可为任意班级开课"""
        response = admin_client.post("/api/v1/course-sessions/start", json={
            "class_id": seeded_students["三班"],
            "course_name": "管理员开课",
        })

        assert response.status_code == 200
        assert response.json()["data"]["active"] is True
