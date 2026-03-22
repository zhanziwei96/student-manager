"""
JWT 工具单元测试
"""
import pytest
from datetime import timedelta
from jose import jwt

from app.core.jwt import (
    create_access_token,
    decode_token,
    SECRET_KEY,
    ALGORITHM,
    COOKIE_NAME,
    get_token_from_cookie
)


class TestJWT:
    """JWT 功能测试"""
    
    def test_create_token(self):
        """测试创建 Token"""
        data = {"sub": "123", "username": "testuser", "role": "admin"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        # 验证是有效的 JWT 格式（三部分，用点分隔）
        parts = token.split('.')
        assert len(parts) == 3
    
    def test_decode_valid_token(self):
        """测试解码有效 Token"""
        data = {"sub": "123", "username": "testuser", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "123"
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "admin"
    
    def test_decode_invalid_token(self):
        """测试解码无效 Token"""
        decoded = decode_token("invalid.token.here")
        assert decoded is None
    
    def test_decode_malformed_token(self):
        """测试解码格式错误的 Token"""
        decoded = decode_token("not.a.valid.token")
        assert decoded is None
    
    def test_token_expiration(self):
        """测试 Token 过期"""
        data = {"sub": "123"}
        # 创建已过期 Token
        expired_token = create_access_token(
            data, 
            expires_delta=timedelta(minutes=-1)
        )
        decoded = decode_token(expired_token)
        # 过期 Token 应该返回 None
        assert decoded is None
    
    def test_token_with_custom_expires(self):
        """测试自定义过期时间"""
        data = {"sub": "123"}
        token = create_access_token(
            data,
            expires_delta=timedelta(hours=2)
        )
        decoded = decode_token(token)
        
        assert decoded is not None
        assert "exp" in decoded
    
    def test_token_contains_all_data(self):
        """测试 Token 包含所有传入数据"""
        data = {
            "sub": "456",
            "username": "teacher1",
            "role": "teacher",
            "is_admin": False,
            "extra_field": "extra_value"
        }
        token = create_access_token(data)
        decoded = decode_token(token)
        
        for key, value in data.items():
            assert decoded[key] == value


class TestJWTCookie:
    """JWT Cookie 操作测试"""
    
    def test_cookie_name_constant(self):
        """测试 Cookie 名称常量"""
        assert COOKIE_NAME == "access_token"
    
    def test_get_token_from_cookie_exists(self):
        """测试从请求中获取存在的 Cookie"""
        class MockRequest:
            def __init__(self):
                self.cookies = {COOKIE_NAME: "test_token_value"}
        
        request = MockRequest()
        token = get_token_from_cookie(request)
        assert token == "test_token_value"
    
    def test_get_token_from_cookie_not_exists(self):
        """测试从请求中获取不存在的 Cookie"""
        class MockRequest:
            def __init__(self):
                self.cookies = {}
        
        request = MockRequest()
        token = get_token_from_cookie(request)
        assert token is None
    
    def test_get_token_from_cookie_other_cookies(self):
        """测试存在其他 Cookie 但无 access_token"""
        class MockRequest:
            def __init__(self):
                self.cookies = {"other_cookie": "value", "session": "abc"}
        
        request = MockRequest()
        token = get_token_from_cookie(request)
        assert token is None
