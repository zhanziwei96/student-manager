"""失物招领班级范围授权回归测试（发布 / 详情 / 列表 / 编辑）

权限真源：course_offering_classes —— 教师只在自己授课教学班关联的班级内有权限。
夹具分工：
- teacher1：一班 + 二班
- teacher2：三班 + 一班（三班是越权目标；一班用于验证跨教师共享班级的物品）
- unlinked_teacher：有教学班但未关联任何班级 → fail-closed，什么都看不到
- admin：不受限
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.jwt import create_access_token
from app.core.security import generate_password_hash
from app.crud.lost_found import get_item_class_ids
from app.models import (
    Course, CourseOffering, CourseOfferingClass, Semester, Student, User,
)
from app.models.constants import UserRoleConst
from app.models.lost_found import LostFoundItem


# ============== 夹具与辅助 ==============

@pytest.fixture
def app(test_engine):
    """测试应用实例（DB override 绑到测试引擎）"""
    from main import create_app

    def override():
        with Session(test_engine) as s:
            yield s

    a = create_app()
    a.dependency_overrides[get_session] = override
    return a


@pytest.fixture
def api(app):
    """返回「按用户建已认证客户端」的工厂"""

    def make(user_id: int, role: str, username: str) -> TestClient:
        token = create_access_token({
            "sub": str(user_id), "username": username, "name": username,
            "role": role, "is_admin": role == UserRoleConst.ADMIN,
        })
        c = TestClient(app)
        c.cookies.set("access_token", token)
        return c

    return make


def _make_user(session, username: str, role: str):
    password_hash, salt = generate_password_hash("pw123456")
    user = User(username=username, name=username, password_hash=password_hash,
                salt=salt, role=role, is_active=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _make_teacher(test_engine, username: str, class_ids) -> int:
    """创建教师 + 教学班（class_ids 为空/None 时教学班不写关联行 = fail-closed）"""
    with Session(test_engine) as s:
        user = _make_user(s, username, UserRoleConst.TEACHER)
        course = Course(code=f"LF-{username}", name=f"课程-{username}")
        sem = Semester(label=f"LFS-{username}", start_date=date(2026, 1, 1),
                       total_weeks=20, is_current=False)
        s.add(course)
        s.add(sem)
        s.commit()
        offering = CourseOffering(
            course_id=course.id, semester_id=sem.id, teacher_id=user.id,
            teacher_name=user.name, status="active",
        )
        s.add(offering)
        s.flush()
        for class_id in (class_ids or []):
            s.add(CourseOfferingClass(offering_id=offering.id, class_id=class_id))
        s.commit()
        return user.id


@pytest.fixture
def teacher1(api, test_engine, seed_refs):
    """教师A：一班 + 二班"""
    uid = _make_teacher(test_engine, "lft_a",
                        [seed_refs["一班"], seed_refs["二班"]])
    return api(uid, UserRoleConst.TEACHER, "lft_a")


@pytest.fixture
def teacher2(api, test_engine, seed_refs):
    """教师B：三班 + 一班"""
    uid = _make_teacher(test_engine, "lft_b",
                        [seed_refs["一班"], seed_refs["三班"]])
    return api(uid, UserRoleConst.TEACHER, "lft_b")


@pytest.fixture
def unlinked_teacher(api, test_engine, seed_refs):
    """教学班未关联任何班级的教师（fail-closed）"""
    uid = _make_teacher(test_engine, "lft_unlinked", None)
    return api(uid, UserRoleConst.TEACHER, "lft_unlinked")


@pytest.fixture
def admin(api, test_engine, seed_refs):
    with Session(test_engine) as s:
        uid = _make_user(s, "lf_admin", UserRoleConst.ADMIN).id
    return api(uid, UserRoleConst.ADMIN, "lf_admin")


def _make_student_client(api, test_engine, username: str, class_id) -> TestClient:
    """创建指定班级的学生用户并返回已认证客户端"""
    with Session(test_engine) as s:
        user = _make_user(s, username, UserRoleConst.STUDENT)
        s.add(Student(student_id=str(user.id), name=username, class_id=class_id,
                      password_hash="x", salt="x"))
        s.commit()
        uid = user.id
    return api(uid, UserRoleConst.STUDENT, username)


def _publish(client: TestClient, class_ids=None, title="测试物品"):
    """发布失物招领（class_ids=None 即不传该字段）"""
    data = {"title": title, "description": "描述", "location": "教室"}
    if class_ids is not None:
        data["class_ids"] = [str(cid) for cid in class_ids]
    return client.post("/api/v1/teacher/lost-found", data=data)


def _class_ids_of(session, item_id: int):
    """物品的可见班级关联行（空 = 全班级可见）"""
    return sorted(get_item_class_ids(session, [item_id]).get(item_id, []))


def _list_ids(client: TestClient):
    resp = client.get("/api/v1/teacher/lost-found")
    assert resp.status_code == 200, resp.json()
    return {i["id"] for i in resp.json()["data"]["items"]}


def _student_list_ids(client: TestClient):
    resp = client.get("/api/v1/student/lost-found")
    assert resp.status_code == 200, resp.json()
    return {i["id"] for i in resp.json()["data"]["items"]}


# ============== L1：发布范围 ==============

def test_publish_without_class_ids_converges_to_own_classes(
    api, teacher1: TestClient, session, test_engine, seed_refs
):
    """教师不传 class_ids → 收敛为自己可访问班级，不再产生「无关联行 = 全校可见」"""
    resp = _publish(teacher1, title="本班物品")
    assert resp.status_code == 200, resp.json()
    item_id = resp.json()["data"]["item_id"]

    assert _class_ids_of(session, item_id) == sorted([seed_refs["一班"], seed_refs["二班"]])

    # 三班学生看不到
    s3 = _make_student_client(api, test_engine, "lf_s3_a", seed_refs["三班"])
    assert item_id not in _student_list_ids(s3)


def test_publish_to_own_class_ok(teacher1: TestClient, session, seed_refs):
    """教师发布到自己班级 → 成功，可见范围就是该班"""
    resp = _publish(teacher1, class_ids=[seed_refs["一班"]], title="一班物品")
    assert resp.status_code == 200, resp.json()
    item_id = resp.json()["data"]["item_id"]
    assert _class_ids_of(session, item_id) == [seed_refs["一班"]]


def test_publish_to_foreign_class_forbidden(teacher1: TestClient, session, seed_refs):
    """教师发布到别的班的物品 → 403，且不落库"""
    resp = _publish(teacher1, class_ids=[seed_refs["三班"]], title="越权物品")
    assert resp.status_code == 403, resp.json()

    assert session.exec(select(LostFoundItem)).all() == []


def test_publish_mixed_own_and_foreign_class_forbidden(
    teacher1: TestClient, session, seed_refs
):
    """班级列表里混入一个无权班级 → 整体 403，不落库"""
    resp = _publish(teacher1, class_ids=[seed_refs["一班"], seed_refs["三班"]])
    assert resp.status_code == 403, resp.json()

    assert session.exec(select(LostFoundItem)).all() == []


def test_admin_publish_without_class_ids_is_global(
    api, admin: TestClient, session, test_engine, seed_refs
):
    """管理员不传 class_ids → 保持原语义「所有班级可见」（无关联行）"""
    resp = _publish(admin, title="全校可见物品")
    assert resp.status_code == 200, resp.json()
    item_id = resp.json()["data"]["item_id"]

    assert _class_ids_of(session, item_id) == []
    s3 = _make_student_client(api, test_engine, "lf_s3_b", seed_refs["三班"])
    assert item_id in _student_list_ids(s3)


def test_unlinked_teacher_cannot_publish(unlinked_teacher: TestClient, seed_refs):
    """教学班未关联任何班级 → 不能发布（fail-closed）"""
    assert _publish(unlinked_teacher, title="无权限物品").status_code == 403
    assert _publish(
        unlinked_teacher, class_ids=[seed_refs["一班"]], title="无权限物品"
    ).status_code == 403


# ============== L2：详情（含认领记录 / 联系方式） ==============

def test_teacher_cannot_read_other_teacher_item_detail(
    api, teacher1: TestClient, teacher2: TestClient, test_engine, seed_refs
):
    """教师读别人发布的物品详情 → 403，且响应不含认领人学号/联系方式"""
    resp = _publish(teacher2, class_ids=[seed_refs["三班"]], title="三班物品")
    item_id = resp.json()["data"]["item_id"]

    # 三班学生认领（详情里最敏感的数据）
    s3 = _make_student_client(api, test_engine, "lf_s3_c", seed_refs["三班"])
    claim = s3.post(f"/api/v1/student/lost-found/{item_id}/claim",
                    json={"contact": "13800138000", "message": "是我的"})
    assert claim.status_code == 200, claim.json()

    resp = teacher1.get(f"/api/v1/teacher/lost-found/{item_id}")
    assert resp.status_code == 403, resp.json()
    assert "13800138000" not in resp.text


def test_teacher_can_read_own_item_detail(
    api, teacher1: TestClient, test_engine, seed_refs
):
    """教师读自己发布的物品详情 → 200（含认领记录）"""
    item_id = _publish(teacher1, class_ids=[seed_refs["一班"]]).json()["data"]["item_id"]

    s1 = _make_student_client(api, test_engine, "lf_s1_a", seed_refs["一班"])
    s1.post(f"/api/v1/student/lost-found/{item_id}/claim",
            json={"contact": "13900139000", "message": "我的"})

    resp = teacher1.get(f"/api/v1/teacher/lost-found/{item_id}")
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["claims"][0]["contact"] == "13900139000"


def test_shared_class_item_listed_but_detail_forbidden(
    teacher1: TestClient, teacher2: TestClient, seed_refs
):
    """刻意的取舍：别人发布的「可见范围含我班」物品进得了列表，但详情/认领记录
    仍按发布者收敛（403）——详情含认领人学号与联系方式，不因班级可见而放开。
    """
    shared_id = _publish(teacher2, class_ids=[seed_refs["一班"]]).json()["data"]["item_id"]

    assert shared_id in _list_ids(teacher1)
    assert teacher1.get(f"/api/v1/teacher/lost-found/{shared_id}").status_code == 403


def test_admin_can_read_any_item_detail(
    admin: TestClient, teacher2: TestClient, seed_refs
):
    """管理员读任意物品详情 → 200"""
    item_id = _publish(teacher2, class_ids=[seed_refs["三班"]]).json()["data"]["item_id"]
    resp = admin.get(f"/api/v1/teacher/lost-found/{item_id}")
    assert resp.status_code == 200, resp.json()


# ============== L3：列表范围 ==============

def test_list_excludes_other_class_items(
    teacher1: TestClient, teacher2: TestClient, seed_refs
):
    """别人班（三班）限定的物品不出现在自己的列表里"""
    foreign_id = _publish(teacher2, class_ids=[seed_refs["三班"]]).json()["data"]["item_id"]
    own_id = _publish(teacher1, class_ids=[seed_refs["二班"]]).json()["data"]["item_id"]

    ids = _list_ids(teacher1)
    assert own_id in ids
    assert foreign_id not in ids


def test_list_includes_own_and_global_items(
    teacher1: TestClient, admin: TestClient, teacher2: TestClient, seed_refs
):
    """自己的物品 + 全班级可见的物品都在列表里（total 与条数一致，不是分页假象）"""
    own_id = _publish(teacher1, class_ids=[seed_refs["二班"]]).json()["data"]["item_id"]
    global_id = _publish(admin, title="全校可见").json()["data"]["item_id"]
    foreign_id = _publish(teacher2, class_ids=[seed_refs["三班"]]).json()["data"]["item_id"]

    resp = teacher1.get("/api/v1/teacher/lost-found")
    assert resp.status_code == 200, resp.json()
    ids = {i["id"] for i in resp.json()["data"]["items"]}
    assert {own_id, global_id} <= ids
    assert foreign_id not in ids
    assert resp.json()["data"]["total"] == len(ids) == 2


def test_list_includes_items_scoped_to_own_class(
    teacher1: TestClient, teacher2: TestClient, seed_refs
):
    """别人发布的、但可见范围含自己班级（一班）的物品 → 出现在列表里"""
    shared_id = _publish(teacher2, class_ids=[seed_refs["一班"]]).json()["data"]["item_id"]
    assert shared_id in _list_ids(teacher1)


def test_unlinked_teacher_list_empty(
    unlinked_teacher: TestClient, teacher1: TestClient, admin: TestClient, seed_refs
):
    """教学班未关联班级 → 列表为空（fail-closed，即便库里有其他物品）"""
    _publish(teacher1, class_ids=[seed_refs["一班"]])
    _publish(admin, title="全校可见")

    resp = unlinked_teacher.get("/api/v1/teacher/lost-found")
    assert resp.status_code == 200, resp.json()
    assert resp.json()["data"]["items"] == []
    assert resp.json()["data"]["total"] == 0


def test_admin_list_unscoped(
    admin: TestClient, teacher1: TestClient, teacher2: TestClient, seed_refs
):
    """管理员列表不受限（含各班限定物品 + 自己发布的）"""
    a = _publish(teacher1, class_ids=[seed_refs["一班"]]).json()["data"]["item_id"]
    b = _publish(teacher2, class_ids=[seed_refs["三班"]]).json()["data"]["item_id"]
    assert {a, b} <= _list_ids(admin)


# ============== 编辑：可见范围同样收敛 ==============

def test_update_to_foreign_class_forbidden(teacher1: TestClient, session, seed_refs):
    """教师把自己的物品改成别的班可见 → 403，可见范围不变"""
    item_id = _publish(teacher1, class_ids=[seed_refs["一班"]]).json()["data"]["item_id"]

    resp = teacher1.put(f"/api/v1/teacher/lost-found/{item_id}",
                        data={"class_ids": [str(seed_refs["三班"])]})
    assert resp.status_code == 403, resp.json()
    assert _class_ids_of(session, item_id) == [seed_refs["一班"]]


def test_clear_class_scope_converges_to_own_classes(
    teacher1: TestClient, session, seed_refs
):
    """教师 clear_class_scope → 收敛为可访问班级（不是「全校可见」，否则可绕过发布限制）"""
    item_id = _publish(teacher1, class_ids=[seed_refs["二班"]]).json()["data"]["item_id"]

    resp = teacher1.put(f"/api/v1/teacher/lost-found/{item_id}",
                        data={"clear_class_scope": "true"})
    assert resp.status_code == 200, resp.json()
    assert _class_ids_of(session, item_id) == sorted([seed_refs["一班"], seed_refs["二班"]])


# ============== 学生端行为不变 ==============

def test_student_list_unchanged(
    api, teacher1: TestClient, teacher2: TestClient, admin: TestClient,
    test_engine, seed_refs
):
    """学生端可见性规则不变：公开物品 + 本班物品可见，他班限定物品不可见"""
    own_id = _publish(teacher1, class_ids=[seed_refs["一班"]]).json()["data"]["item_id"]
    global_id = _publish(admin, title="全校可见").json()["data"]["item_id"]
    foreign_id = _publish(teacher2, class_ids=[seed_refs["三班"]]).json()["data"]["item_id"]

    s1 = _make_student_client(api, test_engine, "lf_s1_b", seed_refs["一班"])
    ids = _student_list_ids(s1)
    assert {own_id, global_id} <= ids
    assert foreign_id not in ids
