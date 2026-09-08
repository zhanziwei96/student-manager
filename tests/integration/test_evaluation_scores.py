"""
小组互评分数返回测试

验证评价接口返回已有分数值，而非仅返回 scored 布尔值。
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from main import create_app
from app.core.db import get_session
from app.core.jwt import create_access_token
from app.models.user import User
from app.models.student import Student
from app.models.group import Group, GroupMember, EvaluationAssignment, GroupEvaluationScore
from app.models.group import GroupTask, GroupTaskDimension
from app.models.constants import UserRoleConst
from app.core.timezone import get_now


@pytest.fixture
def session(engine):
    """PG 数据库会话（复用根 conftest 引擎，函数级清表）"""
    from sqlalchemy import text
    with Session(engine) as s:
        s.execute(text("TRUNCATE %s RESTART IDENTITY CASCADE"
                       % ", ".join(SQLModel.metadata.tables.keys())))
        s.commit()
    with Session(engine) as s:
        yield s


@pytest.fixture
def app(session):
    def override():
        yield session
    a = create_app()
    a.dependency_overrides[get_session] = override
    return a


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def setup_task(session):
    """创建完整的互评任务环境：教师、2个小组、任务、维度、评价分配"""
    # 教师
    teacher = User(username="teacher1", name="李老师", password_hash="x", role=UserRoleConst.TEACHER)
    session.add(teacher)
    session.commit()
    session.refresh(teacher)

    # 学生
    student = User(username="S001", name="张三", password_hash="x", role=UserRoleConst.STUDENT)
    session.add(student)
    session.commit()
    session.refresh(student)
    stu = Student(student_id="S001", name="张三", class_name="一班")
    session.add(stu)
    session.commit()

    # 小组
    group1 = Group(name="A组", class_name="一班", leader_student_id="S001")
    group2 = Group(name="B组", class_name="一班", leader_student_id="S001")
    session.add(group1)
    session.add(group2)
    session.commit()
    session.refresh(group1)
    session.refresh(group2)

    # 组员
    member1 = GroupMember(group_id=group1.id, student_id="S001")
    session.add(member1)
    session.commit()

    # 任务
    task = GroupTask(
        title="互评任务", class_name="一班",
        created_by=teacher.username, status="evaluating",
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # 维度
    dim1 = GroupTaskDimension(task_id=task.id, name="协作能力", sort_order=0)
    dim2 = GroupTaskDimension(task_id=task.id, name="表达能力", sort_order=1)
    session.add(dim1)
    session.add(dim2)
    session.commit()
    session.refresh(dim1)
    session.refresh(dim2)

    # 评价分配：A组评B组
    assign = EvaluationAssignment(
        task_id=task.id, evaluator_group_id=group1.id, target_group_id=group2.id,
    )
    session.add(assign)
    session.commit()

    return {
        "teacher": teacher, "student": student, "task": task,
        "group1": group1, "group2": group2,
        "dim1": dim1, "dim2": dim2,
    }


class TestEvaluationReturnsScores:
    """评价接口应返回已有分数值"""

    def test_evaluations_return_score_value_after_submission(self, client, session, setup_task):
        """提交评分后，再次获取评价列表应包含分数值"""
        s = setup_task
        token = create_access_token({"sub": "S001", "role": UserRoleConst.STUDENT})
        client.cookies.set("access_token", token)

        # 提交评分：dim1=85, dim2=90
        resp = client.post(
            f"/api/v1/student/group-tasks/{s['task'].id}/scores",
            json={
                "target_group_id": s["group2"].id,
                "scores": [
                    {"dimension_id": s["dim1"].id, "score": 85},
                    {"dimension_id": s["dim2"].id, "score": 90},
                ],
            },
        )
        assert resp.status_code == 200

        # 获取评价列表
        resp = client.get(
            f"/api/v1/student/group-tasks/{s['task'].id}/evaluations",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]

        # 找到目标小组
        target = next(t for t in data if t["target_group_id"] == s["group2"].id)

        # 验证维度包含分数值
        dim1_data = next(d for d in target["dimensions"] if d["id"] == s["dim1"].id)
        dim2_data = next(d for d in target["dimensions"] if d["id"] == s["dim2"].id)

        # 这些断言会失败，因为当前 API 只返回 scored: boolean，不返回 score
        assert dim1_data["scored"] is True
        assert dim1_data["score"] == 85, f"期望 score=85，实际: {dim1_data.get('score')}"
        assert dim2_data["scored"] is True
        assert dim2_data["score"] == 90, f"期望 score=90，实际: {dim2_data.get('score')}"

    def test_evaluations_return_null_score_before_submission(self, client, session, setup_task):
        """未提交评分时，维度应返回 score=None"""
        s = setup_task
        token = create_access_token({"sub": "S001", "role": UserRoleConst.STUDENT})
        client.cookies.set("access_token", token)

        resp = client.get(
            f"/api/v1/student/group-tasks/{s['task'].id}/evaluations",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        target = next(t for t in data if t["target_group_id"] == s["group2"].id)

        dim1_data = next(d for d in target["dimensions"] if d["id"] == s["dim1"].id)
        assert dim1_data["scored"] is False
        assert dim1_data["score"] is None, f"期望 score=None，实际: {dim1_data.get('score')}"
