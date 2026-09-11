"""
签到管理 API 集成测试 - 增强版（提升覆盖率）
说明：课堂管理路由(/class-session/*)已迁移，本文件仅保留签到相关 API 测试。
      需要活跃课堂的测试通过 CRUD 直接创建。
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.fixture
def student_user(test_engine, seed_refs):
    """学生（带 class_id）——签到路由按 FK 校验班级匹配，覆盖 conftest 同名 fixture"""
    from app.core.security import generate_password_hash
    from app.models import Student

    with Session(test_engine) as session:
        password_hash, salt = generate_password_hash("student123")
        student = Student(
            student_id="S001",
            name="学生1",
            class_id=seed_refs["一班"],
            password_hash=password_hash,
            salt=salt,
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        return student


class TestCheckinAPIEnhanced:
    """签到管理 API 增强测试"""

    def _start_class_directly(self, test_engine, class_id, course_name=None, teacher_id=1, teacher_name="张老师"):
        """直接通过 CRUD 创建活跃课堂用于测试"""
        from app.crud.course_session import start_course_session
        with Session(test_engine) as session:
            cs = start_course_session(
                session=session,
                class_id=class_id,
                teacher_id=teacher_id,
                teacher_name=teacher_name,
                course_name=course_name
            )
            return cs

    def test_student_checkin(self, client, test_engine, student_user, seed_refs):
        """测试学生签到 - 需要教师先开始上课"""
        self._start_class_directly(test_engine, seed_refs["一班"])

        # 学生登录并签到（student_user fixture 的密码是 student123）
        login_response = client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        assert login_response.status_code == 200

        # 获取验证码（教师已登录，但 client fixture 未登录教师，直接构造）
        from app.core.qr_signature import generate_verification_code
        from app.crud.course_session import get_active_course_session_by_class_id
        from sqlmodel import Session
        with Session(test_engine) as session:
            cs = get_active_course_session_by_class_id(session, seed_refs["一班"])
            code = generate_verification_code(cs.session_code)["code"]

        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "verification_code": code
        })

        # 签到成功返回 200
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_checkin_no_active_class(self, client, student_user):
        """测试没有活跃课堂时不能签到"""
        # 学生登录
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "verification_code": "BAD000"
        })

        assert response.status_code == 400
        data = response.json()
        assert "验证码" in data["message"] or "无效" in data["message"] or "过期" in data["message"] or "上课" in data["message"]

    def test_get_checkin_list(self, teacher_client, test_engine, seed_refs):
        """测试获取签到记录列表"""
        self._start_class_directly(test_engine, seed_refs["一班"])

        response = teacher_client.get("/api/v1/checkins")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_session_checkins(self, client, teacher_client, test_engine, student_user, seed_refs):
        """测试按 session 获取签到列表（教师有权限，学生无权限）"""
        cs = self._start_class_directly(test_engine, seed_refs["一班"])

        # 学生登录并签到
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        from app.core.qr_signature import generate_verification_code
        code = generate_verification_code(cs.session_code)["code"]
        client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "verification_code": code
        })

        # 学生无权限读取该 session 签到列表
        student_resp = client.get(f"/api/v1/checkins/session/{cs.id}")
        assert student_resp.status_code == 403

        # 负责该班的教师获取该 session 签到列表
        response = teacher_client.get(f"/api/v1/checkins/session/{cs.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["student_id"] == "S001"

    def test_get_checkin_stats(self, teacher_client, test_engine, sample_students, seed_refs):
        """测试获取签到统计"""
        # 开始上课
        self._start_class_directly(test_engine, seed_refs["一班"])

        response = teacher_client.get("/api/v1/checkins/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 统计信息
        assert "active" in data["data"]

    def test_get_active_class_sessions(self, teacher_client, test_engine, sample_students, seed_refs):
        """测试获取所有活跃课堂（需登录，教师可访问）"""
        self._start_class_directly(test_engine, seed_refs["一班"])

        response = teacher_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_class_session_for_student(self, client, test_engine, student_user, seed_refs):
        """测试学生获取班级课堂状态 - 需要登录"""
        self._start_class_directly(test_engine, seed_refs["一班"])

        # 学生登录（student_user fixture 创建的密码是 student123）
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        response = client.get(f"/api/v1/course-sessions/class/{seed_refs['一班']}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 有活跃课堂
        assert data["data"]["active"] is True

    def test_student_checkin_with_device(self, client, test_engine, student_user, seed_refs):
        """测试学生签到（带设备信息）"""
        cs = self._start_class_directly(test_engine, seed_refs["一班"])

        # 学生登录
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        from app.core.qr_signature import generate_verification_code
        code = generate_verification_code(cs.session_code)["code"]

        # 学生签到（带设备信息）
        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "device_id": "device001",
            "device_info": "{\"browser\": \"test\"}",
            "verification_code": code
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_device_cannot_checkin_twice(self, client, test_engine, student_user, seed_refs):
        """测试同一设备不能为多个学生签到"""
        cs = self._start_class_directly(test_engine, seed_refs["一班"])

        # 学生登录
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        from app.core.qr_signature import generate_verification_code
        code = generate_verification_code(cs.session_code)["code"]

        # 第一个学生用设备签到
        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "device_id": "shared_device",
            "verification_code": code
        })
        assert response.status_code == 200
