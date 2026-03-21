"""
Pytest 全局配置和 Fixtures
"""
import pytest
import requests
import redis
from typing import Optional

# 服务配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379


class ServiceChecker:
    """服务可用性检查器"""
    
    _backend_available: Optional[bool] = None
    _frontend_available: Optional[bool] = None
    _redis_available: Optional[bool] = None
    
    @classmethod
    def is_backend_available(cls) -> bool:
        """检查后端服务是否可用"""
        if cls._backend_available is None:
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=2)
                cls._backend_available = response.status_code == 200
            except Exception:
                cls._backend_available = False
        return cls._backend_available
    
    @classmethod
    def is_frontend_available(cls) -> bool:
        """检查前端服务是否可用"""
        if cls._frontend_available is None:
            try:
                response = requests.get(FRONTEND_URL, timeout=2)
                cls._frontend_available = response.status_code == 200
            except Exception:
                cls._frontend_available = False
        return cls._frontend_available
    
    @classmethod
    def is_redis_available(cls) -> bool:
        """检查 Redis 是否可用"""
        if cls._redis_available is None:
            try:
                r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=2)
                r.ping()
                cls._redis_available = True
            except Exception:
                cls._redis_available = False
        return cls._redis_available


@pytest.fixture(scope="session")
def base_url() -> str:
    """后端基础 URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def frontend_url() -> str:
    """前端基础 URL"""
    return FRONTEND_URL


@pytest.fixture(scope="session")
def api_client():
    """API 客户端（带 Session）"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    return session


@pytest.fixture(scope="function")
def authenticated_client(api_client):
    """已认证的 API 客户端"""
    # 尝试登录
    try:
        response = api_client.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            return api_client
    except Exception:
        pass
    
    pytest.skip("无法登录，跳过需要认证的测试")


# pytest 标记
def pytest_configure(config):
    """配置 pytest 标记"""
    config.addinivalue_line("markers", "smoke: 冒烟测试（核心流程）")
    config.addinivalue_line("markers", "backend: 后端服务测试")
    config.addinivalue_line("markers", "frontend: 前端服务测试")
    config.addinivalue_line("markers", "redis: Redis 测试")
    config.addinivalue_line("markers", "auth: 认证相关测试")


# 自定义跳过装饰器
backend_required = pytest.mark.skipif(
    not ServiceChecker.is_backend_available(),
    reason="后端服务未运行，跳过测试"
)

frontend_required = pytest.mark.skipif(
    not ServiceChecker.is_frontend_available(),
    reason="前端服务未运行，跳过测试"
)

redis_required = pytest.mark.skipif(
    not ServiceChecker.is_redis_available(),
    reason="Redis 未运行，跳过测试"
)
