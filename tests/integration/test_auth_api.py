"""
认证 API 集成测试
"""
import pytest
from sqlmodel import Session


class TestLoginAPI:
    """登录 API 测试"""
    
    def test_login_success_admin(self, client, admin_user):
        """管理员登录成功"""
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "登录成功"
        assert data["data"]["username"] == "admin"
        assert data["data"]["role"] == "admin"
    
    def test_login_success_teacher(self, client, teacher_user):
        """教师登录成功"""
        response = client.post("/api/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "teacher1"
        assert data["data"]["role"] == "teacher"
    
    def test_login_success_student(self, client, student_user):
        """学生登录成功"""
        response = client.post("/api/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == "S001"
        assert data["data"]["role"] == "student"
    
    def test_login_wrong_password(self, client, admin_user):
        """密码错误"""
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "wrongpassword",
            "role": "admin"
        })
        
        assert response.status_code == 401
        assert "密码错误" in response.json()["message"]
    
    def test_login_user_not_found(self, client):
        """用户不存在"""
        response = client.post("/api/login", json={
            "username": "nonexistent",
            "password": "password123",
            "role": "admin"
        })
        
        assert response.status_code == 401
    
    def test_login_wrong_role(self, client, admin_user):
        """角色不匹配"""
        response = client.post("/api/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "teacher"
        })
        
        assert response.status_code == 401


class TestLogoutAPI:
    """登出 API 测试"""
    
    def test_logout_success(self, admin_client):
        """登出成功"""
        response = admin_client.post("/api/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "登出成功"


class TestCurrentUserAPI:
    """当前用户 API 测试"""
    
    def test_get_current_user_admin(self, admin_client, admin_user):
        """获取当前管理员信息"""
        response = admin_client.get("/api/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "admin"
        assert data["data"]["is_admin"] is True
    
    def test_get_current_user_teacher(self, teacher_client, teacher_user):
        """获取当前教师信息"""
        response = teacher_client.get("/api/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "teacher1"
        assert data["data"]["role"] == "teacher"
    
    def test_get_current_user_unauthorized(self, client):
        """未登录访问"""
        response = client.get("/api/me")
        
        assert response.status_code == 401


class TestChangePasswordAPI:
    """修改密码 API 测试"""
    
    def test_change_password_success(self, admin_client, admin_user, test_engine):
        """修改密码成功"""
        response = admin_client.post("/api/change-password", json={
            "old_password": "admin123",
            "new_password": "newpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "密码修改成功"
        
        # 验证新密码可以登录
        from app.core.security import verify_password_hash
        with Session(test_engine) as session:
            session.add(admin_user)
            session.refresh(admin_user)
            assert verify_password_hash("newpass123", admin_user.password_hash, admin_user.salt)
    
    def test_change_password_wrong_old(self, admin_client):
        """旧密码错误"""
        response = admin_client.post("/api/change-password", json={
            "old_password": "wrongpassword",
            "new_password": "newpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "旧密码错误"
    
    def test_change_password_unauthorized(self, client):
        """未登录修改密码"""
        response = client.post("/api/change-password", json={
            "old_password": "oldpass",
            "new_password": "newpass123"
        })
        
        assert response.status_code == 401


class TestAccountLockout:
    """账号锁定测试"""
    
    def test_account_lock_after_max_failures(self, client, admin_user, test_engine):
        """多次失败后账号锁定"""
        # 连续失败登录（假设最大失败次数为10）
        for i in range(10):
            response = client.post("/api/login", json={
                "username": "admin",
                "password": "wrongpassword",
                "role": "admin"
            })
            if i < 9:
                assert response.status_code == 401
        
        # 第10次应该被锁定
        assert response.status_code == 403
        assert "锁定" in response.json()["message"]
