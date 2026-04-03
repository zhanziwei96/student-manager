"""
单元测试配置和夹具
"""
import pytest
import os
import sys

# 设置测试环境
os.environ['ENV'] = 'testing'
os.environ['RATE_LIMIT__ENABLED'] = 'false'  # 禁用限流

# 确保 backend 在路径中
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


@pytest.fixture
def client():
    """创建测试客户端"""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)
