"""
Pytest 全局配置和 Fixtures
"""
import pytest
import requests
import redis
import sqlite3
import os
from typing import Optional, Generator
from contextlib import contextmanager

# 服务配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "student_manage.db")

# 测试数据配置
TEST_DATA = {
    "users": [
        {"username": "test_admin", "password": "test123", "name": "测试管理员", "role": "admin"},
        {"username": "test_teacher", "password": "test123", "name": "测试教师", "role": "teacher", "assigned_classes": ["测试1班"]},
    ],
    "students": [
        {"student_id": "TEST001", "name": "测试学生1", "class_name": "测试1班", "score": 80},
        {"student_id": "TEST002", "name": "测试学生2", "class_name": "测试1班", "score": 85},
        {"student_id": "TEST003", "name": "测试学生3", "class_name": "测试2班", "score": 90},
    ],
    "class_name": "测试1班"
}


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


class TestDataManager:
    """测试数据管理器"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.created_students = []
        self.created_users = []
        self.created_checkins = []
    
    def setup_test_data(self) -> dict:
        """
        初始化测试数据
        返回创建的数据信息
        """
        print("\n[测试数据] 开始初始化...")
        
        # 1. 创建测试用户（通过API）
        self._create_test_users()
        
        # 2. 创建测试学生（直接操作数据库，绕过认证）
        self._create_test_students()
        
        print("[测试数据] 初始化完成")
        return {
            "users": TEST_DATA["users"],
            "students": TEST_DATA["students"],
            "class_name": TEST_DATA["class_name"]
        }
    
    def _create_test_users(self):
        """创建测试用户"""
        # 先尝试登录，如果不存在则通过管理员创建
        session = requests.Session()
        
        # 尝试用 admin 登录来创建测试用户
        try:
            login_resp = session.post(
                f"{BASE_URL}/api/login",
                json={"username": "admin", "password": "admin123"},
                timeout=5
            )
            
            if login_resp.status_code == 200:
                # 创建测试用户
                for user in TEST_DATA["users"]:
                    try:
                        resp = session.post(
                            f"{BASE_URL}/api/admin/users",
                            json=user,
                            timeout=5
                        )
                        if resp.status_code in [200, 201]:
                            self.created_users.append(user["username"])
                            print(f"  ✓ 创建用户: {user['username']}")
                        elif resp.status_code == 400 and "已存在" in resp.text:
                            print(f"  ⊘ 用户已存在: {user['username']}")
                            self.created_users.append(user["username"])
                    except Exception as e:
                        print(f"  ✗ 创建用户失败 {user['username']}: {e}")
        except Exception as e:
            print(f"  ⚠ 无法登录admin创建测试用户: {e}")
    
    def _create_test_students(self):
        """直接操作数据库创建测试学生"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for student in TEST_DATA["students"]:
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO students (student_id, name, class_name, score, created_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                        """,
                        (student["student_id"], student["name"], 
                         student["class_name"], student["score"])
                    )
                    if cursor.rowcount > 0:
                        self.created_students.append(student["student_id"])
                        print(f"  ✓ 创建学生: {student['name']} ({student['student_id']})")
                    else:
                        print(f"  ⊘ 学生已存在: {student['name']} ({student['student_id']})")
                        self.created_students.append(student["student_id"])
                except Exception as e:
                    print(f"  ✗ 创建学生失败 {student['student_id']}: {e}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ⚠ 数据库操作失败: {e}")
    
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n[测试数据] 开始清理...")
        
        # 1. 删除测试学生
        self._delete_test_students()
        
        # 2. 删除测试用户
        self._delete_test_users()
        
        # 3. 删除测试签到记录
        self._delete_test_checkins()
        
        # 4. 清理 Redis 缓存
        self._clear_redis_cache()
        
        print("[测试数据] 清理完成")
    
    def _delete_test_students(self):
        """删除测试学生"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for student_id in self.created_students:
                cursor.execute(
                    "DELETE FROM students WHERE student_id = ?",
                    (student_id,)
                )
                if cursor.rowcount > 0:
                    print(f"  ✓ 删除学生: {student_id}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ⚠ 删除学生失败: {e}")
    
    def _delete_test_users(self):
        """删除测试用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for username in self.created_users:
                cursor.execute(
                    "DELETE FROM users WHERE username = ?",
                    (username,)
                )
                if cursor.rowcount > 0:
                    print(f"  ✓ 删除用户: {username}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ⚠ 删除用户失败: {e}")
    
    def _delete_test_checkins(self):
        """删除测试签到记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除测试学生的签到记录
            for student_id in TEST_DATA["students"]:
                cursor.execute(
                    "DELETE FROM checkin_records WHERE student_id = ?",
                    (student_id["student_id"],)
                )
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"  ⚠ 删除签到记录失败: {e}")
    
    def _clear_redis_cache(self):
        """清理 Redis 缓存"""
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            # 删除与测试相关的缓存
            for key in r.scan_iter(match="*test*"):
                r.delete(key)
            for key in r.scan_iter(match="*TEST*"):
                r.delete(key)
            print("  ✓ 清理 Redis 测试缓存")
        except Exception as e:
            print(f"  ⚠ 清理 Redis 缓存失败: {e}")


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


@pytest.fixture(scope="session")
def test_data_manager():
    """测试数据管理器"""
    return TestDataManager()


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_test_data():
    """
    自动初始化和清理测试数据
    在整个测试会话开始前初始化，结束后清理
    """
    manager = TestDataManager()
    
    # 检查服务是否可用
    if not ServiceChecker.is_backend_available():
        print("\n⚠️ 后端服务未运行，跳过测试数据初始化")
        yield None
        return
    
    # 初始化测试数据
    manager.setup_test_data()
    
    yield manager
    
    # 清理测试数据
    manager.cleanup_test_data()


@pytest.fixture(scope="function")
def authenticated_client(api_client):
    """已认证的 API 客户端（使用测试账号）"""
    try:
        # 使用测试管理员账号登录
        response = api_client.post(
            f"{BASE_URL}/api/login",
            json={"username": "test_admin", "password": "test123"},
            timeout=5
        )
        
        if response.status_code == 200:
            return api_client
        else:
            # 尝试用默认 admin 登录
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
    config.addinivalue_line("markers", "data: 测试数据相关")


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
