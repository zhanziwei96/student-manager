"""
学生登录账号锁定机制集成测试

覆盖：
- 连续失败达到上限后账号锁定（403）
- 失败计数递增
- 登录成功后重置失败计数与锁定状态
- 锁定期间即使密码正确也拒绝登录
- 锁定过期后可正常登录
- 禁用账号拒绝登录
"""
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session


class TestStudentLoginLockout:
    """学生登录锁定机制测试"""

    def _login(self, client, password, username="S001"):
        return client.post("/api/v1/login", json={
            "username": username,
            "password": password,
            "role": "student"
        })

    def test_student_login_locks_after_max_failures(self, client, student_user, test_engine):
        """学生连续登录失败达到上限后账号锁定"""
        from app.core.config import get_settings
        settings = get_settings()
        max_failures = settings.security.max_login_failures

        # 前 max_failures-1 次失败返回 401
        for _ in range(max_failures - 1):
            response = self._login(client, "wrongpassword")
            assert response.status_code == 401

        # 第 max_failures 次失败触发锁定，返回 403（与教师登录行为一致）
        response = self._login(client, "wrongpassword")
        assert response.status_code == 403
        assert "锁定" in response.json()["message"]

        # 第 max_failures+1 次：即使密码正确也应 403（已锁定）
        response = self._login(client, "student123")
        assert response.status_code == 403
        data = response.json()
        assert "锁定" in data["message"]

        # 数据库中 locked_until 应已设置
        from app.crud import get_student
        with Session(test_engine) as session:
            student = get_student(session, "S001")
            assert student.login_fail_count >= max_failures
            assert student.locked_until is not None

    def test_student_login_failure_increments_count(self, client, student_user, test_engine):
        """单次登录失败后计数递增"""
        from app.crud import get_student

        response = self._login(client, "wrongpassword")
        assert response.status_code == 401

        with Session(test_engine) as session:
            student = get_student(session, "S001")
            assert student.login_fail_count == 1
            assert student.locked_until is None

    def test_student_login_success_resets_fail_count(self, client, student_user, test_engine):
        """登录成功后重置失败计数与锁定状态"""
        from app.crud import get_student

        # 先失败两次
        for _ in range(2):
            response = self._login(client, "wrongpassword")
            assert response.status_code == 401

        # 正确密码登录成功
        response = self._login(client, "student123")
        assert response.status_code == 200

        with Session(test_engine) as session:
            student = get_student(session, "S001")
            assert student.login_fail_count == 0
            assert student.locked_until is None

    def test_student_locked_account_rejects_correct_password(self, client, student_user, test_engine):
        """锁定期间即使密码正确也拒绝登录"""
        from app.crud import get_student

        # 直接设置锁定状态
        with Session(test_engine) as session:
            student = get_student(session, "S001")
            student.locked_until = datetime.now() + timedelta(minutes=30)
            session.add(student)
            session.commit()

        response = self._login(client, "student123")
        assert response.status_code == 403
        data = response.json()
        assert "锁定" in data["message"]

    def test_student_login_after_lockout_expired(self, client, student_user, test_engine):
        """锁定过期后可正常登录"""
        from app.crud import get_student

        # 设置已过期的锁定时间
        with Session(test_engine) as session:
            student = get_student(session, "S001")
            student.locked_until = datetime.now() - timedelta(minutes=1)
            session.add(student)
            session.commit()

        response = self._login(client, "student123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_student_disabled_account_rejected(self, client, student_user, test_engine):
        """禁用账号拒绝登录"""
        from app.crud import get_student

        with Session(test_engine) as session:
            student = get_student(session, "S001")
            student.is_account_enabled = False
            session.add(student)
            session.commit()

        response = self._login(client, "student123")
        assert response.status_code == 403
        data = response.json()
        assert "禁用" in data["message"]


class TestStudentManualUnlock:
    """学生手动解锁机制测试（管理员/教师运维途径）"""

    @pytest.fixture
    def locked_student_id(self, test_engine, seed_refs):
        """创建一名已锁定的学生（一班，密码 student123，便于教师班级权限测试）"""
        from app.core.security import generate_password_hash
        from app.models import Student

        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("student123")
            student = Student(
                student_id="SLOCK",
                name="锁定学生",
                class_id=seed_refs["一班"],
                score=0.0,
                password_hash=password_hash,
                salt=salt,
                login_fail_count=5,
                locked_until=datetime.now() + timedelta(minutes=30),
            )
            session.add(student)
            session.commit()
        return "SLOCK"

    def _login(self, client, password, username="SLOCK"):
        return client.post("/api/v1/login", json={
            "username": username,
            "password": password,
            "role": "student"
        })

    def test_admin_can_unlock_student(self, admin_client, locked_student_id):
        """管理员可手动解锁学生"""
        resp = admin_client.put(f"/api/v1/students/{locked_student_id}/unlock")
        assert resp.status_code == 200
        # 解锁后可正常登录
        login_resp = self._login(admin_client, "student123")
        assert login_resp.status_code == 200

    def test_teacher_can_unlock_own_class_student(self, teacher_client, locked_student_id):
        """教师可解锁自己班的学生"""
        resp = teacher_client.put(f"/api/v1/students/{locked_student_id}/unlock")
        assert resp.status_code == 200

    def test_student_cannot_unlock(self, student_client, locked_student_id):
        """学生不能解锁任何人"""
        resp = student_client.put(f"/api/v1/students/{locked_student_id}/unlock")
        assert resp.status_code == 403

    def test_reset_password_also_unlocks(self, admin_client, locked_student_id):
        """重置密码顺带解锁（与教师侧一致）"""
        resp = admin_client.put(
            f"/api/v1/students/{locked_student_id}/reset-password",
            json={"new_password": "newpass123"}
        )
        assert resp.status_code == 200
        # 解锁后新密码可登录
        login_resp = self._login(admin_client, "newpass123")
        assert login_resp.status_code == 200
