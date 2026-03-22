"""
JWT 依赖注入测试
"""
import pytest
from fastapi import HTTPException

from app.core.jwt import (
    get_current_user,
    require_login,
    require_admin,
    create_access_token,
    COOKIE_NAME
)


class MockRequest:
    """模拟请求对象"""
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


class TestGetCurrentUser:
    """测试 get_current_user 依赖"""
    
    @pytest.mark.asyncio
    async def test_no_token(self):
        """测试无 Token 时抛出 401"""
        request = MockRequest(cookies={})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        
        assert exc_info.value.status_code == 401
        assert "未登录" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_valid_token(self):
        """测试有效 Token"""
        token_data = {
            "sub": "123",
            "username": "testuser",
            "role": "admin",
            "is_admin": True
        }
        token = create_access_token(token_data)
        request = MockRequest(cookies={COOKIE_NAME: token})
        
        user = await get_current_user(request)
        
        assert user is not None
        assert user["sub"] == "123"
        assert user["username"] == "testuser"
        assert user["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """测试无效 Token"""
        request = MockRequest(cookies={COOKIE_NAME: "invalid.token"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        
        assert exc_info.value.status_code == 401
        assert "登录已过期" in exc_info.value.detail


class TestRequireLogin:
    """测试 require_login 依赖"""
    
    @pytest.mark.asyncio
    async def test_require_login_success(self):
        """测试正常获取用户ID"""
        token_data = {"sub": "456", "role": "teacher"}
        token = create_access_token(token_data)
        request = MockRequest(cookies={COOKIE_NAME: token})
        
        user_id = await require_login(request)
        
        assert user_id == "456"
    
    @pytest.mark.asyncio
    async def test_require_login_no_sub(self):
        """测试 Token 中没有 sub 字段"""
        # 创建一个没有 sub 的 token
        token = create_access_token({"role": "admin"})
        request = MockRequest(cookies={COOKIE_NAME: token})
        
        with pytest.raises(HTTPException) as exc_info:
            await require_login(request)
        
        assert exc_info.value.status_code == 401


class TestRequireAdmin:
    """测试 require_admin 依赖"""
    
    @pytest.mark.asyncio
    async def test_admin_success(self):
        """测试管理员权限检查通过"""
        token_data = {
            "sub": "1",
            "role": "admin",
            "is_admin": True
        }
        token = create_access_token(token_data)
        request = MockRequest(cookies={COOKIE_NAME: token})
        
        user_id = await require_admin(request)
        
        assert user_id == "1"
    
    @pytest.mark.asyncio
    async def test_not_admin(self):
        """测试非管理员被禁止"""
        token_data = {
            "sub": "2",
            "role": "teacher",
            "is_admin": False
        }
        token = create_access_token(token_data)
        request = MockRequest(cookies={COOKIE_NAME: token})
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(request)
        
        assert exc_info.value.status_code == 403
        assert "需要管理员权限" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_admin_no_is_admin_field(self):
        """测试 Token 中没有 is_admin 字段"""
        token_data = {"sub": "3", "role": "admin"}  # 没有 is_admin
        token = create_access_token(token_data)
        request = MockRequest(cookies={COOKIE_NAME: token})
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(request)
        
        assert exc_info.value.status_code == 403
