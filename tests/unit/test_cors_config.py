"""
测试CORS配置 - SEC-005: CORS安全策略
"""
import pytest
from fastapi.testclient import TestClient


class TestCORSConfig:
    """测试CORS中间件配置"""

    def test_cors_preflight_request(self, client):
        """测试CORS预检请求响应"""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            }
        )

        assert response.status_code == 200
        # 验证允许的源
        assert "http://localhost:3000" in response.headers.get("access-control-allow-origin", "")
        # 验证允许的方法
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "GET" in allow_methods
        assert "POST" in allow_methods
        assert "PUT" in allow_methods
        assert "DELETE" in allow_methods
        # 验证允许的请求头
        allow_headers = response.headers.get("access-control-allow-headers", "").lower()
        assert "authorization" in allow_headers
        assert "content-type" in allow_headers

    def test_cors_not_allow_wildcard_origin_with_credentials(self, client):
        """测试不允许通配符源配合credentials"""
        response = client.get(
            "/health",
            headers={"Origin": "http://unknown-origin.com"}
        )

        # 对于未知源，应该不在允许列表中
        # 具体行为取决于配置，但不应该允许任意源
        allow_origin = response.headers.get("access-control-allow-origin", "")
        # 只允许配置的源，不是通配符
        assert allow_origin != "*"

    def test_cors_simple_request(self, client):
        """测试简单CORS请求"""
        response = client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
            }
        )

        assert response.status_code == 200
        assert "http://localhost:3000" in response.headers.get("access-control-allow-origin", "")
        # 验证允许携带凭证
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_cors_expose_headers(self, client):
        """测试暴露的响应头"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        expose_headers = response.headers.get("access-control-expose-headers", "")
        assert "X-Request-ID" in expose_headers

    def test_cors_disallowed_methods(self, client):
        """测试不允许的HTTP方法"""
        # PATCH 方法不在白名单中
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "PATCH",
            }
        )

        # 预检请求应该成功，但PATCH不应该在允许的方法中
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "PATCH" not in allow_methods.upper()

    def test_cors_max_age_cache(self, client):
        """测试预检请求缓存时间"""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # 验证缓存时间设置
        max_age = response.headers.get("access-control-max-age")
        assert max_age is not None
        assert int(max_age) == 600  # 10分钟
