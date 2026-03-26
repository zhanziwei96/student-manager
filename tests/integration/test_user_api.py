"""
用户管理 API 集成测试（管理员功能）
"""
import pytest
from sqlmodel import Session


class TestUserListAPI:
    """用户列表 API 测试"""
    
    def test_list_users_admin(self, admin_client, admin_user, teacher_user):
        """管理员获取用户列表"""
        response = admin_client.get("/api/admin/users")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
    
    def test_list_users_filter_by_role(self, admin_client, admin_user, teacher_user):
        """按角色筛选用户"""
        response = admin_client.get("/api/admin/users?role=teacher")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["username"] == "teacher1"
    
    def test_list_users_teacher_forbidden(self, teacher_client):
        """教师无权访问用户列表"""
        response = teacher_client.get("/api/admin/users")
        
        assert response.status_code == 403
    
    def test_list_users_unauthorized(self, client):
        """未授权访问"""
        response = client.get("/api/admin/users")
        
        assert response.status_code == 401


class TestUserCreateAPI:
    """用户创建 API 测试"""
    
    def test_create_user_success(self, admin_client):
        """成功创建用户"""
        response = admin_client.post("/api/admin/users", json={
            "username": "newteacher",
            "password": "password123",
            "name": "新教师",
            "role": "teacher",
            "assigned_classes": ["三班", "四班"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "用户创建成功"
        assert data["data"]["username"] == "newteacher"
        assert data["data"]["role"] == "teacher"
    
    def test_create_user_duplicate_username(self, admin_client, admin_user):
        """用户名重复"""
        response = admin_client.post("/api/admin/users", json={
            "username": "admin",
            "password": "password123",
            "name": "重复用户",
            "role": "teacher"
        })
        
        assert response.status_code == 409
        assert "用户名已存在" in response.json()["message"]
    
    def test_create_user_validation_error(self, admin_client):
        """参数验证错误"""
        response = admin_client.post("/api/admin/users", json={
            "username": "ab",  # 太短
            "password": "123",  # 太短
            "name": "测试"
        })
        
        assert response.status_code == 422
    
    def test_create_user_default_role(self, admin_client):
        """默认角色为教师"""
        response = admin_client.post("/api/admin/users", json={
            "username": "defaultteacher",
            "password": "password123",
            "name": "默认教师"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role"] == "teacher"


class TestUserUpdateAPI:
    """用户更新 API 测试"""
    
    def test_update_user_success(self, admin_client, teacher_user):
        """成功更新用户"""
        response = admin_client.put(f"/api/admin/users/{teacher_user.id}", json={
            "name": "更新的教师名",
            "assigned_classes": ["五班"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "用户更新成功"
        assert data["data"]["name"] == "更新的教师名"
    
    def test_update_user_not_found(self, admin_client):
        """用户不存在"""
        response = admin_client.put("/api/admin/users/9999", json={
            "name": "不存在的用户"
        })
        
        assert response.status_code == 404
    
    def test_update_user_role(self, admin_client, teacher_user):
        """更新用户角色"""
        response = admin_client.put(f"/api/admin/users/{teacher_user.id}", json={
            "role": "admin"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role"] == "admin"


class TestResetPasswordAPI:
    """重置密码 API 测试"""
    
    def test_reset_password_success(self, admin_client, teacher_user, test_engine):
        """成功重置密码"""
        response = admin_client.put(f"/api/admin/users/{teacher_user.id}/reset-password", json={
            "new_password": "resetpass123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "密码重置成功"
        
        # 验证新密码可以登录 (SEC-003: 使用新的 verify_password 接口)
        from app.core.security import verify_password
        with Session(test_engine) as session:
            session.add(teacher_user)
            session.refresh(teacher_user)
            assert verify_password("resetpass123", teacher_user.password_hash)
    
    def test_reset_password_user_not_found(self, admin_client):
        """用户不存在"""
        response = admin_client.put("/api/admin/users/9999/reset-password", json={
            "new_password": "newpass123"
        })
        
        assert response.status_code == 404
    
    def test_reset_password_validation_error(self, admin_client, teacher_user):
        """密码太短"""
        response = admin_client.put(f"/api/admin/users/{teacher_user.id}/reset-password", json={
            "new_password": "123"  # 太短
        })
        
        assert response.status_code == 422


class TestDeleteUserAPI:
    """删除用户 API 测试"""
    
    def test_delete_user_success(self, admin_client, teacher_user):
        """成功删除用户"""
        response = admin_client.delete(f"/api/admin/users/{teacher_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "用户删除成功"
        
        # 验证已删除
        list_response = admin_client.get("/api/admin/users")
        users = list_response.json()["data"]
        assert not any(u["id"] == teacher_user.id for u in users)
    
    def test_delete_user_not_found(self, admin_client):
        """用户不存在"""
        response = admin_client.delete("/api/admin/users/9999")
        
        assert response.status_code == 404
    
    def test_delete_self_forbidden(self, admin_client, admin_user):
        """不能删除自己"""
        response = admin_client.delete(f"/api/admin/users/{admin_user.id}")
        
        assert response.status_code == 400
        assert "不能删除当前登录账号" in response.json()["message"]
    
    def test_delete_user_teacher_forbidden(self, teacher_client, admin_user):
        """教师无权删除用户"""
        response = teacher_client.delete(f"/api/admin/users/{admin_user.id}")
        
        assert response.status_code == 403


class TestUserPermissions:
    """用户权限测试"""
    
    def test_teacher_cannot_create_user(self, teacher_client):
        """教师不能创建用户"""
        response = teacher_client.post("/api/admin/users", json={
            "username": "newuser",
            "password": "password123",
            "name": "新用户"
        })
        
        assert response.status_code == 403
    
    def test_teacher_cannot_update_user(self, teacher_client, admin_user):
        """教师不能更新用户"""
        response = teacher_client.put(f"/api/admin/users/{admin_user.id}", json={
            "name": "试图修改"
        })
        
        assert response.status_code == 403
    
    def test_teacher_cannot_reset_password(self, teacher_client, admin_user):
        """教师不能重置密码"""
        response = teacher_client.put(f"/api/admin/users/{admin_user.id}/reset-password", json={
            "new_password": "newpass123"
        })
        
        assert response.status_code == 403
