"""学生评论/认领失物招领（回归：操作者外键指向 users.id 导致 500）

根因：`lost_found_comments.user_id` / `lost_found_claims.student_id` 原为
`int` + FK→`users.id`，但学生的 JWT `sub` 是**学号**（字符串）：

- 学号非纯数字（如 "S001"）→ 路由里 `int(user["sub"])` 直接 `ValueError`
- 学号是纯数字（如 "2025010101"）→ 插入后无对应 users 行 → `ForeignKeyViolation`

两条路都是 500，所以这两张表在开发库里一直是 0 行。

正确模型：失物招领只有**学生**能评论/认领（无任何教师评论端点），
故外键应指向 `students.student_id`、列类型为 `str`
（与 `enrollments.student_id` / `student_class_semesters.student_id` 同构）。
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select


@pytest.fixture
def published_item(teacher_client: TestClient, seed_refs):
    """教师发布一件「仅一班可见」的物品，返回 item_id

    教师 teacher1 的授课范围是一班+二班；学生 S001 在一班，故对该物品可见。
    """
    resp = teacher_client.post("/api/v1/teacher/lost-found", data={
        "title": "捡到一张校园卡",
        "description": "在机房捡到的",
        "location": "机房302",
        "class_ids": [seed_refs["一班"]],
    })
    assert resp.status_code == 200, resp.json()
    return resp.json()["data"]["item_id"]


def test_student_can_comment_on_item(
    student_client: TestClient, published_item: int, test_engine
):
    """学生评论 → 200，且落库的操作者是学号字符串"""
    from app.models.lost_found import LostFoundComment

    resp = student_client.post(
        f"/api/v1/student/lost-found/{published_item}/comments",
        json={"content": "这张卡是我的"},
    )
    assert resp.status_code == 200, resp.json()
    comment_id = resp.json()["data"]["comment_id"]

    with Session(test_engine) as session:
        comment = session.get(LostFoundComment, comment_id)
    assert comment is not None
    assert comment.student_id == "S001"


def test_student_can_claim_item(student_client: TestClient, published_item: int, test_engine):
    """学生认领 → 200，且落库的操作者是学号字符串"""
    from app.models.lost_found import LostFoundClaim

    resp = student_client.post(
        f"/api/v1/student/lost-found/{published_item}/claim",
        json={"contact": "13800000000", "message": "卡号后四位 1234"},
    )
    assert resp.status_code == 200, resp.json()
    claim_id = resp.json()["data"]["claim_id"]

    with Session(test_engine) as session:
        claim = session.get(LostFoundClaim, claim_id)
    assert claim is not None
    assert claim.student_id == "S001"


def test_comment_response_exposes_student_name(
    student_client: TestClient, teacher_client: TestClient, published_item: int
):
    """教师看详情时，评论显示学生真实姓名（按 students.student_id 解析）"""
    student_client.post(
        f"/api/v1/student/lost-found/{published_item}/comments",
        json={"content": "是我丢的"},
    )

    data = teacher_client.get(
        f"/api/v1/teacher/lost-found/{published_item}"
    ).json()["data"]

    assert len(data["comments"]) == 1
    comment = data["comments"][0]
    assert comment["student_id"] == "S001"
    assert comment["student_name"] == "学生1"


def test_claim_response_exposes_student_name(
    student_client: TestClient, teacher_client: TestClient, published_item: int
):
    """教师看详情时，认领记录显示学生真实姓名"""
    student_client.post(
        f"/api/v1/student/lost-found/{published_item}/claim",
        json={"contact": "13800000000"},
    )

    data = teacher_client.get(
        f"/api/v1/teacher/lost-found/{published_item}"
    ).json()["data"]

    assert len(data["claims"]) == 1
    claim = data["claims"][0]
    assert claim["student_id"] == "S001"
    assert claim["student_name"] == "学生1"


def test_student_sees_own_claim_and_comment(
    student_client: TestClient, published_item: int
):
    """学生看详情时能看到自己的评论与认领（my_claim 按学号匹配）"""
    student_client.post(
        f"/api/v1/student/lost-found/{published_item}/comments",
        json={"content": "是我丢的"},
    )
    student_client.post(
        f"/api/v1/student/lost-found/{published_item}/claim",
        json={"contact": "13800000000"},
    )

    data = student_client.get(
        f"/api/v1/student/lost-found/{published_item}"
    ).json()["data"]

    assert len(data["comments"]) == 1
    # 学生端评论匿名
    assert data["comments"][0]["student_name"] == "匿名用户"
    assert data["comments"][0]["student_id"] == ""
    # my_claim 只回 id/status/created_at（不回显自己填的联系方式）
    assert data["my_claim"] is not None
    assert data["my_claim"]["status"] == "pending"


def test_student_cannot_claim_twice(student_client: TestClient, published_item: int):
    """重复认领 → 400（既有行为不能因本次改动失效）"""
    body = {"contact": "13800000000"}
    assert student_client.post(
        f"/api/v1/student/lost-found/{published_item}/claim", json=body
    ).status_code == 200
    assert student_client.post(
        f"/api/v1/student/lost-found/{published_item}/claim", json=body
    ).status_code == 400
