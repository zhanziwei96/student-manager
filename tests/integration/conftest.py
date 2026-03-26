"""
集成测试配置和夹具
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

# 关键：在导入任何应用模块前，先创建内存引擎
from sqlmodel import SQLModel, create_engine
from sqlmodel.pool import StaticPool

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 现在导入 db 模块并替换引擎
import app.core.db as db_module
db_module.engine = _test_engine

# 在新引擎上创建所有表
SQLModel.metadata.create_all(_test_engine)

# 现在可以安全导入其他组件
from fastapi.testclient import TestClient
from sqlmodel import Session
from main import app
from app.models import User, Student, UserRoleConst
from app.core.security import generate_password_hash


def _clear_all_data():
    """清理所有表数据"""
    from sqlalchemy import text
    with Session(_test_engine) as session:
        # 按照外键依赖顺序删除
        tables = [
            "score_logs",
            "checkin_records",
            "class_session",
            "course_schedules",
            "security_alerts",
            "audit_logs",
            "students",
            "users"
        ]
        for table in tables:
            try:
                session.execute(text(f"DELETE FROM {table}"))
            except Exception as e:
                pass
        session.commit()


@pytest.fixture(scope="function")
def test_engine():
    """提供测试引擎"""
    _clear_all_data()
    yield _test_engine


@pytest.fixture(scope="function")
def client(test_engine):
    """创建测试客户端"""
    def get_session_override():
        with Session(_test_engine) as session:
            yield session
    
    from app.core.db import get_session
    app.dependency_overrides[get_session] = get_session_override
    
    # 使用 cookie 存储 session
    with TestClient(app, cookies={}) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(test_engine):
    """创建管理员用户"""
    with Session(_test_engine) as session:
        password_hash, salt = generate_password_hash("admin123")
        user = User(
            username="admin",
            name="管理员",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.ADMIN,
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def teacher_user(test_engine):
    """创建教师用户"""
    with Session(_test_engine) as session:
        password_hash, salt = generate_password_hash("teacher123")
        user = User(
            username="teacher1",
            name="教师1",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.TEACHER,
            assigned_classes='["一班", "二班"]',
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def student_user(test_engine):
    """创建学生用户"""
    with Session(_test_engine) as session:
        password_hash, salt = generate_password_hash("student123")
        student = Student(
            student_id="S001",
            name="学生1",
            class_name="一班",
            score=80.0,
            password_hash=password_hash,
            salt=salt
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        return student


@pytest.fixture
def sample_students(test_engine):
    """创建多个学生用于测试"""
    with Session(_test_engine) as session:
        students = []
        for i in range(1, 6):
            student = Student(
                student_id=f"S00{i}",
                name=f"学生{i}",
                class_name="一班" if i <= 3 else "二班",
                score=70.0 + i * 5
            )
            session.add(student)
            students.append(student)
        # 添加一个三班学生（用于测试教师权限）
        student_s006 = Student(
            student_id="S006",
            name="学生6",
            class_name="三班",
            score=80.0
        )
        session.add(student_s006)
        students.append(student_s006)
        session.commit()
        for student in students:
            session.refresh(student)
        return students


@pytest.fixture
def admin_client(client, admin_user):
    """已登录管理员的客户端"""
    response = client.post("/api/login", json={
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    })
    assert response.status_code == 200, f"Admin login failed: {response.json()}"
    # 保存 cookies 以保持会话
    return client


@pytest.fixture
def teacher_client(client, teacher_user):
    """已登录教师的客户端"""
    response = client.post("/api/login", json={
        "username": "teacher1",
        "password": "teacher123",
        "role": "teacher"
    })
    assert response.status_code == 200, f"Teacher login failed: {response.json()}"
    return client


@pytest.fixture
def student_client(client, student_user):
    """已登录学生的客户端"""
    response = client.post("/api/login", json={
        "username": "S001",
        "password": "student123",
        "role": "student"
    })
    assert response.status_code == 200, f"Student login failed: {response.json()}"
    return client
