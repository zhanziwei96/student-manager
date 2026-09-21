"""排行榜 / 教学班列表「班级范围收敛」回归测试

覆盖两类越权：
- R1 GET /rankings：教师曾可借 scope=class + 任意 class_id 读他班个人榜/小组榜，
  scope=all 时更可读同科目**其他教师**教学班的全部学生数据。
- R2 GET /offerings：教师曾可拿到本学期全部教学班（含他人 teacher_id / class_ids）。

范围唯一真源为 course_offering_classes 关联表（见 app/api/deps.py）。
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    Class_, Course, CourseOffering, CourseOfferingClass, Enrollment, Group, GroupMember,
    Semester, Student, User,
)

API = "/api/v1"


def _class_id(session, name: str) -> int:
    cls = session.exec(select(Class_).where(Class_.name == name)).first()
    if cls is None:
        cls = Class_(name=name, cohort_year="2026")
        session.add(cls)
        session.flush()
    return cls.id


def _course(session, code: str, name: str) -> Course:
    course = session.exec(select(Course).where(Course.code == code)).first()
    if course is None:
        course = Course(code=code, name=name)
        session.add(course)
        session.flush()
    return course


def _student(session, sid: str, name: str, class_id: int) -> Student:
    stu = session.get(Student, sid)
    if stu is None:
        stu = Student(student_id=sid, name=name, class_name="", class_id=class_id)
        session.add(stu)
    stu.class_id = class_id
    return stu


@pytest.fixture
def scope_seed(test_engine, teacher_user, session):
    """teacher1（可访问一班/二班）| t2 李老师（三班）| t3（教学班未配班级关联）

    - MATH1@当前学期：teacher1 教学班关联一班+二班（S001 选课）；t2 教学班关联三班（S004 选课）
    - MATH2@当前学期：t3 教学班**无任何班级关联**（S006 选课）
    """
    from app.core.security import generate_password_hash

    cls1 = _class_id(session, "一班")
    cls2 = _class_id(session, "二班")
    cls3 = _class_id(session, "三班")
    sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).first()
    if sem is None:
        sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                       total_weeks=20, is_current=True)
        session.add(sem)
        session.flush()
    math = _course(session, "MATH1", "高等数学")
    math2 = _course(session, "MATH2", "线性代数")

    pwd, salt = generate_password_hash("teacher123")
    t2 = User(username="t2", name="李老师", password_hash=pwd, salt=salt,
              role="teacher", is_active=True)
    t3 = User(username="t3", name="王老师", password_hash=pwd, salt=salt,
              role="teacher", is_active=True)
    session.add_all([t2, t3])
    session.flush()

    m1 = CourseOffering(course_id=math.id, semester_id=sem.id, teacher_id=teacher_user.id,
                        teacher_name=teacher_user.name, status="active")
    m2 = CourseOffering(course_id=math.id, semester_id=sem.id, teacher_id=t2.id,
                        teacher_name="李老师", status="active")
    m3 = CourseOffering(course_id=math2.id, semester_id=sem.id, teacher_id=t3.id,
                        teacher_name="王老师", status="active")
    session.add_all([m1, m2, m3])
    session.flush()
    session.add_all([
        CourseOfferingClass(offering_id=m1.id, class_id=cls1),
        CourseOfferingClass(offering_id=m1.id, class_id=cls2),
        CourseOfferingClass(offering_id=m2.id, class_id=cls3),
        # m3（t3）刻意不配关联：fail-closed 场景
    ])
    _student(session, "S001", "学生1", cls1)
    _student(session, "S004", "学生4", cls3)
    _student(session, "S006", "学生6", cls1)
    session.flush()
    session.add_all([
        Enrollment(student_id="S001", offering_id=m1.id, semester_id=sem.id,
                   score=90.0, status="enrolled"),
        Enrollment(student_id="S004", offering_id=m2.id, semester_id=sem.id,
                   score=95.0, status="enrolled"),  # 分数更高：旧行为下会压过 S001
        Enrollment(student_id="S006", offering_id=m3.id, semester_id=sem.id,
                   score=99.0, status="enrolled"),
    ])
    g1 = Group(name="第一组", class_id=cls1, course_id=math.id, semester_id=sem.id,
               leader_student_id="S001", score=95.0, is_active=True)
    g3 = Group(name="三班组", class_id=cls3, course_id=math.id, semester_id=sem.id,
               leader_student_id="S004", score=99.0, is_active=True)
    session.add_all([g1, g3])
    session.flush()
    session.add_all([
        GroupMember(group_id=g1.id, student_id="S001"),
        GroupMember(group_id=g3.id, student_id="S004"),
    ])
    session.commit()
    return {"math": math, "math2": math2, "m1": m1, "m2": m2,
            "class_1": cls1, "class_3": cls3}


@pytest.fixture
def make_teacher_client(test_engine):
    """工厂：为任意教师账号创建已登录客户端（teardown 统一关闭）"""
    from app.core.db import get_session
    from main import app

    clients = []

    def _make(username: str, password: str) -> TestClient:
        def get_session_override():
            with Session(test_engine) as s:
                yield s

        app.dependency_overrides[get_session] = get_session_override
        c = TestClient(app, cookies={})
        c.__enter__()
        resp = c.post(f"{API}/login", json={
            "username": username, "password": password, "role": "teacher"})
        assert resp.status_code == 200, resp.json()
        clients.append(c)
        return c

    yield _make
    for c in clients:
        c.__exit__(None, None, None)
    app.dependency_overrides.clear()


# ---------- R1: GET /rankings ----------

def test_teacher_class_scope_rejects_unowned_class(teacher_client, scope_seed):
    """scope=class 指定非本人班级 → 403；本人班级 → 200"""
    params = {"type": "individual", "course_id": scope_seed["math"].id, "scope": "class"}
    denied = teacher_client.get(f"{API}/rankings", params={**params, "class_id": scope_seed["class_3"]})
    assert denied.status_code == 403

    ok = teacher_client.get(f"{API}/rankings", params={**params, "class_id": scope_seed["class_1"]})
    assert ok.status_code == 200
    assert [e["student_id"] for e in ok.json()["data"]["entries"]] == ["S001"]


def test_teacher_scope_all_excludes_other_teacher_classes(teacher_client, scope_seed):
    """scope=all：同科目其他教师教学班（三班 S004，95 分）不得入榜"""
    resp = teacher_client.get(f"{API}/rankings", params={
        "type": "individual", "course_id": scope_seed["math"].id, "scope": "all"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [e["student_id"] for e in data["entries"]] == ["S001"]
    assert data["entries"][0]["score"] == 90.0
    assert data["classes"] == ["2026届一班"]


def test_teacher_scope_class_without_class_id_converges(teacher_client, scope_seed):
    """scope=class 但不传 class_id：收敛到本人班级，而非返回全校"""
    resp = teacher_client.get(f"{API}/rankings", params={
        "type": "individual", "course_id": scope_seed["math"].id, "scope": "class"})
    assert resp.status_code == 200
    assert [e["student_id"] for e in resp.json()["data"]["entries"]] == ["S001"]


def test_teacher_group_ranking_excludes_other_teacher_classes(teacher_client, scope_seed):
    """小组榜 scope=all：他班小组及其成员名单不得入榜"""
    resp = teacher_client.get(f"{API}/rankings", params={
        "type": "group", "course_id": scope_seed["math"].id, "scope": "all"})
    assert resp.status_code == 200
    entries = resp.json()["data"]["entries"]
    assert [e["name"] for e in entries] == ["第一组"]
    assert entries[0]["members"] == ["学生1"]


def test_teacher_group_ranking_rejects_unowned_class(teacher_client, scope_seed):
    """小组榜 scope=class 指定他班 → 403"""
    resp = teacher_client.get(f"{API}/rankings", params={
        "type": "group", "course_id": scope_seed["math"].id,
        "scope": "class", "class_id": scope_seed["class_3"]})
    assert resp.status_code == 403


def test_teacher_without_class_binding_gets_empty_ranking(make_teacher_client, scope_seed):
    """教学班未关联任何班级（fail-closed）：即使有选课成绩也返回空榜，而非全校数据"""
    c = make_teacher_client("t3", "teacher123")
    resp = c.get(f"{API}/rankings", params={
        "type": "individual", "course_id": scope_seed["math2"].id, "scope": "all"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["entries"] == []  # 旧行为：S006（99 分）会被返回
    assert data["classes"] == []


def test_teacher_without_class_binding_forbidden_on_class_scope(make_teacher_client, scope_seed):
    """教学班未关联任何班级 + 显式 class_id → 403（fail-closed）"""
    c = make_teacher_client("t3", "teacher123")
    resp = c.get(f"{API}/rankings", params={
        "type": "individual", "course_id": scope_seed["math2"].id,
        "scope": "class", "class_id": scope_seed["class_1"]})
    assert resp.status_code == 403


def test_admin_ranking_not_restricted(admin_client, scope_seed):
    """admin 不受班级范围限制（保持原行为）"""
    resp = admin_client.get(f"{API}/rankings", params={
        "type": "individual", "course_id": scope_seed["math"].id, "scope": "all"})
    assert resp.status_code == 200
    assert [e["student_id"] for e in resp.json()["data"]["entries"]] == ["S004", "S001"]


# ---------- R2: GET /offerings ----------

def test_offerings_list_teacher_only_own(teacher_client, scope_seed):
    """教师教学班列表只含本人授课（不含他人 teacher_id/class_ids）"""
    resp = teacher_client.get(f"{API}/offerings")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [o["id"] for o in data] == [scope_seed["m1"].id]
    assert data[0]["teacher_id"] != scope_seed["m2"].teacher_id


def test_offerings_list_admin_sees_all(admin_client, scope_seed):
    """admin 仍可看到全部教学班"""
    resp = admin_client.get(f"{API}/offerings")
    assert resp.status_code == 200
    ids = {o["id"] for o in resp.json()["data"]}
    assert {scope_seed["m1"].id, scope_seed["m2"].id} <= ids
