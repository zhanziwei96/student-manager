import sys
import os

# 添加 backend 到 Python 路径（必须在任何其他导入之前）
backend_path = "/home/yufeng/student-manager/backend"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

"""
Pytest 全局配置和 Fixtures
"""
import pytest
import requests
import redis
import sqlite3
from typing import Optional, Generator
from contextlib import contextmanager

# ========== Infrastructure 层 Fixtures ==========

class MockDatabase:
    """模拟 Database 类，使用共享的 SQLite 连接
    
    SQLite :memory: 数据库每个连接都是独立的，
    这个类包装一个共享连接，让 Repository 可以正常使用。
    """
    
    def __init__(self, connection):
        self._conn = connection
    
    def connection(self):
        """返回一个上下文管理器，yield 共享连接"""
        class SharedConnection:
            def __init__(self, conn):
                self._conn = conn
            def __enter__(self):
                return self._conn
            def __exit__(self, *args):
                pass  # 不关闭共享连接
        return SharedConnection(self._conn)
    
    def transaction(self):
        """事务上下文管理器"""
        class SharedTransaction:
            def __init__(self, conn):
                self._conn = conn
            def __enter__(self):
                return self._conn
            def __exit__(self, exc_type, *args):
                if exc_type is None:
                    self._conn.commit()
                else:
                    self._conn.rollback()
        return SharedTransaction(self._conn)


@pytest.fixture
def db():
    """内存数据库 fixture（用于单元测试）"""
    import sqlite3
    
    # 创建一个共享连接用于内存数据库
    shared_conn = sqlite3.connect(":memory:")
    shared_conn.row_factory = sqlite3.Row
    
    # 创建表
    cursor = shared_conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class_name TEXT DEFAULT '未分班',
            score REAL DEFAULT 70.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'teacher',
            assigned_class TEXT,
            is_active INTEGER DEFAULT 1,
            login_fail_count INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            last_login_ip TEXT,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            student_name TEXT,
            class_name TEXT,
            checkin_type TEXT DEFAULT 'self',
            checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS score_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            old_score REAL,
            new_score REAL,
            delta REAL,
            reason TEXT,
            operator TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    shared_conn.commit()
    
    return MockDatabase(shared_conn)


@pytest.fixture
def student_repo(db):
    """学生仓储 fixture"""
    from infrastructure.persistence.repositories.sqlite_student_repository import SQLiteStudentRepository
    return SQLiteStudentRepository(db)


@pytest.fixture
def user_repo(db):
    """用户仓储 fixture"""
    from infrastructure.persistence.repositories.sqlite_user_repository import SQLiteUserRepository
    return SQLiteUserRepository(db)


@pytest.fixture
def checkin_repo(db):
    """签到仓储 fixture"""
    from infrastructure.persistence.repositories.sqlite_checkin_repository import SQLiteCheckinRepository
    return SQLiteCheckinRepository(db)


@pytest.fixture
def score_log_repo(db):
    """分数日志仓储 fixture"""
    from infrastructure.persistence.repositories.sqlite_score_log_repository import SQLiteScoreLogRepository
    return SQLiteScoreLogRepository(db)


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
                import requests
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
                import requests
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
                import redis
                r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_connect_timeout=2)
                r.ping()
                cls._redis_available = True
            except Exception:
                cls._redis_available = False
        return cls._redis_available


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
