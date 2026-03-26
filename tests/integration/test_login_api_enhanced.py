"""
登录 API 集成测试 - 增强版（提升覆盖率）
"""
import pytest
from fastapi.testclient import TestClient


class TestLoginAPIEnhanced:
    """登录 API 增强测试"""
    
    def test_admin_login_success(self, client, admin_user):
        """测试管理员登录成功"""
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "admin"
        # 验证 cookie 已设置
        assert "access_token" in response.cookies
    
    def test_teacher_login_success(self, client, teacher_user):
        """测试教师登录成功"""
        response = client.post("/api/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "teacher"
    
    def test_student_login_success(self, client, student_user):
        """测试学生登录成功"""
        response = client.post("/api/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role"] == "student"
    
    def test_login_wrong_password(self, client, admin_user):
        """测试登录密码错误"""
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "wrongpassword",
            "role": "admin"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "密码" in data["message"]
    
    def test_login_user_not_found(self, client):
        """测试登录用户不存在"""
        response = client.post("/api/login", json={
            "username": "notexist",
            "password": "password123",
            "role": "admin"
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_login_wrong_role(self, client, admin_user):
        """测试登录角色错误"""
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "teacher"  # 错误的角色
        })
        
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
    
    def test_login_account_locked(self, client, admin_user):
        """测试账号被锁定后登录"""
        from datetime import datetime, timedelta
        from sqlmodel import Session
        from app.core.db import engine
        
        # 设置账号锁定
        with Session(engine) as session:
            from app.crud import get_user_by_username
            user = get_user_by_username(session, "admin")
            user.locked_until = datetime.now() + timedelta(minutes=30)
            session.add(user)
            session.commit()
        
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        assert response.status_code == 403
        data = response.json()
        assert "锁定" in data["message"]
    
    def test_login_account_disabled(self, client, admin_user):
        """测试账号被禁用后登录"""
        from sqlmodel import Session
        from app.core.db import engine
        
        # 禁用账号
        with Session(engine) as session:
            from app.crud import get_user_by_username
            user = get_user_by_username(session, "admin")
            user.is_account_enabled = False
            session.add(user)
            session.commit()
        
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        assert response.status_code == 403
        data = response.json()
        assert "禁用" in data["message"]
    
    def test_logout(self, admin_client):
        """测试登出"""
        response = admin_client.post("/api/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_me(self, admin_client):
        """测试获取当前用户信息"""
        response = admin_client.get("/api/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "admin"
    
    def test_get_me_unauthorized(self, client):
        """测试未登录获取用户信息"""
        response = client.get("/api/me")
        
        assert response.status_code == 401
    
    def test_change_password_success(self, admin_client):
        """测试修改密码成功"""
        response = admin_client.post("/api/change-password", json={
            "old_password": "admin123",
            "new_password": "newpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 使用新密码登录
        response = admin_client.post("/api/login", json={
            "username": "admin",
            "password": "newpassword123",
            "role": "admin"
        })
        assert response.status_code == 200
    
    def test_change_password_wrong_old(self, admin_client):
        """测试修改密码时旧密码错误"""
        response = admin_client.post("/api/change-password", json={
            "old_password": "wrongpassword",
            "new_password": "newpassword123"
        })
        
        assert response.status_code == 200  # 返回 200 但 success=False
        data = response.json()
        assert data["success"] is False
        assert "旧密码" in data["message"]
    
    def test_student_change_password(self, client, student_user):
        """测试学生修改密码"""
        # 学生登录
        response = client.post("/api/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        assert response.status_code == 200
        
        # 修改密码
        response = client.post("/api/change-password", json={
            "old_password": "student123",
            "new_password": "newstudentpass"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
