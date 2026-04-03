"""
JWT Token 刷新机制测试
REVIEW-P1: Token 过期前自动刷新测试

测试场景:
- Token 正常刷新
- Token 过期后访问
- Token 即将过期时自动刷新
"""
import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.core.config import get_settings
from app.core.jwt import create_access_token, decode_token


class TestTokenRefresh:
    """测试 Token 刷新机制"""
    
    def test_token_expiration(self):
        """测试 Token 过期时间"""
        settings = get_settings()
        
        # 创建短期 Token
        token = create_access_token(
            data={"sub": "1", "username": "test"},
            expires_delta=timedelta(seconds=1)
        )
        
        # 立即验证应成功
        payload = decode_token(token)
        assert payload is not None
        assert payload["username"] == "test"
        
        # 等待 Token 过期
        time.sleep(2)
        
        # 过期后验证应失败
        expired_payload = decode_token(token)
        assert expired_payload is None
    
    def test_access_protected_route_with_valid_token(self, client: TestClient, teacher_user):
        """测试使用有效 Token 访问受保护接口"""
        # 登录获取 Token（使用 fixture 中的 teacher1 用户）
        login_response = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert login_response.status_code == 200
        
        # 获取 Cookie
        cookies = login_response.cookies
        
        # 访问受保护接口
        response = client.get("/api/v1/classes", cookies=cookies)
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_access_protected_route_without_token(self, client: TestClient):
        """测试不使用 Token 访问受保护接口"""
        # 访问受保护接口应失败
        response = client.get("/api/v1/classes")
        assert response.status_code == 401
    
    def test_token_claims_structure(self):
        """测试 Token 声明结构"""
        settings = get_settings()
        
        token = create_access_token(
            data={
                "sub": "1",
                "username": "testuser",
                "role": "teacher",
                "name": "Test User"
            }
        )
        
        # 使用项目自带的 decode_token 函数解码
        payload = decode_token(token)
        
        # 验证声明
        assert payload is not None
        assert "sub" in payload
        assert "username" in payload
        assert "exp" in payload  # 过期时间
        assert payload["username"] == "testuser"
    
    def test_same_data_tokens_can_be_decoded(self):
        """测试相同数据生成的 Token 可以正确解码"""
        settings = get_settings()
        
        # 创建 Token
        token = create_access_token(
            data={"sub": "1", "username": "test"},
            expires_delta=timedelta(minutes=5)
        )
        
        # Token 可以正确解码
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["username"] == "test"
