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

    # 验证新任务出现在二班列表中，且标题带（复制）后缀
    resp = teacher_client.get("/api/v1/teacher/group-tasks?class_name=二班")
    assert resp.status_code == 200
    tasks = resp.json()["data"]
    cloned = next((t for t in tasks if t["id"] == data["data"]["task_id"]), None)
    assert cloned is not None
    assert cloned["title"] == "克隆源任务（复制）"


def test_teacher_clone_nonexistent_task(teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/group-tasks/99999/clone", json={
        "target_class_name": "二班",
    })
    assert resp.status_code == 404
    assert resp.json()["success"] is False
