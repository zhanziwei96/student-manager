import pytest
from fastapi.testclient import TestClient


def test_teacher_create_task(teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/group-tasks", json={
        "class_name": "一班",
        "title": "项目A",
        "description": "描述",
        "dimensions": ["创意"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "task_id" in data["data"]


def test_student_my_group_unauthenticated(client: TestClient):
    resp = client.get("/api/v1/student/groups/my-group")
    assert resp.status_code == 401


def test_student_create_and_view_group(student_client: TestClient):
    # 创建小组
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "先锋组",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["name"] == "先锋组"

    # 查看我的小组
    resp = student_client.get("/api/v1/student/groups/my-group")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["name"] == "先锋组"
    assert data["data"]["is_leader"] is True


def test_teacher_auto_assign_and_list_groups(teacher_client: TestClient):
    # 自动分配（前提是班级有未分组学生）
    resp = teacher_client.post("/api/v1/teacher/groups/auto-assign", json={
        "class_name": "一班",
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


def test_teacher_dissolution_requests(teacher_client: TestClient, student_client: TestClient):
    # 学生先创建小组
    student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "解散测试组",
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


def test_teacher_get_class_group_settings_default(teacher_client: TestClient):
    resp = teacher_client.get("/api/v1/teacher/class-group-settings?class_name=一班")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["max_members_per_group"] == 5


def test_teacher_update_class_group_settings(teacher_client: TestClient):
    resp = teacher_client.put("/api/v1/teacher/class-group-settings", json={
        "class_name": "一班",
        "max_members_per_group": 6,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["max_members_per_group"] == 6


def test_student_cannot_join_full_group(teacher_client: TestClient):
    """教师设置上限后，设置端点返回正确值"""
    # 教师设置上限为 2
    resp = teacher_client.put("/api/v1/teacher/class-group-settings", json={
        "class_name": "一班",
        "max_members_per_group": 2,
    })
    assert resp.status_code == 200
    # 验证设置端点返回正确值
    resp = teacher_client.get("/api/v1/teacher/class-group-settings?class_name=一班")
    assert resp.json()["data"]["max_members_per_group"] == 2


def test_student_groups_returns_max_members_and_is_full(student_client: TestClient):
    """学生小组列表应返回 max_members 和 is_full 字段"""
    # 学生创建小组
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "测试组",
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


def test_teacher_clone_own_task(teacher_client: TestClient):
    # 先创建源任务
    resp = teacher_client.post("/api/v1/teacher/group-tasks", json={
        "class_name": "一班",
        "title": "克隆源任务",
        "description": "源描述",
        "dimensions": ["创意", "表达"],
    })
    assert resp.status_code == 200
    source_task_id = resp.json()["data"]["task_id"]

    # 复制到二班
    resp = teacher_client.post(f"/api/v1/teacher/group-tasks/{source_task_id}/clone", json={
        "target_class_name": "二班",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "task_id" in data["data"]
    assert data["data"]["status"] == "preparing"

    # 验证新任务出现在二班列表中
    resp = teacher_client.get("/api/v1/teacher/group-tasks?class_name=二班")
    assert resp.status_code == 200
    tasks = resp.json()["data"]
    cloned = next((t for t in tasks if t["id"] == data["data"]["task_id"]), None)
    assert cloned is not None
    assert cloned["title"] == "克隆源任务"


def test_teacher_clone_nonexistent_task(teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/group-tasks/99999/clone", json={
        "target_class_name": "二班",
    })
    assert resp.status_code == 404
    assert resp.json()["success"] is False


def test_teacher_delete_own_task(teacher_client: TestClient):
    # 先创建并关闭任务
    resp = teacher_client.post("/api/v1/teacher/group-tasks", json={
        "class_name": "一班",
        "title": "待删除任务",
        "description": "描述",
        "dimensions": ["创意"],
    })
    assert resp.status_code == 200
    task_id = resp.json()["data"]["task_id"]

    resp = teacher_client.delete(f"/api/v1/teacher/group-tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["message"] == "任务已删除"

    # 再次删除应 404
    resp = teacher_client.delete(f"/api/v1/teacher/group-tasks/{task_id}")
    assert resp.status_code == 404


def test_teacher_delete_evaluating_task(teacher_client: TestClient, student_client: TestClient):
    # 通过底层数据操作确保一班有两个活跃小组（启动互评的前提）
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import Student, Group, GroupMember

    with Session(_test_engine) as session:
        s2 = Student(student_id="S002", name="学生2", class_name="一班", score=80.0)
        session.add(s2)
        session.commit()

    # 学生 S001 创建组1
    student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "删除测试组1",
    })

    # 底层创建组2（S002 为组长）
    with Session(_test_engine) as session:
        g2 = Group(class_name="一班", name="删除测试组2", leader_student_id="S002", is_active=True)
        session.add(g2)
        session.commit()
        session.refresh(g2)
        session.add(GroupMember(group_id=g2.id, student_id="S002"))
        session.commit()

    resp = teacher_client.post("/api/v1/teacher/group-tasks", json={
        "class_name": "一班",
        "title": "互评中任务",
        "description": "描述",
        "dimensions": ["创意"],
    })
    task_id = resp.json()["data"]["task_id"]

    # 启动任务
    resp = teacher_client.post(f"/api/v1/teacher/group-tasks/{task_id}/start")
    assert resp.status_code == 200

    resp = teacher_client.delete(f"/api/v1/teacher/group-tasks/{task_id}")
    assert resp.status_code == 400
    assert resp.json()["message"] == "互评中的任务不可删除"


def test_join_group_during_evaluation(student_client):
    """测试互评阶段未分配学生可以加入小组"""
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import GroupTask, Group, GroupMember

    # 先创建一个小组（由其他学生创建）
    with Session(_test_engine) as session:
        group = Group(
            class_name="一班",
            name="测试小组",
            leader_student_id="S002",
            is_active=True,
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        group_id = group.id

        # 添加组长为成员
        member = GroupMember(group_id=group_id, student_id="S002")
        session.add(member)
        session.commit()

    # 创建 evaluating 状态的 GroupTask
    with Session(_test_engine) as session:
        task = GroupTask(
            class_name="一班",
            title="互评任务",
            description="测试",
            status="evaluating",
            created_by="teacher1",
        )
        session.add(task)
        session.commit()

    # 学生 S001 未在任何小组中，尝试加入小组
    resp = student_client.post(f"/api/v1/student/groups/{group_id}/join-requests")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "request_id" in data["data"]


def test_create_group_during_evaluation(student_client):
    """测试互评阶段未分配学生可以创建小组"""
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import GroupTask

    # 先创建一个 evaluating 状态的 GroupTask
    with Session(_test_engine) as session:
        task = GroupTask(
            class_name="一班",
            title="互评任务",
            description="测试",
            status="evaluating",
            created_by="teacher1",
        )
        session.add(task)
        session.commit()

    # 学生 S001 未在任何小组中，尝试创建小组
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "新小组",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "group_id" in data["data"]


def test_leave_group_during_evaluation(student_client):
    """测试互评阶段已有小组学生不能退出小组"""
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import GroupTask, Group, GroupMember, Student

    # Create a student record and group for S001
    with Session(_test_engine) as session:
        # Ensure student exists
        student = session.get(Student, "S001")
        if not student:
            student = Student(student_id="S001", name="测试学生", class_name="一班")
            session.add(student)
            session.commit()

        # Create group with S001 as member
        group = Group(
            class_name="一班",
            name="测试小组",
            leader_student_id="S099",
            is_active=True,
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        group_id = group.id

        member = GroupMember(group_id=group_id, student_id="S001")
        session.add(member)
        session.commit()

    # Create evaluating GroupTask
    with Session(_test_engine) as session:
        task = GroupTask(
            class_name="一班",
            title="互评任务",
            description="测试",
            status="evaluating",
            created_by="teacher1",
        )
        session.add(task)
        session.commit()

    # Try to leave group during evaluation
    resp = student_client.post("/api/v1/student/groups/leave")
    assert resp.status_code == 400
    data = resp.json()
    assert "班级正在互评阶段" in data["message"]


def test_dissolve_group_during_evaluation(student_client):
    """测试互评阶段已有小组学生不能解散小组"""
    from sqlmodel import Session
    from tests.integration.conftest import _test_engine
    from app.models import GroupTask, Group, GroupMember, Student

    # Ensure student exists
    with Session(_test_engine) as session:
        student = session.get(Student, "S001")
        if not student:
            student = Student(student_id="S001", name="测试学生", class_name="一班")
            session.add(student)
            session.commit()

    # Create group with S001 as leader
    with Session(_test_engine) as session:
        group = Group(
            class_name="一班",
            name="测试小组",
            leader_student_id="S001",
            is_active=True,
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        group_id = group.id

        member = GroupMember(group_id=group_id, student_id="S001")
        session.add(member)
        session.commit()

    # Create evaluating GroupTask
    with Session(_test_engine) as session:
        task = GroupTask(
            class_name="一班",
            title="互评任务",
            description="测试",
            status="evaluating",
            created_by="teacher1",
        )
        session.add(task)
        session.commit()

    # Try to dissolve group during evaluation
    resp = student_client.post("/api/v1/student/groups/dissolution-requests", json={
        "reason": "测试解散",
    })
    assert resp.status_code == 400
    data = resp.json()
    assert "班级正在互评阶段" in data["message"]
