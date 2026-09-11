"""成绩排行榜 API 集成测试：教师教学班/权限修复/4 榜/学生本班榜"""
from datetime import date

import pytest
from sqlmodel import select

from app.models import (
    Class_, Course, CourseOffering, CourseOfferingClass, Enrollment, Semester, Student, User,
)


@pytest.fixture
def seed_rankings(session, teacher_user):
    """届/班/学期/课程/教学班/选课基础数据（teacher1 的数学教学班关联一班+二班）"""
    # 班级可能已由 conftest 的 student_user fixture 创建，get-or-create
    cls1 = session.exec(select(Class_).where(Class_.name == "一班")).first()
    if cls1 is None:
        cls1 = Class_(name="一班", cohort_year="2026")
        session.add(cls1)
    cls2 = session.exec(select(Class_).where(Class_.name == "二班")).first()
    if cls2 is None:
        cls2 = Class_(name="二班", cohort_year="2026")
        session.add(cls2)
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                         total_weeks=20, is_current=True))
    math = session.exec(select(Course).where(Course.code == "MATH1")).first()
    if math is None:
        math = Course(code="MATH1", name="高等数学")
        session.add(math)
    eng = session.exec(select(Course).where(Course.code == "ENG1")).first()
    if eng is None:
        eng = Course(code="ENG1", name="大学英语")
        session.add(eng)
    other = User(username="t2", name="李老师", password_hash="x", role="teacher")
    session.add(other)
    session.commit()
    sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).one()
    t1 = teacher_user  # conftest fixture（teacher1）
    # uix_offering=(course,semester,teacher)：同一教师同课同学期只能一个教学班，
    # 跨班范围由 course_offering_classes 关联行表达（m 关联一班+二班）
    m1 = CourseOffering(course_id=math.id, semester_id=sem.id, teacher_id=t1.id,
                        teacher_name=t1.name, status="active")
    e1 = CourseOffering(course_id=eng.id, semester_id=sem.id, teacher_id=other.id,
                        teacher_name="李老师", status="active")
    session.add_all([m1, e1])
    session.flush()
    session.add_all([
        CourseOfferingClass(offering_id=m1.id, class_id=cls1.id),
        CourseOfferingClass(offering_id=m1.id, class_id=cls2.id),
        CourseOfferingClass(offering_id=e1.id, class_id=cls1.id),
    ])
    session.commit()
    # S001 可能已由 conftest 的 student_user fixture 创建（学生视角用例），get-or-create
    s1 = session.get(Student, "S001")
    if s1 is None:
        s1 = Student(student_id="S001", name="学生1", class_name="一班")
        session.add(s1)
    s1.class_id = cls1.id
    session.add_all([
        Student(student_id="S002", name="学生2", class_name="一班", class_id=cls1.id),
        Student(student_id="S003", name="学生3", class_name="二班", class_id=cls2.id),
    ])
    session.commit()
    session.add_all([
        Enrollment(student_id="S001", offering_id=m1.id, semester_id=sem.id,
                   score=90.0, status="enrolled"),
        Enrollment(student_id="S002", offering_id=m1.id, semester_id=sem.id,
                   score=80.0, status="enrolled"),
        Enrollment(student_id="S003", offering_id=m1.id, semester_id=sem.id,
                   score=85.0, status="enrolled"),
        Enrollment(student_id="S001", offering_id=e1.id, semester_id=sem.id,
                   score=70.0, status="enrolled"),
    ])
    session.commit()
    return {"math": math, "m1": m1, "e1": e1, "class_1": cls1.id}


def test_teacher_offerings_list_only_own(teacher_client, seed_rankings):
    """教师教学班列表：仅本人授课，含课程信息与选课人数"""
    resp = teacher_client.get("/api/v1/teacher/offerings")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1  # teacher1 的数学教学班（李老师的英语班不在内）
    assert data[0]["course_code"] == "MATH1"
    assert data[0]["class_scope"] == "2026届一班、2026届二班"  # 关联表 display_name 拼装
    assert data[0]["enrolled_count"] == 3


def test_teacher_cannot_list_other_teacher_enrollments(teacher_client, seed_rankings):
    """教师不能查看他人教学班名单 → 403"""
    resp = teacher_client.get(f"/api/v1/offerings/{seed_rankings['e1'].id}/enrollments")
    assert resp.status_code == 403


def test_teacher_can_list_own_enrollments(teacher_client, seed_rankings):
    """教师可查看自己教学班名单 → 200"""
    resp = teacher_client.get(f"/api/v1/offerings/{seed_rankings['m1'].id}/enrollments")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 3


def test_individual_ranking_class_scope(teacher_client, seed_rankings):
    """个人榜·班内：按行政班过滤并按分数降序排名"""
    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["math"].id,
        "scope": "class", "class_id": seed_rankings["class_1"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["course_name"] == "高等数学"
    assert data["classes"] == ["2026届一班"]  # 班级展示名
    assert [e["student_id"] for e in data["entries"]] == ["S001", "S002"]
    assert data["entries"][0]["score"] == 90.0
    assert data["entries"][0]["rank"] == 1


def test_individual_ranking_all_scope(teacher_client, seed_rankings):
    """个人榜·跨班：教师该科目全部教学班合并排名"""
    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["math"].id, "scope": "all",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [e["student_id"] for e in data["entries"]] == ["S001", "S003", "S002"]
    assert sorted(data["classes"]) == ["2026届一班", "2026届二班"]


def test_ranking_teacher_cannot_query_other_course(teacher_client, seed_rankings):
    """教师不能查非本人授课科目排行榜 → 403"""
    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["e1"].course_id, "scope": "all",
    })
    assert resp.status_code == 403


def test_student_ranking_forced_own_class(student_client, seed_rankings):
    """学生排行榜：scope 强制 class 且班取学生自己（S001 在一班）"""
    resp = student_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["math"].id, "scope": "all",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["scope"] == "class"
    assert [e["student_id"] for e in data["entries"]] == ["S001", "S002"]  # 只含一班
    assert data["my_rank"]["student_id"] == "S001"
    assert data["my_rank"]["rank"] == 1


def test_group_ranking(teacher_client, seed_rankings, session):
    """小组榜：按科目+班级取小组累计分排名，含成员名单"""
    from app.models import Group, GroupMember

    sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).one()
    g1 = Group(name="第一组", class_id=seed_rankings["class_1"], course_id=seed_rankings["math"].id,
               semester_id=sem.id, leader_student_id="S001", score=95.0, is_active=True)
    g2 = Group(name="第二组", class_id=seed_rankings["class_1"], course_id=seed_rankings["math"].id,
               semester_id=sem.id, leader_student_id="S003", score=88.0, is_active=True)
    session.add_all([g1, g2])
    session.commit()
    session.add_all([
        GroupMember(group_id=g1.id, student_id="S001"),
        GroupMember(group_id=g2.id, student_id="S003"),
    ])
    session.commit()

    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "group", "course_id": seed_rankings["math"].id,
        "scope": "class", "class_id": seed_rankings["class_1"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [e["name"] for e in data["entries"]] == ["第一组", "第二组"]
    assert data["entries"][0]["score"] == 95.0
    assert data["entries"][0]["members"] == ["学生1"]
