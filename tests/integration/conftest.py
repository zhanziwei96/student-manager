"""
集成测试配置和夹具
"""
import pytest
import os
import sys

# 设置测试环境
os.environ['ENV'] = 'testing'
os.environ['RATE_LIMIT__ENABLED'] = 'false'  # 禁用限流
os.environ.setdefault('DATABASE__URL',
                      'postgresql+psycopg2://classhub:classhub_dev@localhost:5432/classhub_test')

# 确保 backend 在路径中
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 关键：在导入任何应用模块前，先创建 PG 测试引擎
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, create_engine

# NullPool：每次会话独立连接，不跨线程共享（StaticPool 单连接会被 TestClient
# 应用线程与审计后台线程共享，造成间歇性丢写/refresh 失败），也不常驻连接
_test_engine = create_engine(os.environ['DATABASE__URL'], poolclass=NullPool)

# 现在导入 db 模块并替换引擎
import app.core.db as db_module
db_module.engine = _test_engine

# 先删废弃表（任务/互评已停用，旧测试库残留且 FK 引用 groups，阻止 drop_all）
with _test_engine.begin() as conn:
    from sqlalchemy import text
    conn.execute(text(
        "DROP TABLE IF EXISTS group_evaluation_scores, evaluation_assignments, "
        "group_task_dimensions, group_tasks CASCADE"
    ))
    conn.execute(text(
        "DROP TABLE IF EXISTS student_subject_score_logs, student_subject_scores, "
        "subjects, score_logs CASCADE"
    ))

# 在新引擎上创建所有表
# 必须先导入全部模型：否则 metadata 不完整，drop_all/create_all 会跳过这些表，
# 长期存在的测试库会保留旧 schema（模型改动看起来"没生效"）
import app.models  # noqa: F401
SQLModel.metadata.drop_all(_test_engine)
SQLModel.metadata.create_all(_test_engine)

# 现在可以安全导入其他组件
from fastapi.testclient import TestClient
from sqlmodel import Session
from main import app
from app.models import User, Student, UserRoleConst
from app.models.question import Question, Answer  # noqa: F401
from app.core.security import generate_password_hash


def _clear_all_data():
    """清理所有表数据 — PG TRUNCATE 一次清空，自动覆盖新表"""
    from sqlalchemy import text
    with Session(_test_engine) as session:
        session.execute(text(
            "TRUNCATE %s RESTART IDENTITY CASCADE"
            % ", ".join(SQLModel.metadata.tables.keys())
        ))
        session.commit()


@pytest.fixture(scope="function")
def test_engine():
    """提供测试引擎"""
    _clear_all_data()
    # 模型变更后重新创建表/索引（如 partial unique index）
    SQLModel.metadata.create_all(_test_engine)
    # 清理进程级缓存（班级/学期映射），避免跨测试污染
    from app.core.class_cache import invalidate_class_cache
    from app.core.term import invalidate_semester_cache
    invalidate_class_cache()
    invalidate_semester_cache()
    yield _test_engine


@pytest.fixture(scope="function")
def session(test_engine):
    """集成测试会话 — 绑定 _test_engine，与 API 客户端/清表逻辑同引擎同连接，
    避免与 root conftest 引擎双连接共库交错（间歇性 refresh 失败的根因）"""
    with Session(_test_engine) as s:
        yield s


def ensure_class(engine, name: str) -> int:
    """get-or-create 班级行并返回 class_id（供使用自有引擎的用例复用）"""
    from sqlmodel import select
    from app.models import Class_
    from app.core.class_cache import invalidate_class_cache

    with Session(engine) as session:
        cls = session.exec(select(Class_).where(Class_.name == name)).first()
        if cls is None:
            cls = Class_(name=name, cohort_year="2026")
            session.add(cls)
            session.commit()
            session.refresh(cls)
        class_id = cls.id
    invalidate_class_cache()
    return class_id


def ensure_current_semester(engine) -> int:
    """get-or-create 当前学期并返回 semester_id"""
    from datetime import date
    from sqlmodel import select
    from app.models import Semester
    from app.core.term import invalidate_semester_cache

    with Session(engine) as session:
        sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).first()
        if sem is None:
            sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                           total_weeks=20, is_current=True)
            session.add(sem)
            session.commit()
            session.refresh(sem)
        semester_id = sem.id
    invalidate_semester_cache()
    return semester_id


def ensure_class_and_semester(engine, name: str = "一班") -> int:
    """get-or-create 班级与当前学期（FK 锚点），返回 class_id"""
    class_id = ensure_class(engine, name)
    ensure_current_semester(engine)
    return class_id


@pytest.fixture
def seed_refs(test_engine):
    """seed 班级（一班/二班/三班）与当前学期，返回引用 id 的 dict

    业务表已改为纯 FK 锚点（class_id / semester_id 必填），测试构造业务对象
    时从此 fixture 取 id：
        cs = CourseSession(..., class_id=seed_refs["一班"], semester_id=seed_refs["semester_id"])
    """
    refs = {name: ensure_class(test_engine, name) for name in ("一班", "二班", "三班")}
    refs["semester_id"] = ensure_current_semester(test_engine)
    return refs


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
    """创建教师用户（授课关系从 course_offerings 派生，class_scope 覆盖一班/二班）"""
    with Session(_test_engine) as session:
        password_hash, salt = generate_password_hash("teacher123")
        user = User(
            username="teacher1",
            name="教师1",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.TEACHER,
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        # 授课教学班（权限唯一真源）：semester_id FK 必填，用非当前学期占位
        from datetime import date
        from sqlmodel import select
        from app.models import Course, CourseOffering, Semester
        math = session.exec(select(Course).where(Course.code == "MATH1")).first()
        if math is None:
            math = Course(code="MATH1", name="高等数学")
            session.add(math)
        sem = session.exec(select(Semester).where(Semester.label == "TCH-SEED")).first()
        if sem is None:
            sem = Semester(label="TCH-SEED", start_date=date(2026, 1, 1),
                           total_weeks=20, is_current=False)
            session.add(sem)
        session.commit()
        session.add(CourseOffering(
            course_id=math.id, semester_id=sem.id, teacher_id=user.id,
            teacher_name=user.name, class_scope="一班,二班", status="active",
        ))
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def student_user(test_engine):
    """创建学生用户（所属班级为一班，class_id 与 class_name 同步写入）"""
    class_id = ensure_class(test_engine, "一班")
    with Session(_test_engine) as session:
        password_hash, salt = generate_password_hash("student123")
        student = Student(
            student_id="S001",
            name="学生1",
            class_name="一班",
            class_id=class_id,
            password_hash=password_hash,
            salt=salt
        )
        session.add(student)
        session.commit()
        session.refresh(student)
        return student


@pytest.fixture
def sample_students(test_engine, seed_refs):
    """创建多个学生用于测试（class_id 引用 seed_refs 锚定的班级）"""
    with Session(_test_engine) as session:
        students = []
        for i in range(1, 6):
            class_name = "一班" if i <= 3 else "二班"
            student = Student(
                student_id=f"S00{i}",
                name=f"学生{i}",
                class_name=class_name,
                class_id=seed_refs[class_name],
            )
            session.add(student)
            students.append(student)
        # 添加一个三班学生（用于测试教师权限）
        student_s006 = Student(
            student_id="S006",
            name="学生6",
            class_name="三班",
            class_id=seed_refs["三班"],
        )
        session.add(student_s006)
        students.append(student_s006)
        session.commit()
        for student in students:
            session.refresh(student)
        return students


@pytest.fixture
def admin_client(test_engine, admin_user):
    """已登录管理员的客户端（独立实例，避免 cookie 冲突）"""
    def get_session_override():
        with Session(_test_engine) as session:
            yield session
    from app.core.db import get_session
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app, cookies={}) as c:
        response = c.post("/api/v1/login", json={
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        })
        assert response.status_code == 200, f"Admin login failed: {response.json()}"
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def teacher_client(test_engine, teacher_user):
    """已登录教师的客户端（独立实例，避免 cookie 冲突）"""
    def get_session_override():
        with Session(_test_engine) as session:
            yield session
    from app.core.db import get_session
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app, cookies={}) as c:
        response = c.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert response.status_code == 200, f"Teacher login failed: {response.json()}"
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def student_client(test_engine, student_user):
    """已登录学生的客户端（独立实例，避免 cookie 冲突）"""
    def get_session_override():
        with Session(_test_engine) as session:
            yield session
    from app.core.db import get_session
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app, cookies={}) as c:
        response = c.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        assert response.status_code == 200, f"Student login failed: {response.json()}"
        yield c
    app.dependency_overrides.clear()
