"""
登录限流隔离并发测试
验证修复后：多个不同学生同时登录不会互相触发 429
"""
import pytest
import asyncio
import httpx
from sqlmodel import Session
from pyrate_limiter import Limiter, Rate
from app.models import Student, UserRoleConst
from app.core.security import generate_password_hash
from app.core.rate_limit import PerKeyBucketFactory, settings as rate_limit_settings


pytestmark = pytest.mark.integration


class TestConcurrentLoginIsolation:
    """并发登录限流隔离测试"""

    def _create_students(self, test_engine, count=5):
        """创建多个学生用户"""
        with Session(test_engine) as session:
            students = []
            for i in range(1, count + 1):
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
            for s in students:
                session.refresh(s)
            return students

    @pytest.mark.asyncio
    async def test_multiple_students_login_concurrently_with_rate_limit_enabled(self, client, test_engine):
        """
        临时启用限流后，5 个不同学生同时登录应全部成功，互不触发 429
        """
        from main import app

        # 准备数据：创建 5 个学生
        self._create_students(test_engine, count=5)

        # 临时替换为真实限流器（5次/60秒）
        original_limiter = getattr(app.state, 'limiter', None)
        real_limiter = Limiter(PerKeyBucketFactory([Rate(5, 60_000)]))
        app.state.limiter = real_limiter

        original_enabled = rate_limit_settings.rate_limit.enabled
        rate_limit_settings.rate_limit.enabled = True
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as ac:
                # 并发登录：5 个不同学生同时请求
                tasks = [
                    ac.post("/api/v1/login", json={
                        "username": f"S{i:03d}",
                        "password": "student123",
                        "role": UserRoleConst.STUDENT
                    })
                    for i in range(1, 6)
                ]
                responses = await asyncio.gather(*tasks)

                status_codes = [r.status_code for r in responses]

                # 断言：所有学生都应登录成功，没有任何 429
                assert all(s == 200 for s in status_codes), (
                    f"限流按 key 隔离后，不同学生同时登录不应触发 429，"
                    f"实际状态码: {status_codes}"
                )

                # 额外验证：单个用户在 60 秒内超过 5 次应被限流
                extra_tasks = [
                    ac.post("/api/v1/login", json={
                        "username": "S001",
                        "password": "student123",
                        "role": UserRoleConst.STUDENT
                    })
                    for _ in range(6)
                ]
                extra_responses = await asyncio.gather(*extra_tasks)
                extra_codes = [r.status_code for r in extra_responses]
                assert 429 in extra_codes, (
                    f"单用户超过 5 次登录应触发 429，实际状态码: {extra_codes}"
                )

        finally:
            # 恢复原始 limiter 和限流开关
            rate_limit_settings.rate_limit.enabled = original_enabled
            app.state.limiter = original_limiter

    @pytest.mark.asyncio
    async def test_single_user_rapid_login_with_rate_limit_enabled(self, client, test_engine):
        """
        临时启用限流后，同一学生快速登录 6 次，应有部分请求被 429
        """
        from main import app

        with Session(test_engine) as session:
            password_hash, salt = generate_password_hash("student123")
            student = Student(
                student_id="S999",
                name="测试学生",
                class_name="一班",
                score=80.0,
                password_hash=password_hash,
                salt=salt
            )
            session.add(student)
            session.commit()

        # 临时替换为严格限流器（2次/1秒）
        original_limiter = getattr(app.state, 'limiter', None)
        strict_limiter = Limiter(PerKeyBucketFactory([Rate(2, 1_000)]))
        app.state.limiter = strict_limiter

        original_enabled = rate_limit_settings.rate_limit.enabled
        rate_limit_settings.rate_limit.enabled = True
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as ac:
                tasks = [
                    ac.post("/api/v1/login", json={
                        "username": "S999",
                        "password": "student123",
                        "role": UserRoleConst.STUDENT
                    })
                    for _ in range(5)
                ]
                responses = await asyncio.gather(*tasks)

                status_codes = [r.status_code for r in responses]
                assert 200 in status_codes, f"前两次登录应成功，实际状态码: {status_codes}"
                assert 429 in status_codes, f"超过限流阈值后应返回 429，实际状态码: {status_codes}"
        finally:
            rate_limit_settings.rate_limit.enabled = original_enabled
            app.state.limiter = original_limiter
