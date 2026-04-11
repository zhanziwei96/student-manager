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
        "group_size": 4,
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
