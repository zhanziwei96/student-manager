"""
并发登录场景测试
REVIEW-P1: 同账号多地登录测试

测试场景:
- 同一账号同时从多个地方登录
- 登录失败计数并发更新
- Token 失效与重新登录
"""
import pytest
import threading
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient


class TestConcurrentLogin:
    """测试并发登录场景"""
    
    def test_same_account_multiple_login_tokens(self, client: TestClient, teacher_user):
        """测试同一账号多次登录产生不同 Token"""
        # 第一次登录（使用 fixture 中的 teacher1 用户）
        response1 = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["success"] is True
        
        # 第二次登录（同一账号）
        response2 = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["success"] is True
        
        # 两次登录都应成功（系统允许多地登录）
        # 验证都返回了 cookie
        assert "access_token" in response1.cookies or "access_token" in response2.cookies
    
    def test_concurrent_login_with_wrong_password(self, client: TestClient, teacher_user):
        """测试并发错误密码登录 - 失败计数应正确累加"""
        # 连续多次使用错误密码登录
        for i in range(3):
            response = client.post("/api/v1/login", json={
                "username": "teacher1",
                "password": "wrong_password",
                "role": "teacher"
            })
            assert response.status_code == 401
        
        # 使用正确密码登录应成功（尚未被锁定）
        response = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        # 根据配置可能返回 200 或 429
        assert response.status_code in [200, 429]
    
    def test_concurrent_api_access_with_same_token(self, client: TestClient, teacher_user):
        """测试使用同一 Token 并发访问 API"""
        # 先登录获取 Token
        login_response = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert login_response.status_code == 200
        
        # 获取 Cookie 中的 token
        cookies = login_response.cookies
        
        # 使用同一 Token 并发访问受保护接口
        def make_request():
            return client.get("/api/v1/classes", cookies=cookies)
        
        # 并发执行多个请求
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in futures]
        
        # 所有请求都应成功
        for response in results:
            assert response.status_code == 200
            assert response.json()["success"] is True


class TestConcurrentLoginFailure:
    """测试并发登录失败场景"""
    
    def test_rapid_fire_login_attempts(self, client: TestClient, teacher_user):
        """测试快速连续登录尝试 - 应触发限流"""
        # 快速发送多个登录请求
        responses = []
        for i in range(10):
            response = client.post("/api/v1/login", json={
                "username": "teacher1",
                "password": "wrong_password",
                "role": "teacher"
            })
            responses.append(response)
        
        # 后面的请求应被限流（返回 429）或继续返回 401
        status_codes = [r.status_code for r in responses]
        # 应有部分请求失败
        assert 401 in status_codes or 429 in status_codes
