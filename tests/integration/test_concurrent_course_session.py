"""
课堂会话并发测试
验证教师并发开始上课不会创建重复的活跃课堂

注意：由于测试环境使用 StaticPool（单连接），FastAPI 的 def 路由在线程池中
并发执行时会导致多个线程共享同一个 SQLite 连接，引发 sqlite3.InterfaceError。
因此并发竞争测试直接调用 CRUD 函数并使用独立的多连接共享内存数据库；
HTTP 层的 409 响应通过顺序请求 + mock 验证。
"""
import uuid
import pytest
from concurrent.futures import ThreadPoolExecutor
from sqlmodel import Session, select, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool
from app.models import User, UserRoleConst, CourseSession
from app.core.security import generate_password_hash
from app.crud.course_session import start_course_session
from app.core.config import HttpStatus


pytestmark = pytest.mark.integration


def _create_shared_memory_engine():
    """创建一个使用 NullPool 的随机命名共享内存数据库引擎，保证每次测试完全隔离"""
    name = f"course_session_test_{uuid.uuid4().hex}"
    return create_engine(
        f"sqlite:///file:{name}?mode=memory&cache=shared",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )


class TestConcurrentCourseSession:
    """并发课堂会话测试"""

    def test_concurrent_start_course_session_crud_raises_integrity_error(self):
        """
        多线程并发直接调用 start_course_session：
        使用独立的多连接共享内存数据库，数据库唯一约束应确保只有一个成功，其余抛出 IntegrityError
        """
        engine = _create_shared_memory_engine()
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            password_hash, salt = generate_password_hash("teacher123")
            session.add(User(
                username="teacher1",
                name="教师1",
                password_hash=password_hash,
                salt=salt,
                role=UserRoleConst.TEACHER,
                assigned_classes='["一班"]',
                is_active=True
            ))
            session.commit()

        def start_class():
            with Session(engine) as session:
                return start_course_session(
                    session=session,
                    class_name="一班",
                    teacher_id=1,
                    teacher_name="教师1",
                    course_name="数学"
                )

        # 并发执行 3 次（模拟快速双击或少数并发）
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(start_class) for _ in range(3)]
            results = [f.result() if not f.exception() else f.exception() for f in futures]

        successes = [r for r in results if isinstance(r, CourseSession)]
        errors = [r for r in results if not isinstance(r, CourseSession)]

        assert len(successes) == 1, (
            f"数据库约束下应有恰好 1 个成功，实际 {len(successes)} 个，结果: {results}"
        )
        assert len(errors) == 2, (
            f"数据库约束下应有 2 个失败，实际 {len(errors)} 个，结果: {results}"
        )

        # 数据库验证：一班的活跃课堂只有 1 个
        with Session(engine) as session:
            active_list = session.exec(
                select(CourseSession).where(
                    CourseSession.class_name == "一班",
                    CourseSession.status == "active"
                )
            ).all()
            assert len(active_list) == 1, (
                f"数据库中一班的活跃课堂应只有 1 个，实际 {len(active_list)} 个"
            )

    def test_start_course_session_http_returns_409_on_conflict(self, client, test_engine):
        """
        顺序调用 API 验证路由层能把数据库冲突透传为 HTTP 409
        """
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("teacher123")
            session.add(User(
                username="teacher1",
                name="教师1",
                password_hash=password_hash,
                salt=salt,
                role=UserRoleConst.TEACHER,
                assigned_classes='["一班"]',
                is_active=True
            ))
            # 开课校验要求班级有启用学生
            from app.models import Student
            session.add(Student(
                student_id="CCS001",
                name="学生1",
                class_name="一班",
                score=60.0,
            ))
            session.commit()

        login_response = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert login_response.status_code == 200
        cookies = login_response.cookies

        # 先正常开始一次课堂
        response1 = client.post("/api/v1/course-sessions/start", json={
            "class_name": "一班",
            "course_name": "数学"
        }, cookies=cookies)
        assert response1.status_code == 200, f"首次开始上课应成功: {response1.json()}"

        # Mock CRUD 抛 IntegrityError，验证路由层捕获并返回 409
        from unittest.mock import patch
        with patch(
            "app.api.routes.course_sessions.start_course_session",
            side_effect=IntegrityError("INSERT INTO course_sessions ...", None, None)
        ):
            response2 = client.post("/api/v1/course-sessions/start", json={
                "class_name": "一班",
                "course_name": "数学"
            }, cookies=cookies)

        assert response2.status_code == HttpStatus.CONFLICT, (
            f"重复开始上课应返回 409，实际 {response2.status_code}: {response2.json()}"
        )
