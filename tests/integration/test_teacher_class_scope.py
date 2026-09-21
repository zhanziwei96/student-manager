"""教师班级范围授权测试

教师只能访问自己授课教学班关联的班级（`course_offering_classes` 是唯一真源）；
不属于自己的班级数据一律不可见 / 403。管理员不受限。

`teacher_user` fixture 关联「一班 + 二班」，`seed_refs` 另有「三班」作越权目标。
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select


def test_teacher_classes_list_scoped_to_own_classes(
    teacher_client: TestClient, teacher_user, seed_refs
):
    """GET /classes 只返回教师授课关联的班级，不返回全校班级"""
    resp = teacher_client.get("/api/v1/classes")
    assert resp.status_code == 200, resp.json()
    names = {c["name"] for c in resp.json()["data"]}
    assert names == {"一班", "二班"}
    assert "三班" not in names


def test_admin_classes_list_unscoped(admin_client: TestClient, teacher_user, seed_refs):
    """管理员仍能看到全部班级"""
    resp = admin_client.get("/api/v1/classes")
    assert resp.status_code == 200, resp.json()
    names = {c["name"] for c in resp.json()["data"]}
    assert {"一班", "二班", "三班"} <= names


def test_teacher_cannot_read_other_class_groups(
    teacher_client: TestClient, teacher_user, seed_refs
):
    """教师读别的班的小组 → 403"""
    resp = teacher_client.get(
        "/api/v1/teacher/groups", params={"class_id": seed_refs["三班"]}
    )
    assert resp.status_code == 403


def test_teacher_can_read_own_class_groups(
    teacher_client: TestClient, teacher_user, seed_refs
):
    """教师读自己班的小组 → 200"""
    resp = teacher_client.get(
        "/api/v1/teacher/groups", params={"class_id": seed_refs["一班"]}
    )
    assert resp.status_code == 200, resp.json()
    assert resp.json()["success"] is True


def test_admin_can_read_any_class_groups(
    admin_client: TestClient, teacher_user, seed_refs
):
    """管理员读任意班的小组 → 200"""
    resp = admin_client.get(
        "/api/v1/teacher/groups", params={"class_id": seed_refs["三班"]}
    )
    assert resp.status_code == 200, resp.json()


# ---------- 小组模块：写/读端点都必须按班级收敛 ----------


def test_teacher_cannot_create_group_in_other_class(
    teacher_client: TestClient, teacher_user, seed_refs
):
    """教师在别的班建组 → 403"""
    resp = teacher_client.post("/api/v1/teacher/groups", json={
        "class_id": seed_refs["三班"], "name": "越权小组", "course_id": 1,
    })
    assert resp.status_code == 403


def test_teacher_cannot_auto_assign_in_other_class(
    teacher_client: TestClient, teacher_user, seed_refs
):
    """教师在别的班批量分组 → 403"""
    resp = teacher_client.post("/api/v1/teacher/groups/auto-assign", json={
        "class_id": seed_refs["三班"], "course_id": 1,
    })
    assert resp.status_code == 403


def test_teacher_cannot_read_other_class_group_settings(
    teacher_client: TestClient, teacher_user, seed_refs
):
    """教师读别的班的小组设置 → 403"""
    resp = teacher_client.get(
        "/api/v1/teacher/class-group-settings", params={"class_id": seed_refs["三班"]}
    )
    assert resp.status_code == 403


def test_teacher_cannot_update_other_class_group_settings(
    teacher_client: TestClient, teacher_user, seed_refs
):
    """教师改别的班的小组人数上限 → 403"""
    resp = teacher_client.put("/api/v1/teacher/class-group-settings", json={
        "class_id": seed_refs["三班"], "max_members_per_group": 3,
    })
    assert resp.status_code == 403


@pytest.fixture
def foreign_group(test_engine, seed_refs, teacher_user):
    """别的班（三班）里的一个小组，作越权目标；返回 (group_id, dissolution_req_id)"""
    from app.models.group import Group, GroupDissolutionRequest

    with Session(test_engine) as session:
        group = Group(
            class_id=seed_refs["三班"], semester_id=seed_refs["semester_id"],
            name="三班小组", leader_student_id="S006",
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        req = GroupDissolutionRequest(group_id=group.id, reason="想解散")
        session.add(req)
        session.commit()
        session.refresh(req)
        return group.id, req.id


def test_teacher_cannot_read_other_class_group_detail(
    teacher_client: TestClient, teacher_user, foreign_group
):
    """教师读别的班的小组详情 → 403"""
    gid, _ = foreign_group
    assert teacher_client.get(f"/api/v1/teacher/groups/{gid}").status_code == 403


def test_teacher_cannot_dissolve_other_class_group(
    teacher_client: TestClient, teacher_user, foreign_group
):
    """教师解散别的班的小组 → 403"""
    gid, _ = foreign_group
    assert teacher_client.delete(f"/api/v1/teacher/groups/{gid}").status_code == 403


def test_teacher_cannot_transfer_other_class_group_leader(
    teacher_client: TestClient, teacher_user, foreign_group
):
    """教师转让别班小组的组长 → 403"""
    gid, _ = foreign_group
    resp = teacher_client.post(
        f"/api/v1/teacher/groups/{gid}/transfer-leader", json={"new_leader_id": "S006"}
    )
    assert resp.status_code == 403


def test_teacher_cannot_remove_member_of_other_class_group(
    teacher_client: TestClient, teacher_user, foreign_group
):
    """教师踢别班小组的成员 → 403"""
    gid, _ = foreign_group
    resp = teacher_client.delete(f"/api/v1/teacher/groups/{gid}/members/S006")
    assert resp.status_code == 403


def test_teacher_cannot_resolve_other_class_dissolution_request(
    teacher_client: TestClient, teacher_user, foreign_group
):
    """教师批准/拒绝别班的解散申请 → 403"""
    _, req_id = foreign_group
    assert teacher_client.post(
        f"/api/v1/teacher/group-dissolution-requests/{req_id}/approve"
    ).status_code == 403
    assert teacher_client.post(
        f"/api/v1/teacher/group-dissolution-requests/{req_id}/reject"
    ).status_code == 403


def test_teacher_dissolution_request_list_scoped(
    teacher_client: TestClient, teacher_user, foreign_group
):
    """解散申请列表不含别班的申请"""
    _, req_id = foreign_group
    resp = teacher_client.get("/api/v1/teacher/group-dissolution-requests")
    assert resp.status_code == 200, resp.json()
    assert req_id not in {r["id"] for r in resp.json()["data"]}


# ---------- fail-closed：教学班未关联任何班级 → 什么都看不到 ----------


@pytest.fixture
def unlinked_teacher_client(test_engine, seed_refs):
    """教学班**未关联任何班级**的教师客户端（旧「通配」语义下会看到全校）"""
    from datetime import date

    from app.core.security import generate_password_hash
    from app.models import Course, CourseOffering, Semester, User
    from app.models.constants import UserRoleConst
    from main import app
    from app.core.db import get_session
    from sqlmodel import Session as _Session

    with _Session(test_engine) as session:
        password_hash, salt = generate_password_hash("unlinked123")
        user = User(
            username="unlinked_teacher", name="未配关联教师",
            password_hash=password_hash, salt=salt,
            role=UserRoleConst.TEACHER, is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        course = session.exec(select(Course).where(Course.code == "UNLINK1")).first()
        if course is None:
            course = Course(code="UNLINK1", name="未关联课程")
            session.add(course)
        sem = session.exec(select(Semester).where(Semester.label == "UNLINK-SEED")).first()
        if sem is None:
            sem = Semester(label="UNLINK-SEED", start_date=date(2026, 1, 1),
                           total_weeks=20, is_current=False)
            session.add(sem)
        session.commit()
        # 关键：建教学班但**不写** course_offering_classes 关联行
        session.add(CourseOffering(
            course_id=course.id, semester_id=sem.id, teacher_id=user.id,
            teacher_name=user.name, status="active",
        ))
        session.commit()

    def get_session_override():
        with _Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app, cookies={}) as c:
        resp = c.post("/api/v1/login", json={
            "username": "unlinked_teacher", "password": "unlinked123", "role": "teacher",
        })
        assert resp.status_code == 200, resp.json()
        yield c
    app.dependency_overrides.clear()


def test_unlinked_teacher_sees_no_classes(
    unlinked_teacher_client: TestClient, seed_refs
):
    """教学班未关联班级 → 班级列表为空（fail-closed，不再通配放行全校）"""
    resp = unlinked_teacher_client.get("/api/v1/classes")
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"] == []


def test_unlinked_teacher_cannot_read_any_class(
    unlinked_teacher_client: TestClient, seed_refs
):
    """教学班未关联班级 → 任意班级的读取一律 403"""
    for cls in ("一班", "二班", "三班"):
        resp = unlinked_teacher_client.get(
            "/api/v1/teacher/groups", params={"class_id": seed_refs[cls]}
        )
        assert resp.status_code == 403, f"{cls} 应被拒绝"
