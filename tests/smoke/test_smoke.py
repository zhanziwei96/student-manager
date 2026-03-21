"""
冒烟测试 - 核心流程验证

根据 TEST_PLAN.md 第 8 章测试执行计划：
Day 1-2: 冒烟测试（核心流程）

测试项：
1. 服务启动 - 后端/前端/Redis 正常启动
2. 健康检查 - GET /health 返回 healthy
3. 用户登录 - admin 能正常登录系统
4. 学生列表 - 能获取学生列表数据
5. 签到功能 - 能完成一次签到操作
6. 页面导航 - 首页/登录页/管理页能正常访问
"""
import pytest
import requests
from tests.conftest import (
    backend_required, 
    frontend_required, 
    redis_required,
    BASE_URL,
    FRONTEND_URL
)


# =============================================================================
# 1. 服务启动检查
# =============================================================================

class TestServiceStartup:
    """服务启动检查 - 确保所有服务都已启动"""
    
    @pytest.mark.smoke
    @pytest.mark.backend
    def test_backend_service_running(self):
        """测试后端服务是否运行"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200, f"后端返回状态码: {response.status_code}"
            data = response.json()
            assert data.get("status") == "healthy", f"后端状态异常: {data}"
        except requests.exceptions.ConnectionError:
            pytest.fail("后端服务未启动，请运行: cd backend && python main.py")
        except Exception as e:
            pytest.fail(f"后端服务检查失败: {e}")
    
    @pytest.mark.smoke
    @pytest.mark.frontend
    def test_frontend_service_running(self):
        """测试前端服务是否运行"""
        try:
            response = requests.get(FRONTEND_URL, timeout=5)
            assert response.status_code == 200, f"前端返回状态码: {response.status_code}"
            assert "text/html" in response.headers.get("Content-Type", ""), "前端应返回 HTML"
        except requests.exceptions.ConnectionError:
            pytest.fail("前端服务未启动，请运行: cd frontend && pnpm dev")
        except Exception as e:
            pytest.fail(f"前端服务检查失败: {e}")
    
    @pytest.mark.smoke
    @pytest.mark.redis
    def test_redis_service_running(self):
        """测试 Redis 是否运行"""
        try:
            import redis
            r = redis.Redis(host="localhost", port=6379, socket_connect_timeout=5)
            assert r.ping() is True, "Redis ping 失败"
        except ImportError:
            pytest.skip("未安装 redis 包，跳过 Redis 测试")
        except redis.ConnectionError:
            pytest.fail("Redis 未启动，请运行: redis-server")
        except Exception as e:
            pytest.fail(f"Redis 检查失败: {e}")


# =============================================================================
# 2. 健康检查
# =============================================================================

class TestHealthCheck:
    """健康检查端点测试"""
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_health_endpoint(self):
        """测试 /health 端点"""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "healthy"
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert data["checks"]["database"]["status"] == "up"
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_ready_endpoint(self):
        """测试 /ready 端点（Kubernetes 就绪检查）"""
        response = requests.get(f"{BASE_URL}/ready", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "ready"
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_live_endpoint(self):
        """测试 /live 端点（Kubernetes 存活检查）"""
        response = requests.get(f"{BASE_URL}/live", timeout=5)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "alive"


# =============================================================================
# 3. 用户登录
# =============================================================================

class TestUserLogin:
    """用户登录功能测试"""
    
    @pytest.mark.smoke
    @pytest.mark.auth
    @pytest.mark.backend
    @backend_required
    def test_admin_login_success(self):
        """测试 admin 用户正常登录"""
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "admin123"},
            timeout=5
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") is True
        assert "user" in data
        assert data["user"]["username"] == "admin"
        assert "id" in data["user"]
        
        # 验证设置了 session cookie
        assert "session" in response.cookies
    
    @pytest.mark.smoke
    @pytest.mark.auth
    @pytest.mark.backend
    @backend_required
    def test_login_wrong_password(self):
        """测试错误密码登录失败"""
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "wrongpassword"},
            timeout=5
        )
        assert response.status_code == 401
        
        data = response.json()
        assert data.get("success") is False
    
    @pytest.mark.smoke
    @pytest.mark.auth
    @pytest.mark.backend
    @backend_required
    def test_login_nonexistent_user(self):
        """测试不存在的用户登录失败"""
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "nonexistent", "password": "123456"},
            timeout=5
        )
        assert response.status_code == 401


# =============================================================================
# 4. 学生列表
# =============================================================================

class TestStudentList:
    """学生列表功能测试"""
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_get_students_with_auth(self, authenticated_client):
        """测试已认证用户能获取学生列表"""
        response = authenticated_client.get(
            f"{BASE_URL}/api/students",
            timeout=5
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_get_students_without_auth(self):
        """测试未认证用户无法获取学生列表"""
        response = requests.get(
            f"{BASE_URL}/api/students",
            timeout=5
        )
        assert response.status_code == 401


# =============================================================================
# 5. 签到功能
# =============================================================================

class TestCheckin:
    """签到功能测试"""
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_checkin_endpoint_available(self):
        """测试签到端点可访问（可能需要课堂开始）"""
        # 先尝试获取课堂状态
        session_response = requests.get(
            f"{BASE_URL}/api/class-session",
            timeout=5
        )
        
        # 尝试签到（可能失败，但端点应该可用）
        response = requests.post(
            f"{BASE_URL}/api/checkin",
            json={"student_id": "2024001", "name": "测试学生"},
            timeout=5
        )
        
        # 端点应该返回 200 或 400（课堂未开始）或 429（限流）
        # 只要不是 404 或 500，说明端点存在
        assert response.status_code in [200, 400, 429], \
            f"签到端点异常，状态码: {response.status_code}"
    
    @pytest.mark.smoke
    @pytest.mark.backend
    @backend_required
    def test_class_session_endpoint(self):
        """测试课堂状态端点"""
        response = requests.get(
            f"{BASE_URL}/api/class-session",
            timeout=5
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") is True
        assert "data" in data
        assert "active" in data["data"]


# =============================================================================
# 6. 页面导航
# =============================================================================

class TestPageNavigation:
    """前端页面导航测试"""
    
    @pytest.mark.smoke
    @pytest.mark.frontend
    @frontend_required
    def test_homepage_loads(self):
        """测试首页能正常加载"""
        response = requests.get(FRONTEND_URL, timeout=5)
        assert response.status_code == 200
        assert "ClassHub" in response.text or "classhub" in response.text.lower()
    
    @pytest.mark.smoke
    @pytest.mark.frontend
    @frontend_required
    def test_login_page_loads(self):
        """测试登录页能正常加载"""
        # Vue 路由通常是前端路由，直接访问根路径
        response = requests.get(FRONTEND_URL, timeout=5)
        assert response.status_code == 200
        # 检查是否包含 Vue 应用挂载点
        assert "<div id=" in response.text or "<body" in response.text


# =============================================================================
# 冒烟测试汇总报告
# =============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """测试结束后打印汇总报告"""
    terminalreporter.write_sep("=", "冒烟测试汇总")
    
    passed = len(terminalreporter.stats.get("passed", []))
    failed = len(terminalreporter.stats.get("failed", []))
    skipped = len(terminalreporter.stats.get("skipped", []))
    total = passed + failed + skipped
    
    terminalreporter.write_line(f"\n总测试数: {total}")
    terminalreporter.write_line(f"通过: {passed} ✓")
    terminalreporter.write_line(f"失败: {failed} ✗")
    terminalreporter.write_line(f"跳过: {skipped} ⊘")
    
    if failed == 0 and passed > 0:
        terminalreporter.write_line("\n🎉 所有冒烟测试通过！核心流程正常。")
    elif failed > 0:
        terminalreporter.write_line("\n⚠️  部分测试失败，请检查服务状态。")
        terminalreporter.write_line("\n排查建议:")
        terminalreporter.write_line("1. 检查后端: curl http://localhost:8000/health")
        terminalreporter.write_line("2. 检查前端: curl http://localhost:3000")
        terminalreporter.write_line("3. 检查 Redis: redis-cli ping")
        terminalreporter.write_line("4. 查看日志: tail -f backend/backend.log")
    else:
        terminalreporter.write_line("\n⚠️  所有测试都被跳过，请确保服务已启动。")
