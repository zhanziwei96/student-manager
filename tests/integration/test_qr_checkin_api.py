"""
二维码签到 API 集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


class TestQRCheckinAPI:
    """二维码签到接口测试"""

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
        from app.core.security import generate_password_hash
        from app.models import Student
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("student123")
            student = Student(
                student_id=student_id,
                name=name,
                class_name=class_name,
                score=80.0,
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

    def test_get_qr_payload_success(self, client, test_engine):
        """教师成功获取二维码 payload"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)

        response = client.get(f"/api/v1/course-sessions/{cs.id}/qr-payload")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_code" in data["data"]
        assert "timestamp" in data["data"]
        assert "signature" in data["data"]

    def test_get_qr_payload_not_found(self, client, test_engine):
        """获取不存在的课堂二维码返回 404"""
        self._get_teacher_token(client, test_engine)

        response = client.get("/api/v1/course-sessions/99999/qr-payload")
        assert response.status_code == 404

    def test_get_qr_payload_forbidden(self, client, test_engine):
        """非创建教师获取二维码返回 403"""
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

        response = client.get(f"/api/v1/course-sessions/{cs.id}/qr-payload")
        assert response.status_code == 403

    def test_checkin_with_valid_qr(self, client, test_engine):
        """使用有效二维码签到成功"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        # 重新登录教师，确保调用 /qr-payload 是教师身份
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })

        # 获取二维码
        qr_resp = client.get(f"/api/v1/course-sessions/{cs.id}/qr-payload")
        assert qr_resp.status_code == 200
        qr = qr_resp.json()["data"]

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
            "qr_payload": {
                "session_code": qr["session_code"],
                "timestamp": qr["timestamp"],
                "signature": qr["signature"]
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["student_id"] == "S001"

    def test_checkin_with_invalid_qr_signature(self, client, test_engine):
        """使用无效二维码签名签到失败"""
        self._get_teacher_token(client, test_engine)
        self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "qr_payload": {
                "session_code": "INVALID",
                "timestamp": 1234567890,
                "signature": "bad_signature"
            }
        })
        assert response.status_code == 400
        data = response.json()
        assert "二维码" in data["message"] or "无效" in data["message"] or "过期" in data["message"]

    def test_checkin_with_expired_qr(self, client, test_engine):
        """使用过期的二维码签到失败"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        import time
        from app.core.qr_signature import generate_qr_signature
        expired_timestamp = int(time.time()) - 3600
        expired_signature = generate_qr_signature(cs.session_code, expired_timestamp)

        response = client.post("/api/v1/checkin", json={
            "student_id": "S001",
            "student_name": "学生1",
            "qr_payload": {
                "session_code": cs.session_code,
                "timestamp": expired_timestamp,
                "signature": expired_signature
            }
        })
        assert response.status_code == 400
        data = response.json()
        assert "过期" in data["message"] or "二维码" in data["message"] or "无效" in data["message"]

    def test_checkin_duplicate_with_qr(self, client, test_engine):
        """同一学生重复二维码签到失败"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        # 教师登录获取二维码
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        qr_resp = client.get(f"/api/v1/course-sessions/{cs.id}/qr-payload")
        assert qr_resp.status_code == 200
        qr = qr_resp.json()["data"]

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
            "qr_payload": {
                "session_code": qr["session_code"],
                "timestamp": qr["timestamp"],
                "signature": qr["signature"]
            }
        }

        first = client.post("/api/v1/checkin", json=payload)
        assert first.status_code == 200

        second = client.post("/api/v1/checkin", json=payload)
        assert second.status_code == 409
        assert "签到" in second.json()["message"]

    def test_checkin_device_bound_and_updated(self, client, test_engine):
        """设备绑定创建和更新"""
        self._get_teacher_token(client, test_engine)
        cs = self._start_class_directly(test_engine, "一班", teacher_id=1)
        self._get_student_client(client, test_engine, student_id="S001", class_name="一班")

        # 教师登录获取二维码
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        qr_resp = client.get(f"/api/v1/course-sessions/{cs.id}/qr-payload")
        assert qr_resp.status_code == 200
        qr = qr_resp.json()["data"]

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
            "qr_payload": {
                "session_code": qr["session_code"],
                "timestamp": qr["timestamp"],
                "signature": qr["signature"]
            }
        })
        assert response.status_code == 200

        from app.crud.device_bind import get_device_bind
        with Session(test_engine) as session:
            bind = get_device_bind(session, cs.id, "S001")
            assert bind is not None
            assert bind.device_id == "device_old"

        # 再次获取新二维码（时间戳会变化）
        client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        qr_resp2 = client.get(f"/api/v1/course-sessions/{cs.id}/qr-payload")
        assert qr_resp2.status_code == 200
        qr2 = qr_resp2.json()["data"]

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
            "qr_payload": {
                "session_code": qr2["session_code"],
                "timestamp": qr2["timestamp"],
                "signature": qr2["signature"]
            }
        })
        # 学生已经签到过，应返回 409；但设备绑定应已更新
        # 注意：需求说"如果已绑定且设备不同，更新绑定"，但重复签到会抛 DuplicateCheckinError
        # 所以这里行为是 409，但绑定已更新
        assert response2.status_code == 409

        with Session(test_engine) as session:
            bind = get_device_bind(session, cs.id, "S001")
            assert bind.device_id == "device_new"
