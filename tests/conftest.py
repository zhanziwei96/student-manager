"""
Pytest 全局配置和 Fixtures
"""
import sys
import os

# 添加 backend 到 Python 路径（必须在任何其他导入之前）
# 动态检测项目根目录
_current_file = os.path.abspath(__file__)
_project_root = os.path.dirname(os.path.dirname(_current_file))
backend_path = os.path.join(_project_root, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 测试环境变量（必须在任何应用模块导入前设置）
# xdist 并行：每 worker 独立分库（classhub_test_0..3），避免 TRUNCATE 交错
def _worker_suffix() -> str:
    worker = os.environ.get("PYTEST_XDIST_WORKER", "")
    if worker.startswith("gw"):
        return "_" + worker[2:]
    return ""


os.environ['ENV'] = 'testing'
os.environ['RATE_LIMIT__ENABLED'] = 'false'
os.environ['DATABASE__URL'] = (
    'postgresql+psycopg2://classhub:classhub_dev@localhost:5432/classhub_test'
    + _worker_suffix()
)
TEST_DATABASE_URL = os.environ['DATABASE__URL']

import pytest
from typing import Generator
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


def _truncate_all_tables(engine) -> None:
    """清空测试库所有表（PG TRUNCATE，比逐表 DELETE 可靠且自动覆盖新表）"""
    with Session(engine) as s:
        s.execute(text("TRUNCATE %s RESTART IDENTITY CASCADE"
                       % ", ".join(SQLModel.metadata.tables.keys())))
        s.commit()


# PostgreSQL 测试引擎（session 级，函数级清表见 session fixture）
@pytest.fixture(scope="session")
def engine():
    """PG 测试引擎"""
    test_engine = create_engine(TEST_DATABASE_URL, poolclass=StaticPool)
    # 创建所有表
    from app.models import Student, User, CheckinRecord, CourseSession, AuditLog, SecurityAlert, CourseSchedule, DeviceBind
    from app.models.question import Question, Answer  # noqa: F401
    # 先删废弃表（任务/互评已停用，旧测试库残留且 FK 引用 groups，阻止 drop_all）
    with test_engine.begin() as conn:
        conn.execute(text(
            "DROP TABLE IF EXISTS group_evaluation_scores, evaluation_assignments, "
            "group_task_dimensions, group_tasks CASCADE"
        ))
        conn.execute(text(
            "DROP TABLE IF EXISTS student_subject_score_logs, student_subject_scores, "
            "subjects, score_logs CASCADE"
        ))
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)
    try:
        yield test_engine
    finally:
        test_engine.dispose()


@pytest.fixture(scope="function")
def session(engine) -> Generator[Session, None, None]:
    """数据库会话 fixture — 每函数 TRUNCATE 清表 + 清理进程级缓存，保持测试隔离"""
    _truncate_all_tables(engine)
    from app.core.class_cache import invalidate_class_cache
    from app.core.term import invalidate_semester_cache
    invalidate_class_cache()
    invalidate_semester_cache()
    with Session(engine) as session:
        yield session
        # 测试结束后回滚
        session.rollback()


@pytest.fixture
def test_student(session: Session):
    """创建测试学生"""
    from app.models import Student
    from app.core.security import generate_password_hash
    
    password_hash, salt = generate_password_hash("TEST001")
    student = Student(
        student_id="TEST001",
        name="测试学生",
        class_name="测试班级",
        score=80.0,
        password_hash=password_hash,
        salt=salt
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


@pytest.fixture
def test_user(session: Session):
    """创建测试用户（教师）"""
    from app.models import User
    from app.models.constants import UserRoleConst
    from app.core.security import generate_password_hash
    
    password_hash, salt = generate_password_hash("teacher123")
    user = User(
        username="test_teacher",
        name="测试教师",
        password_hash=password_hash,
        salt=salt,
        role=UserRoleConst.TEACHER,
        assigned_classes='["测试班级"]'
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_admin(session: Session):
    """创建测试管理员"""
    from app.models import User
    from app.models.constants import UserRoleConst
    from app.core.security import generate_password_hash
    
    password_hash, salt = generate_password_hash("admin123")
    user = User(
        username="test_admin",
        name="测试管理员",
        password_hash=password_hash,
        salt=salt,
        role=UserRoleConst.ADMIN,
        assigned_classes='[]'
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# 服务配置
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379


class ServiceChecker:
    """服务可用性检查器"""
    
    _backend_available: bool = None
    _frontend_available: bool = None
    _redis_available: bool = None
    
    @classmethod
    def is_backend_available(cls) -> bool:
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


# ========== JWT 集成测试 Fixtures ==========

@pytest.fixture(scope="function")
def jwt_client(monkeypatch, engine):
    """Create a test client with PostgreSQL test database for JWT tests"""
    from fastapi.testclient import TestClient
    from sqlmodel import Session
    from main import app
    import app.core.db as db_module
    from app.api import deps
    from app.api.routes import login, students, users, checkin, system

    # 清空测试库（与 session fixture 同机制）
    _truncate_all_tables(engine)

    # 创建测试用的 get_session
    def get_test_session():
        with Session(engine) as session:
            yield session

    # 猴子补丁替换所有相关模块的 get_session
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "get_session", get_test_session)
    monkeypatch.setattr(deps, "get_session", get_test_session)
    monkeypatch.setattr(login, "get_session", get_test_session)
    monkeypatch.setattr(students, "get_session", get_test_session)
    monkeypatch.setattr(users, "get_session", get_test_session)
    monkeypatch.setattr(checkin, "get_session", get_test_session)
    monkeypatch.setattr(system, "get_session", get_test_session)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def jwt_admin_user(jwt_client):
    """Create admin user for JWT tests"""
    import app.core.db as db_module
    from app.models import User
    from app.core.security import generate_password_hash
    from sqlmodel import Session
    
    with Session(db_module.engine) as session:
        password_hash, _ = generate_password_hash("admin123")
        user = User(
            username="admin",
            password_hash=password_hash,
            salt="",  # bcrypt 不需要外部 salt
            name="Administrator",
            role="admin"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        yield user


@pytest.fixture
def jwt_teacher_user(jwt_client):
    """Create teacher user for JWT tests"""
    import app.core.db as db_module
    from app.models import User
    from app.core.security import generate_password_hash
    from sqlmodel import Session
    
    with Session(db_module.engine) as session:
        password_hash, _ = generate_password_hash("zha123")
        user = User(
            username="zhanziwei",
            password_hash=password_hash,
            salt="",  # bcrypt 不需要外部 salt
            name="Teacher Zhao",
            role="teacher"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        yield user
