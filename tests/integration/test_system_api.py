"""
系统相关 API 集成测试
"""
import pytest


class TestHealthAPI:
    """健康检查 API 测试"""

    def test_health_check(self, client):
        """健康检查接口"""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_health_check_no_auth_required(self, client):
        """健康检查不需要认证"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        # 确保没有返回 401
        assert response.json()["status"] == "healthy"


class TestStatsAPI:
    """统计 API 测试"""

    def test_get_stats_empty(self, admin_client):
        """空数据统计"""
        response = admin_client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 0
        assert data["data"]["total_classes"] == 0
        assert data["data"]["today_checkins"] == 0
    
    def test_get_stats_with_data(self, admin_client, sample_students):
        """有数据的统计"""
        response = admin_client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 6
        assert data["data"]["total_classes"] == 3  # 一班、二班
        assert data["data"]["today_checkins"] == 0
    
    def test_get_stats_requires_auth(self, client):
        """统计接口需要认证（未登录返回 401）"""
        response = client.get("/api/v1/stats")

        assert response.status_code == 401

    def test_get_stats_student_access(self, student_client, student_user):
        """学生统计只覆盖本班（一班）"""
        response = student_client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 1  # 一班只有 student_user 一个学生
        assert data["data"]["total_classes"] == 1   # 本人所在班级
        assert data["data"]["today_checkins"] == 0

    def test_get_stats_teacher_access(self, teacher_client, sample_students):
        """教师统计只覆盖授课班级（course_offerings.class_scope = 一班,二班）

        sample_students 共 6 人：一班 3 人、二班 2 人、三班 1 人 → 教师看不到三班
        """
        response = teacher_client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total_students"] == 5
        assert data["data"]["total_classes"] == 2

    def test_get_stats_teacher_without_offerings_is_empty(self, test_engine, sample_students):
        """无授课教学班的教师统计为空（fail-closed，不回退全校数据）"""
        from fastapi.testclient import TestClient
        from sqlmodel import Session
        from app.models import User, UserRoleConst
        from app.core.security import generate_password_hash
        from tests.integration.conftest import _test_engine
        from main import app  # noqa: F401

        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("teacher123")
            session.add(User(
                username="teacher_no_class", name="无课教师",
                password_hash=password_hash, salt=salt,
                role=UserRoleConst.TEACHER, is_active=True,
            ))
            session.commit()

        def get_session_override():
            with Session(_test_engine) as s:
                yield s

        from app.core.db import get_session
        app.dependency_overrides[get_session] = get_session_override
        try:
            with TestClient(app, cookies={}) as client:
                login = client.post("/api/v1/login", json={
                    "username": "teacher_no_class",
                    "password": "teacher123",
                    "role": "teacher",
                })
                assert login.status_code == 200, login.json()
                response = client.get("/api/v1/stats")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()["data"]
        assert data == {"total_students": 0, "total_classes": 0, "today_checkins": 0}
