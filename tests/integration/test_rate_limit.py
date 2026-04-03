"""
限流功能集成测试

注意：限流在测试环境中默认禁用 (RATE_LIMIT__ENABLED=false)
这些测试主要验证限流相关代码路径和 HTTP 状态码语义
"""
import pytest
from unittest.mock import patch

pytestmark = pytest.mark.integration


class TestRateLimitHttpSemantics:
    """测试限流 HTTP 语义正确性 - 验证状态码 429 被正确使用"""
    
    def test_rate_limit_returns_429_not_503(self, client):
        """
        测试限流返回 429 而不是 503
        
        通过 mock check_rate_limit 返回 False 来模拟限流触发
        """
        # Mock check_rate_limit 返回 False 模拟限流触发
        with patch("app.api.routes.login.check_rate_limit", return_value=False):
            response = client.post("/api/v1/login", json={
                "username": "rate_limit_test_user",
                "password": "wrong_password",
                "role": "teacher"
            })
            
            # 必须是 429，不能是 503
            assert response.status_code == 429, f"限流应返回 429，实际返回 {response.status_code}"
            
            # 响应体应包含限流提示（统一 API 格式使用 message 字段）
            data = response.json()
            assert "message" in data
            assert "请求过于频繁" in data.get("message", "")
    
    def test_rate_limit_disabled_allows_request(self, client):
        """
        测试限流禁用时请求正常通过（到达密码验证阶段）
        """
        # 限流禁用（默认状态），请求应该到达密码验证阶段（401 表示密码错误）
        response = client.post("/api/v1/login", json={
            "username": "nonexistent_user",
            "password": "wrong_password",
            "role": "teacher"
        })
        
        # 不是 429（限流未触发），应该是 401（密码错误）或 404（用户不存在）
        assert response.status_code != 429
        assert response.status_code in [401, 404]


class TestRateLimitConfig:
    """测试限流配置"""
    
    def test_http_status_has_too_many_requests(self):
        """测试 HttpStatus 类包含 TOO_MANY_REQUESTS (429)"""
        from app.core.config import HttpStatus
        
        assert hasattr(HttpStatus, "TOO_MANY_REQUESTS")
        assert HttpStatus.TOO_MANY_REQUESTS == 429
    
    def test_rate_limit_settings_structure(self):
        """测试限流配置结构"""
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # 检查限流配置存在
        assert hasattr(settings, "rate_limit")
        assert hasattr(settings.rate_limit, "enabled")
        assert hasattr(settings.rate_limit, "login_max_requests")
        assert hasattr(settings.rate_limit, "login_window_seconds")
