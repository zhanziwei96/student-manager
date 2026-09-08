"""
签到并发测试
验证同一学生在高并发场景下不会重复签到
"""
import pytest
import asyncio
import httpx
from sqlmodel import Session, create_engine
from app.models import Student, User, UserRoleConst
from app.core.security import generate_password_hash
from app.crud.course_session import start_course_session
from main import app


pytestmark = pytest.mark.integration


class TestConcurrentCheckin:
    """并发签到场景测试"""

    def _create_teacher(self, test_engine):
        """创建并返回教师用户"""
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("teacher123")
            user = User(
                username="teacher1",
                name="教师1",
                password_hash=password_hash,
                salt=salt,
                role=UserRoleConst.TEACHER,
                assigned_classes='["一班"]',
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def _create_student(self, test_engine, student_id="S001"):
        """创建并返回学生用户"""
        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("student123")
            student = Student(
                student_id=student_id,
                name=f"学生{student_id}",
                class_name="一班",
                score=80.0,
                password_hash=password_hash,
                salt=salt
            )
            session.add(student)
            session.commit()
            session.refresh(student)
            return student

    def _start_class(self, test_engine):
        """直接通过 CRUD 创建活跃课堂"""
        with Session(test_engine) as session:
            cs = start_course_session(
                session=session,
                class_name="一班",
                teacher_id=1,
                teacher_name="教师1",
                course_name="数学"
            )
            return cs

    @pytest.mark.asyncio
    async def test_concurrent_checkin_same_student(self, client, test_engine):
        """
        同一学生并发签到：只能有 1 个成功，其余应返回 409
        使用 AsyncClient + asyncio.gather 实现真正的并发请求
        """
        # 准备数据
        self._create_teacher(test_engine)
        self._create_student(test_engine, "S001")
        cs = self._start_class(test_engine)

        # 学生登录获取 cookie
        login_response = client.post("/api/v1/login", json={
            "username": "S001",
            "password": "student123",
            "role": "student"
        })
        assert login_response.status_code == 200
        cookies = login_response.cookies

        from main import app

        from app.core.qr_signature import generate_verification_code
        code = generate_verification_code(cs.session_code)["code"]

        async def do_checkin():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
                cookies=cookies
            ) as ac:
                return await ac.post("/api/v1/checkin", json={
                    "student_id": "S001",
                    "student_name": "学生S001",
                    "verification_code": code
                })

        # 并发发送 5 个签到请求
        responses = await asyncio.gather(
            do_checkin(), do_checkin(), do_checkin(), do_checkin(), do_checkin()
        )

        status_codes = [r.status_code for r in responses]
        success_count = status_codes.count(200)
        conflict_count = status_codes.count(409)

        # 断言：恰好 1 个成功，其余都是 409
        assert success_count == 1, (
            f"并发签到应有恰好 1 个成功，实际成功 {success_count} 个，"
            f"状态码分布: {status_codes}"
        )
        assert conflict_count == 4, (
            f"并发签到应有 4 个冲突，实际 {conflict_count} 个，"
            f"状态码分布: {status_codes}"
        )

        # 验证数据库中只有 1 条签到记录
        with Session(test_engine) as session:
            from app.crud.checkin import get_checkins_by_session_id
            checkins = get_checkins_by_session_id(session, cs.id)
            assert len(checkins) == 1, f"数据库中应只有 1 条签到记录，实际 {len(checkins)} 条"

    @pytest.mark.asyncio
    async def test_concurrent_checkin_multiple_students(self, client, test_engine):
        """
        全班多个学生同时签到：所有学生都应成功，且互不冲突
        """
        self._create_teacher(test_engine)
        students = []
        with Session(test_engine) as session:
            for i in range(1, 6):
                password_hash, salt = generate_password_hash("student123")
                student = Student(
                    student_id=f"S{i:03d}",
                    name=f"学生{i}",
                    class_name="一班",
                    score=80.0,
                    password_hash=password_hash,
                    salt=salt
                )
                session.add(student)
                students.append(student)
            session.commit()

        cs = self._start_class(test_engine)

        from app.core.qr_signature import generate_verification_code
        code = generate_verification_code(cs.session_code)["code"]

        async def login_and_checkin(student_id):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver"
            ) as ac:
                login_resp = await ac.post("/api/v1/login", json={
                    "username": student_id,
                    "password": "student123",
                    "role": "student"
                })
                if login_resp.status_code != 200:
                    return login_resp
                cookies = login_resp.cookies
                return await ac.post("/api/v1/checkin", json={
                    "student_id": student_id,
                    "student_name": f"学生{student_id}",
                    "verification_code": code
                }, cookies=cookies)

        tasks = [login_and_checkin(f"S{i:03d}") for i in range(1, 6)]
        responses = await asyncio.gather(*tasks)

        status_codes = [r.status_code for r in responses]
        assert all(s == 200 for s in status_codes), (
            f"全班同时签到应全部成功，实际状态码: {status_codes}"
        )

        with Session(test_engine) as session:
            from app.crud.checkin import count_checkins_by_session_id
            count = count_checkins_by_session_id(session, cs.id)
            assert count == 5, f"数据库中应有 5 条签到记录，实际 {count} 条"

    def test_mass_concurrent_checkin_wal_stress(self):
        """
        高并发 WAL 压力测试：50 名学生通过独立的数据库连接并发签到
        使用 NullPool + 共享内存数据库，直接调用 CRUD，绕过 HTTP 层线程池干扰，
        专门验证 SQLite WAL 模式下大量并发写不会出现 DATABASE IS LOCKED 等异常。
        """
        import os
        from sqlalchemy import text
        from sqlalchemy.pool import NullPool
        from app.crud.checkin import create_checkin
        from app.crud.course_session import start_course_session

        engine = create_engine(
            os.environ['DATABASE__URL'],
            poolclass=NullPool,
        )
        from sqlmodel import SQLModel
        SQLModel.metadata.create_all(engine)
        with Session(engine) as s:
            s.execute(text("TRUNCATE %s RESTART IDENTITY CASCADE"
                           % ", ".join(SQLModel.metadata.tables.keys())))
            s.commit()

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
            for i in range(1, 51):
                ph, s = generate_password_hash("student123")
                session.add(Student(
                    student_id=f"W{i:03d}",
                    name=f"学生{i}",
                    class_name="一班",
                    score=80.0,
                    password_hash=ph,
                    salt=s
                ))
            session.commit()

        with Session(engine) as session:
            cs = start_course_session(
                session=session,
                class_name="一班",
                teacher_id=1,
                teacher_name="教师1",
                course_name="数学"
            )
            session_id = cs.id

        def do_checkin(student_id):
            try:
                with Session(engine) as session:
                    create_checkin(
                        session,
                        student_id=student_id,
                        student_name=f"学生{student_id}",
                        class_name="一班",
                        session_id=session_id
                    )
                    return True
            except Exception as e:
                return e

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(do_checkin, f"W{i:03d}") for i in range(1, 51)]
            results = [f.result() for f in futures]

        errors = [r for r in results if isinstance(r, Exception)]
        successes = [r for r in results if r is True]

        assert len(errors) == 0, (
            f"WAL 模式下 50 并发签到不应抛异常，实际异常数: {len(errors)}，"
            f"前 3 个异常: {[str(e) for e in errors[:3]]}"
        )
        assert len(successes) == 50, (
            f"应有 50 个成功，实际 {len(successes)} 个"
        )

        with Session(engine) as session:
            from app.crud.checkin import count_checkins_by_session_id
            count = count_checkins_by_session_id(session, session_id)
            assert count == 50, f"数据库中应有 50 条签到记录，实际 {count} 条"
