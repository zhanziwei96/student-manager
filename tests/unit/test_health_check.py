"""
测试增强健康检查 - P2-3: 健康检查增强

测试内容：
- 基础健康检查 /health
- 增强健康检查 /health/detailed
- 依赖状态检查（数据库、文件系统、磁盘空间）
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestHealthCheckBasic:
    """基础健康检查测试 - 使用 FastAPI TestClient"""

    def test_health_check_basic(self):
        """测试基础健康检查端点"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["version"] == "2.0.0"


class TestHealthCheckDetailed:
    """增强健康检查测试"""

    def test_health_check_detailed_structure(self):
        """测试增强健康检查响应结构"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "dependencies" in data

        # 验证依赖项列表
        deps = data["dependencies"]
        assert len(deps) == 3

        # 验证每个依赖项的结构
        dep_names = [d["name"] for d in deps]
        assert "database" in dep_names
        assert "filesystem" in dep_names
        assert "disk_space" in dep_names

    def test_health_check_dependencies_structure(self):
        """测试依赖状态项结构"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/v1/health/detailed")
        data = response.json()

        for dep in data["dependencies"]:
            assert "name" in dep
            assert "status" in dep
            assert "response_time_ms" in dep
            assert "message" in dep
            assert dep["status"] in ["healthy", "unhealthy", "warning"]
            assert isinstance(dep["response_time_ms"], float)

    def test_health_check_healthy_status(self):
        """测试所有依赖健康时的状态"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/v1/health/detailed")
        data = response.json()

        # 所有关键依赖都健康时，整体状态应为 healthy
        critical_deps = ["database", "filesystem"]
        critical_statuses = [
            d for d in data["dependencies"]
            if d["name"] in critical_deps
        ]

        all_healthy = all(d["status"] == "healthy" for d in critical_statuses)

        if all_healthy:
            assert data["status"] in ["healthy", "degraded"]

    def test_health_check_uptime(self):
        """测试运行时间字段"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/v1/health/detailed")
        data = response.json()

        # 运行时间应为正数
        assert data["uptime_seconds"] >= 0


class TestDatabaseHealth:
    """数据库健康检查测试"""

    def test_database_health_check_function(self):
        """测试数据库健康检查函数"""
        from app.api.routes.system import _check_database_health

        result = _check_database_health()

        assert result.name == "database"
        assert result.status == "healthy"
        assert "数据库连接正常" in result.message
        assert result.response_time_ms >= 0

    def test_database_health_check_failure(self):
        """测试数据库健康检查失败情况"""
        from app.api.routes.system import _check_database_health
        from sqlalchemy import text

        # 模拟数据库连接失败
        with patch('app.api.routes.system.engine') as mock_engine:
            mock_engine.connect.side_effect = Exception("Connection refused")

            result = _check_database_health()

            assert result.name == "database"
            assert result.status == "unhealthy"
            assert "数据库连接失败" in result.message


class TestFilesystemHealth:
    """文件系统健康检查测试"""

    def test_filesystem_health_check_function(self):
        """测试文件系统健康检查函数"""
        from app.api.routes.system import _check_filesystem_health

        result = _check_filesystem_health()

        assert result.name == "filesystem"
        assert result.status == "healthy"
        assert "文件系统可写" in result.message
        assert result.response_time_ms >= 0

    def test_filesystem_health_check_failure(self):
        """测试文件系统健康检查失败情况"""
        from app.api.routes.system import _check_filesystem_health

        # 模拟文件系统不可写
        with patch('app.api.routes.system.Path') as mock_path_class:
            mock_path = MagicMock()
            mock_path.parent.__truediv__ = MagicMock(return_value=mock_path)
            mock_path.write_text.side_effect = PermissionError("Permission denied")
            mock_path_class.return_value = mock_path

            result = _check_filesystem_health()

            assert result.name == "filesystem"
            assert result.status == "unhealthy"


class TestDiskSpaceHealth:
    """磁盘空间健康检查测试"""

    def test_disk_space_health_check_function(self):
        """测试磁盘空间健康检查函数"""
        from app.api.routes.system import _check_disk_space

        result = _check_disk_space()

        assert result.name == "disk_space"
        assert result.status in ["healthy", "warning"]
        assert "磁盘空间" in result.message
        assert result.response_time_ms >= 0

    def test_disk_space_warning(self):
        """测试磁盘空间不足警告"""
        from app.api.routes.system import _check_disk_space
        import shutil

        # 模拟磁盘空间不足
        mock_stat = MagicMock()
        mock_stat.free = 500 * 1024 * 1024  # 500MB
        mock_stat.total = 1000 * 1024 * 1024  # 1GB
        mock_stat.used = 500 * 1024 * 1024

        with patch.object(shutil, 'disk_usage', return_value=mock_stat):
            result = _check_disk_space()

            assert result.name == "disk_space"
            assert result.status == "warning"
            assert "磁盘空间不足" in result.message


class TestHealthCheckIntegration:
    """健康检查集成测试"""

    def test_health_check_response_time(self):
        """测试健康检查响应时间"""
        import time
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        start = time.time()
        response = client.get("/api/v1/health/detailed")
        elapsed = time.time() - start

        assert response.status_code == 200
        # 健康检查应在 1 秒内完成
        assert elapsed < 1.0

    def test_health_check_consistency(self):
        """测试健康检查结果一致性"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        # 连续调用多次，检查结果一致
        responses = []
        for _ in range(3):
            response = client.get("/api/v1/health/detailed")
            responses.append(response.json())

        # 所有响应的结构应一致
        for resp in responses:
            assert "status" in resp
            assert "dependencies" in resp
            assert len(resp["dependencies"]) == 3
