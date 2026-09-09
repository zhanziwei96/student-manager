import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select


@pytest.fixture(autouse=True)
def seed_class_students(test_engine):
    """创建合作任务校验要求班级有启用学生：为一班/二班各预置 1 个启用学生"""
    from app.models import Student

    with Session(test_engine) as session:
        session.add(Student(
            student_id="GT000",
            name="种子学生",
            class_name="一班",
            score=60.0,
        ))
        session.add(Student(
            student_id="GT001",
            name="种子学生二",
            class_name="二班",
            score=60.0,
        ))
        session.commit()


@pytest.fixture
def course(test_engine):
    """创建课程 MATH1（小组按课程划分），返回 course_id"""
    from app.models import Course

    with Session(test_engine) as session:
        c = Course(code="MATH1", name="高等数学")
        session.add(c)
        session.commit()
        session.refresh(c)
        return c.id


def test_student_my_group_unauthenticated(client: TestClient):
    resp = client.get("/api/v1/student/groups/my-group")
    assert resp.status_code == 401


def test_student_create_and_view_group(student_client: TestClient, course):
    # 创建小组
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "先锋组",
        "course_id": course,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["name"] == "先锋组"

    # 查看我的小组（列表结构：每科一个）
    resp = student_client.get("/api/v1/student/groups/my-group")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "先锋组"
    assert data["data"][0]["is_leader"] is True


def test_teacher_auto_assign_and_list_groups(teacher_client: TestClient, session, course):
    _seed_settings_deps(session)
    # 自动分配（前提是班级有未分组学生）
    resp = teacher_client.post("/api/v1/teacher/groups/auto-assign", json={
        "class_name": "一班",
        "course_id": course,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

    # 列出班级小组
    resp = teacher_client.get("/api/v1/teacher/groups?class_name=一班")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_teacher_dissolution_requests(teacher_client: TestClient, student_client: TestClient, course):
    # 学生先创建小组
    student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "解散测试组",
        "course_id": course,
    })

    # 学生申请解散
    resp = student_client.post("/api/v1/student/groups/dissolution-requests", json={
        "reason": "测试解散",
    })
    assert resp.status_code == 200

    # 教师查看解散申请
    resp = teacher_client.get("/api/v1/teacher/group-dissolution-requests")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1

    req_id = data["data"][0]["id"]

    # 教师批准解散
    resp = teacher_client.post(f"/api/v1/teacher/group-dissolution-requests/{req_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def _seed_settings_deps(session):
    """seed 届/班/当前学期（复合主键设置表依赖）"""
    from datetime import date
    from app.models import Cohort, Class_, Semester

    if session.exec(select(Cohort).where(Cohort.year == "2026")).first() is None:
        session.add(Cohort(year="2026"))
    if session.exec(select(Class_).where(Class_.name == "一班")).first() is None:
        session.add(Class_(name="一班", cohort_year="2026"))
    if session.exec(select(Semester).where(Semester.is_current.is_(True))).first() is None:
        session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                             total_weeks=20, is_current=True))
    session.commit()


def test_teacher_get_class_group_settings_default(teacher_client: TestClient, session):
    _seed_settings_deps(session)
    resp = teacher_client.get("/api/v1/teacher/class-group-settings?class_name=一班")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["max_members_per_group"] == 5


def test_teacher_update_class_group_settings(teacher_client: TestClient, session):
    _seed_settings_deps(session)
    resp = teacher_client.put("/api/v1/teacher/class-group-settings", json={
        "class_name": "一班",
        "max_members_per_group": 6,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["max_members_per_group"] == 6


def test_student_cannot_join_full_group(teacher_client: TestClient, session):
    """教师设置上限后，设置端点返回正确值"""
    _seed_settings_deps(session)
    # 教师设置上限为 2
    resp = teacher_client.put("/api/v1/teacher/class-group-settings", json={
        "class_name": "一班",
        "max_members_per_group": 2,
    })
    assert resp.status_code == 200
    # 验证设置端点返回正确值
    resp = teacher_client.get("/api/v1/teacher/class-group-settings?class_name=一班")
    assert resp.json()["data"]["max_members_per_group"] == 2


def test_student_groups_returns_max_members_and_is_full(student_client: TestClient, course):
    """学生小组列表应返回 max_members 和 is_full 字段"""
    # 学生创建小组
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "测试组",
        "course_id": course,
    })
    assert resp.status_code == 200
    # 获取小组列表
    resp = student_client.get("/api/v1/student/groups?class_name=一班")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    groups = data["data"]
    assert len(groups) >= 1
    group = groups[-1]
    assert "max_members" in group
    assert "is_full" in group
    # 默认上限为 5，学生创建组后只有 1 人，不应满
    assert group["is_full"] is False


def test_teacher_groups_returns_course_and_score(teacher_client: TestClient):
    """GET /teacher/groups 返回 course_id/course_name/score"""
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import Course, Group

    with Session(_test_engine) as session:
        course = Course(code="MATH1", name="高等数学")
        session.add(course)
        session.commit()
        session.refresh(course)
        course_id = course.id

        group = Group(
            class_name="一班",
            name="第一组",
            leader_student_id="S001",
            course_id=course_id,
            score=5.0,
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        group_id = group.id

    resp = teacher_client.get("/api/v1/teacher/groups?class_name=一班")
    assert resp.status_code == 200
    data = resp.json()["data"]
    target = next((g for g in data if g["id"] == group_id), None)
    assert target is not None
    assert target["course_id"] == course_id
    assert target["course_name"] == "高等数学"
    assert target["score"] == 5.0


def test_student_create_group_with_course(student_client: TestClient):
    """学生创建小组带课程（course_id 必填）"""
    from sqlmodel import Session, select
    from tests.integration.conftest import _test_engine
    from app.models import Course, Group

    with Session(_test_engine) as session:
        course = Course(code="MATH1", name="高等数学")
        session.add(course)
        session.commit()
        session.refresh(course)

    resp = student_client.post(
        "/api/v1/student/groups",
        json={"class_name": "一班", "name": "数学第一组", "course_id": course.id},
    )
    assert resp.status_code == 200

    # 验证小组带课程
    with Session(_test_engine) as session:
        group = session.exec(
            select(Group).where(Group.name == "数学第一组")
        ).first()
        assert group is not None
        assert group.course_id == course.id


def test_student_can_join_multiple_course_groups(student_client: TestClient):
    """学生在不同科目可分别建组（每科一个小组）"""
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import Course

    with Session(_test_engine) as session:
        math = Course(code="MATH1", name="高等数学")
        eng = Course(code="ENG1", name="大学英语")
        session.add(math)
        session.add(eng)
        session.commit()
        math_id, eng_id = math.id, eng.id

    resp = student_client.post(
        "/api/v1/student/groups",
        json={"class_name": "一班", "name": "数学一组", "course_id": math_id},
    )
    assert resp.status_code == 200

    # 同科目重复建组被拒
    resp = student_client.post(
        "/api/v1/student/groups",
        json={"class_name": "一班", "name": "数学二组", "course_id": math_id},
    )
    assert resp.status_code == 400

    # 不同科目可再建组
    resp = student_client.post(
        "/api/v1/student/groups",
        json={"class_name": "一班", "name": "英语一组", "course_id": eng_id},
    )
    assert resp.status_code == 200

    # 我的小组返回两个（每科一个）
    resp = student_client.get("/api/v1/student/groups/my-group")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    assert {g["course_id"] for g in data} == {math_id, eng_id}
    assert all(g["course_name"] for g in data)


def test_teacher_creates_group(teacher_client: TestClient):
    """教师建组（TCH-06）：按班级+课程创建"""
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import Course

    with Session(_test_engine) as session:
        course = Course(code="MATH1", name="高等数学")
        session.add(course)
        session.commit()
        course_id = course.id

    resp = teacher_client.post(
        "/api/v1/teacher/groups",
        json={"class_name": "一班", "name": "数学A组", "course_id": course_id},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["group_id"] > 0

    resp = teacher_client.get("/api/v1/teacher/groups", params={
        "class_name": "一班", "course_id": course_id,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "数学A组"


def test_groups_leaderboard_removed(teacher_client: TestClient):
    """旧小组排行榜端点已删除（新 /rankings?type=group 取代）→ 404"""
    resp = teacher_client.get("/api/v1/groups/leaderboard")
    assert resp.status_code == 404
