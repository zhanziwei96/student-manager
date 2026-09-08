"""
学生分数并发更新测试
验证乐观锁能防止并发更新导致的数据丢失

注意：由于测试环境使用 StaticPool（单连接），FastAPI 的 async def 路由在并发
请求时可能因线程池 Session 创建与主线程 commit 的交互导致底层 SQLite 连接出现
线程安全问题。因此并发竞争测试直接调用 CRUD 函数；HTTP 层的 409 响应通过
顺序请求 + mock 验证。
"""
import os
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import Session, select, create_engine
from sqlalchemy.pool import NullPool
from app.models import Student, User, UserRoleConst
from app.core.security import generate_password_hash
from app.crud.student import update_student_score
from app.core.config import HttpStatus


pytestmark = pytest.mark.integration


def _create_pg_engine():
    """PG 测试引擎（NullPool：多线程独立连接真并发）；使用前清空共享测试库"""
    from sqlmodel import SQLModel
    eng = create_engine(os.environ['DATABASE__URL'], poolclass=NullPool)
    SQLModel.metadata.create_all(eng)  # 幂等（已存在则跳过）
    with Session(eng) as s:
        s.execute(text("TRUNCATE %s RESTART IDENTITY CASCADE"
                       % ", ".join(SQLModel.metadata.tables.keys())))
        s.commit()
    return eng


class TestConcurrentScoreUpdate:
    """并发分数更新测试"""

    def test_concurrent_score_update_crud_optimistic_lock(self):
        """
        多线程并发直接调用 update_student_score：
        使用独立的多连接共享内存数据库，确保 SQLite 事务隔离和锁机制正常工作。
        乐观锁应确保只有一个成功，另一个抛出 HTTPException(409)
        """
        # 创建支持多连接并发的共享内存数据库（避免 StaticPool 单连接竞争）
        engine = _create_pg_engine()
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
            ph2, salt2 = generate_password_hash("student123")
            session.add(Student(
                student_id="S001",
                name="学生1",
                class_name="一班",
                score=80.0,
                password_hash=ph2,
                salt=salt2
            ))
            session.commit()

        def update_score(delta, reason):
            with Session(engine) as session:
                return update_student_score(session, "S001", delta, reason, "teacher")

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(update_score, 5, "教师1加分")
            f2 = executor.submit(update_score, 10, "教师2加分")
            r1 = f1.result() if not f1.exception() else f1.exception()
            r2 = f2.result() if not f2.exception() else f2.exception()

        successes = [r for r in [r1, r2] if isinstance(r, Student)]
        errors = [r for r in [r1, r2] if isinstance(r, HTTPException)]

        assert len(successes) == 1, (
            f"乐观锁下应只有一个更新成功，实际 {len(successes)} 个，结果: {[r1, r2]}"
        )
        assert len(errors) == 1, (
            f"乐观锁下应有一个冲突 409，实际 {len(errors)} 个，结果: {[r1, r2]}"
        )
        assert errors[0].status_code == 409

        # 数据库验证
        with Session(engine) as session:
            result = session.exec(select(Student).where(Student.student_id == "S001")).first()
            assert result is not None
            final_score = result.score

            # 最终分数只能是 85 或 90，取决于哪个请求先成功
            assert final_score in [85.0, 90.0], (
                f"最终分数应为 85 或 90，实际 {final_score}"
            )

            # ScoreLog 应该只有 1 条
            logs = session.exec(select(Student).where(Student.student_id == "S001")).all()
            # Oops, ScoreLog 表查询...
            from app.models import ScoreLog
            logs = session.exec(select(ScoreLog).where(ScoreLog.student_id == "S001")).all()
            assert len(logs) == 1, f"应只有 1 条分数日志，实际 {len(logs)} 条"

    def test_score_update_http_returns_409_on_conflict(self, client, test_engine):
        """
        顺序调用 API 验证路由层能正确把 CRUD 的乐观锁异常透传为 HTTP 409
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
            ph2, salt2 = generate_password_hash("student123")
            session.add(Student(
                student_id="S001",
                name="学生1",
                class_name="一班",
                score=80.0,
                password_hash=ph2,
                salt=salt2
            ))
            session.commit()

        # 教师登录
        login_resp = client.post("/api/v1/login", json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "teacher"
        })
        assert login_resp.status_code == 200
        cookies = login_resp.cookies

        # 先正常更新一次
        r1 = client.put("/api/v1/students/S001/score", json={
            "score_change": 5,
            "reason": "第一次更新"
        }, cookies=cookies)
        assert r1.status_code == 200, f"首次更新应成功: {r1.json()}"

        # Mock CRUD 抛 409，验证路由层透传
        from unittest.mock import patch
        from fastapi import HTTPException
        with patch(
            "app.api.routes.students.update_student_score",
            side_effect=HTTPException(status_code=409, detail="分数已被其他用户修改")
        ):
            r2 = client.put("/api/v1/students/S001/score", json={
                "score_change": 10,
                "reason": "模拟并发冲突"
            }, cookies=cookies)

        assert r2.status_code == HttpStatus.CONFLICT, (
            f"乐观锁冲突应返回 409，实际 {r2.status_code}: {r2.json()}"
        )
        assert "已被其他用户修改" in r2.json().get("message", "")
