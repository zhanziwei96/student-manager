"""
问答 API 集成测试
"""
import pytest
from fastapi.testclient import TestClient


# ============== 教师端测试 ==============

def test_teacher_create_question(teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "什么是递归？",
        "class_name": "一班",
        "is_realtime": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "question_id" in data["data"]


def test_teacher_create_question_all_classes(teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/questions", json={
        "content": "通用问题",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_teacher_list_questions(teacher_client: TestClient):
    teacher_client.post("/api/v1/teacher/questions", json={"content": "Q1", "class_name": "一班"})
    teacher_client.post("/api/v1/teacher/questions", json={"content": "Q2", "class_name": "二班"})

    resp = teacher_client.get("/api/v1/teacher/questions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) == 2


def test_teacher_close_question(teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/questions", json={"content": "Q1"})
    qid = resp.json()["data"]["question_id"]

    resp = teacher_client.put(f"/api/v1/teacher/questions/{qid}/close")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = teacher_client.get("/api/v1/teacher/questions?status=closed")
    assert len(resp.json()["data"]) == 1


def test_teacher_reply_and_star(teacher_client: TestClient, student_client: TestClient):
    # 老师创建问题
    resp = teacher_client.post("/api/v1/teacher/questions", json={"content": "Q1", "class_name": "一班"})
    qid = resp.json()["data"]["question_id"]

    # 学生回答
    resp = student_client.post("/api/v1/student/answers", json={
        "question_id": qid,
        "content": "学生回答",
    })
    assert resp.status_code == 200
    aid = resp.json()["data"]["answer_id"]

    # 老师追问
    resp = teacher_client.post(f"/api/v1/teacher/answers/{aid}/reply", json={
        "answer_id": aid,
        "content": "老师追问",
    })
    assert resp.status_code == 200

    # 老师标记优秀
    resp = teacher_client.put(f"/api/v1/teacher/answers/{aid}/star?starred=true")
    assert resp.status_code == 200

    # 验证回答列表
    resp = teacher_client.get(f"/api/v1/student/questions/{qid}/answers")
    data = resp.json()["data"]
    assert len(data) == 2  # 回答 + 追问
    assert data[0]["is_starred"] is True


# ============== 学生端测试 ==============

def test_student_list_questions(student_client: TestClient, teacher_client: TestClient):
    teacher_client.post("/api/v1/teacher/questions", json={"content": "班级Q", "class_name": "一班"})
    teacher_client.post("/api/v1/teacher/questions", json={"content": "通用Q"})
    teacher_client.post("/api/v1/teacher/questions", json={"content": "其他班Q", "class_name": "二班"})

    resp = student_client.get("/api/v1/student/questions")
    assert resp.status_code == 200
    data = resp.json()["data"]
    # 学生看到本班问题 + 通用问题，看不到二班问题
    assert len(data) == 2


def test_student_create_answer(student_client: TestClient, teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/questions", json={"content": "Q1", "class_name": "一班"})
    qid = resp.json()["data"]["question_id"]

    resp = student_client.post("/api/v1/student/answers", json={
        "question_id": qid,
        "content": "我的回答",
        "is_anonymous": True,
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_student_cannot_answer_closed_question(student_client: TestClient, teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/questions", json={"content": "Q1", "class_name": "一班"})
    qid = resp.json()["data"]["question_id"]
    teacher_client.put(f"/api/v1/teacher/questions/{qid}/close")

    resp = student_client.post("/api/v1/student/answers", json={
        "question_id": qid,
        "content": "尝试回答",
    })
    assert resp.status_code == 400


def test_student_update_own_answer(student_client: TestClient, teacher_client: TestClient):
    resp = teacher_client.post("/api/v1/teacher/questions", json={"content": "Q1", "class_name": "一班"})
    qid = resp.json()["data"]["question_id"]
    resp = student_client.post("/api/v1/student/answers", json={
        "question_id": qid, "content": "原始内容",
    })
    aid = resp.json()["data"]["answer_id"]

    resp = student_client.put(f"/api/v1/student/answers/{aid}", json={"content": "修改后"})
    assert resp.status_code == 200

    resp = student_client.get(f"/api/v1/student/questions/{qid}/answers")
    assert resp.json()["data"][0]["content"] == "修改后"


def test_anonymous_answer_visibility(student_client: TestClient, teacher_client: TestClient):
    """测试匿名回答：老师能看到姓名和 student_id，其他学生看不到"""
    resp = teacher_client.post("/api/v1/teacher/questions", json={"content": "Q1", "class_name": "一班"})
    qid = resp.json()["data"]["question_id"]

    student_client.post("/api/v1/student/answers", json={
        "question_id": qid, "content": "匿名回答", "is_anonymous": True,
    })

    # 老师查看：能看到 student_id 和姓名
    resp = teacher_client.get(f"/api/v1/student/questions/{qid}/answers")
    data = resp.json()["data"]
    assert data[0]["student_id"] != ""
    assert data[0]["student_name"] is not None

    # 回答者自己查看：能看到自己的名字
    resp = student_client.get(f"/api/v1/student/questions/{qid}/answers")
    data = resp.json()["data"]
    assert data[0]["student_name"] is not None


def test_unauthenticated_access(client: TestClient):
    """测试未认证访问被拒绝"""
    resp = client.get("/api/v1/student/questions")
    assert resp.status_code == 401

    resp = client.post("/api/v1/teacher/questions", json={"content": "Q"})
    assert resp.status_code == 401
