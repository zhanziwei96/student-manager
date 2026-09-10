"""
用户模型单元测试
"""
import pytest
from datetime import datetime
from app.models import User, UserCreate, UserUpdate
from app.core.security import generate_password_hash


class TestUserModel:
    """测试用户模型"""
    
    def test_user_creation(self):
        """测试创建用户"""
        password_hash, salt = generate_password_hash("password123")
        
        user = User(
            username="teacher1",
            name="教师1",
            password_hash=password_hash,
            salt=salt,
            role="teacher"
        )
        
        assert user.username == "teacher1"
        assert user.name == "教师1"
        assert user.role == "teacher"
        assert user.is_account_enabled is True
        assert user.login_fail_count == 0
    
    def test_user_is_admin(self):
        """测试管理员判断"""
        password_hash, salt = generate_password_hash("password123")
        
        admin = User(
            username="admin1",
            name="管理员",
            password_hash=password_hash,
            salt=salt,
            role="admin"
        )
        assert admin.is_admin() is True
        
        teacher = User(
            username="teacher2",
            name="教师2",
            password_hash=password_hash,
            salt=salt,
            role="teacher"
        )
        assert teacher.is_admin() is False
    
    def test_user_default_values(self):
        """测试用户默认值"""
        password_hash, salt = generate_password_hash("password123")
        
        user = User(
            username="teacher3",
            name="教师3",
            password_hash=password_hash,
            salt=salt
        )
        
        assert user.role == "teacher"
        assert user.is_account_enabled is True
        assert user.created_at is not None


class TestUserSchemas:
    """测试用户 Schema"""
    
    def test_user_create(self):
        """测试创建用户请求"""
        data = UserCreate(
            username="new_user",
            password="password123",
            name="新用户",
            role="teacher",
                    )
        
        assert data.username == "new_user"
            
    def test_user_update(self):
        """测试更新用户请求"""
        data = UserUpdate(name="新名称")
        assert data.name == "新名称"
        assert data.role is None
