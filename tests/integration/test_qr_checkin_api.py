"""
动态验证码签到 API 集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestQRCheckinAPI:
    """动态验证码签到接口测试"""

    def _start_class_directly(self, test_engine, class_name, course_name=None, teacher_id=1, teacher_name="张老师"):
        """直接通过 CRUD 创建活跃课堂用于测试"""
        from app.crud.course_session import start_course_session
        with Session(test_engine) as session:
            cs = start_course_session(
                session=session,
                class_name=class_name,
                teacher_id=teacher_id,
                teacher_name=teacher_name,
                course_name=course_name
            )
            return cs

    def _get_teacher_token(self, client, test_engine):
        """获取教师登录 token/cookie"""
        from app.core.security import generate_password_hash
        from app.models import User, UserRoleConst
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("teacher123")
            user = User(
                username="teacher1",
                name="教师1",
                password_hash=password_hash,
                salt=salt,
                role=UserRoleConst.TEACHER,
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        response = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert response.status_code == 200
        return user

    def _get_student_client(self, client, test_engine, student_id="S001", name="学生1", class_name="一班"):
        """创建学生并登录，返回 (client, student)"""
        from app.core.class_cache import get_class_id_by_name
        from app.core.security import generate_password_hash
        from app.models import Student
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("student123")
            student = Student(
                student_id=student_id,
                name=name,
                class_name=class_name,
                class_id=get_class_id_by_name(session, class_name),
                password_hash=password_hash,
                salt=salt
            )
            session.add(student)
            session.commit()
            session.refresh(student)
        response = client.post("/api/v1/login", json={
            "username": student_id,
            "password": "student123",
            "role": "student"
        })
        assert response.status_code == 200
        return client, student

    def test_get_verification_code_success(self, client, test_engine, seed_refs):
        """教师成功获取动态验证码"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)

        response = client.get(f"/api/v1/course-sessions/{cs.id}/verification-code")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "code" in data["data"]
        assert len(data["data"]["code"]) == 6
        assert "expires_in" in data["data"]

    def test_get_verification_code_not_found(self, client, test_engine):
        """获取不存在的课堂验证码返回 404"""
        self._get_teacher_token(client, test_engine)

        response = client.get("/api/v1/course-sessions/99999/verification-code")
        assert response.status_code == 404

    def test_get_verification_code_forbidden(self, client, test_engine, seed_refs):
        """非创建教师获取验证码返回 403"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)

        # 登录另一个教师
        from app.core.security import generate_password_hash
        from app.models import User, UserRoleConst
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("teacher123")
            user2 = User(
                username="teacher2",
                name="教师2",
                password_hash=password_hash,
                salt=salt,
                role=UserRoleConst.TEACHER,
                is_active=True
            )
            session.add(user2)
            session.commit()
            session.refresh(user2)
        client.post("/api/v1/login", json={
            "username": "teacher2",
            "password": "teacher123",
            "role": "teacher"
        })

        response = client.get(f"/api/v1/course-sessions/{cs.id}/verification-code")
        assert response.status_code == 403

    def test_checkin_with_valid_code(self, client, test_engine, seed_refs):
        """使用有效验证码签到成功"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        # 重新登录教师，确保调用 /verification-code 是教师身份
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })

        # 获取验证码
        code_resp = client.get(f"/api/v1/course-sessions/{cs.id}/verification-code")
        assert code_resp.status_code == 200
        code = code_resp.json()["data"]["code"]

        # 登录学生
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })

        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "device_id": "device001",
            "device_info": '{"browser": "test"}',
            "verification_code": code
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["student_id"] == "S001"

    def test_checkin_with_invalid_code(self, client, test_engine, seed_refs):
        """使用无效验证码签到失败"""
        self._get_teacher_token(client, test_engine)
        self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "verification_code": "BAD000"
        })
        assert response.status_code == 400
        data = response.json()
        assert "验证码" in data["message"] or "无效" in data["message"] or "过期" in data["message"]

    def test_checkin_duplicate_with_code(self, client, test_engine, seed_refs):
        """同一学生重复验证码签到失败"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        # 教师登录获取验证码
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        code_resp = client.get(f"/api/v1/course-sessions/{cs.id}/verification-code")
        assert code_resp.status_code == 200
        code = code_resp.json()["data"]["code"]

        # 学生登录签到
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        payload = {
            "student_id": "S001",
            "student_name": "学生1",
            "device_id": "device001",
            "verification_code": code
        }

        first = client.post("/api/v1/checkin", json=payload)
        assert first.status_code == 200

        second = client.post("/api/v1/checkin", json=payload)
        assert second.status_code == 409
        assert "签到" in second.json()["message"]

    def test_checkin_device_bound_and_updated(self, client, test_engine, seed_refs):
        """设备绑定创建和更新"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        # 教师登录获取验证码
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        code_resp = client.get(f"/api/v1/course-sessions/{cs.id}/verification-code")
        assert code_resp.status_code == 200
        code = code_resp.json()["data"]["code"]

        # 学生登录签到
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        # 第一次签到，设备绑定
        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "device_id": "device_old",
            "verification_code": code
        })
        assert response.status_code == 200

        from app.crud.device_bind import get_device_bind
        with Session(test_engine) as session:
            bind = get_device_bind(session, cs.id, "S001")
            assert bind is not None
            assert bind.device_id == "device_old"

        # 再次获取新验证码
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        code_resp2 = client.get(f"/api/v1/course-sessions/{cs.id}/verification-code")
        assert code_resp2.status_code == 200
        code2 = code_resp2.json()["data"]["code"]

        # 学生登录，用新设备签到，绑定应更新
        client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        response2 = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "device_id": "device_new",
            "verification_code": code2
        })
        # 学生已经签到过，应返回 409；但设备绑定应已更新
        assert response2.status_code == 409

        with Session(test_engine) as session:
            bind = get_device_bind(session, cs.id, "S001")
            assert bind.device_id == "device_new"
