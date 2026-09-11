"""管理员管理 API 集成测试：学期/届/班级/课程/教学班/学籍/转班"""
from datetime import date

import pytest
from sqlmodel import Session, select

from app.models import Cohort, Class_, Course, Semester, Student, User


@pytest.fixture
def seed_basics(session):
    """届/班/学期/课程/学生/教师基础数据"""
    session.add(Cohort(year="2026", label="2026届"))
    session.add(Class_(name="一班", cohort_year="2026"))
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                         total_weeks=20, is_current=True))
    session.add(Course(code="MATH1", name="高等数学"))
    session.commit()
    cls = session.exec(select(Class_).where(Class_.name == "一班")).one()
    session.add(Student(student_id="S001", name="学生1", class_name="一班",
                        class_id=cls.id, cohort_year="2026"))
    session.add(User(username="t1", name="张老师", password_hash="x", role="teacher"))
    session.commit()


def test_semesters_crud(admin_client, seed_basics):
    """学期列表/创建/切换/重复创建 409"""
    resp = admin_client.get("/api/v1/semesters")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1

    resp = admin_client.post("/api/v1/semesters", json={
        "label": "2026-2027-2", "start_date": "2027-02-22", "total_weeks": 20,
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["label"] == "2026-2027-2"

    # 重复创建 409
    resp = admin_client.post("/api/v1/semesters", json={
        "label": "2026-2027-2", "start_date": "2027-02-22", "total_weeks": 20,
    })
    assert resp.status_code == 409

    # 切换当前学期
    resp = admin_client.get("/api/v1/semesters")
    new_sem = next(s for s in resp.json()["data"] if s["label"] == "2026-2027-2")
    resp = admin_client.post(f"/api/v1/semesters/{new_sem['id']}/activate")
    assert resp.status_code == 200

    resp = admin_client.get("/api/v1/semesters")
    current = [s for s in resp.json()["data"] if s["is_current"]]
    assert len(current) == 1
    assert current[0]["label"] == "2026-2027-2"


def test_cohorts_crud(admin_client, seed_basics):
    """届列表/创建/毕业归档"""
    resp = admin_client.post("/api/v1/cohorts", json={"year": "2027", "label": "2027届"})
    assert resp.status_code == 200

    resp = admin_client.put("/api/v1/cohorts/2026", json={"status": "graduated"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "graduated"

    resp = admin_client.put("/api/v1/cohorts/2026", json={"status": "invalid"})
    assert resp.status_code == 400


def test_classes_crud(admin_client, seed_basics, session):
    """班级列表含学生数/创建/改名/有学生删除拒绝"""
    resp = admin_client.get("/api/v1/classes")
    assert resp.status_code == 200
    cls = resp.json()["data"][0]
    assert cls["student_count"] == 1
    assert cls["display_name"] == "2026届一班"

    resp = admin_client.post("/api/v1/classes", json={
        "name": "二班", "major": "计算机", "cohort_year": "2026",
    })
    assert resp.status_code == 200

    resp = admin_client.put(f"/api/v1/classes/{cls['id']}", json={"major": "软件"})
    assert resp.status_code == 200
    assert resp.json()["data"]["major"] == "软件"

    # 有学生的班级删除拒绝
    resp = admin_client.delete(f"/api/v1/classes/{cls['id']}")
    assert resp.status_code == 409


def test_class_archive_and_restore(admin_client, seed_basics):
    """班级归档：默认列表隐藏、include_archived 可见、可恢复、无效状态 400"""
    resp = admin_client.get("/api/v1/classes")
    cls = resp.json()["data"][0]
    assert cls["status"] == "active"

    resp = admin_client.put(f"/api/v1/classes/{cls['id']}", json={"status": "archived"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "archived"

    ids = [c["id"] for c in admin_client.get("/api/v1/classes").json()["data"]]
    assert cls["id"] not in ids  # 归档后默认不可见
    ids = [c["id"] for c in admin_client.get(
        "/api/v1/classes", params={"include_archived": True}).json()["data"]]
    assert cls["id"] in ids

    resp = admin_client.put(f"/api/v1/classes/{cls['id']}", json={"status": "bogus"})
    assert resp.status_code == 400

    resp = admin_client.put(f"/api/v1/classes/{cls['id']}", json={"status": "active"})
    assert resp.status_code == 200
    ids = [c["id"] for c in admin_client.get("/api/v1/classes").json()["data"]]
    assert cls["id"] in ids


def test_delete_class_blocked_by_schedule_but_empty_deletable(
    admin_client, seed_basics, session
):
    """删除班级：被课表引用时 409 并说明来源；无引用班级可正常删除"""
    from app.models import CourseSchedule

    cls = session.exec(select(Class_).where(Class_.name == "一班")).one()
    sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).one()
    session.add(CourseSchedule(
        course_name="高等数学", class_id=cls.id, semester_id=sem.id,
        teacher_id=1, teacher_name="张老师", day_of_week=1,
        start_time="08:00", end_time="09:40",
    ))
    session.commit()

    resp = admin_client.delete(f"/api/v1/classes/{cls.id}")
    assert resp.status_code == 409
    message = resp.json()["message"]  # 统一错误包装：{"success": false, "message": ...}
    assert "课表 1 条" in message
    assert "学生 1 人" in message

    resp = admin_client.post("/api/v1/classes", json={
        "name": "空班", "major": "测试专业", "cohort_year": "2026",
    })
    assert resp.status_code == 200
    resp = admin_client.delete(f"/api/v1/classes/{resp.json()['data']['id']}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "班级已删除"


def test_create_class_requires_major(admin_client, seed_basics):
    """专业必填（缺省或空串 → 422）"""
    resp = admin_client.post("/api/v1/classes", json={
        "name": "9班", "cohort_year": "2026",
    })
    assert resp.status_code == 422

    resp = admin_client.post("/api/v1/classes", json={
        "name": "9班", "major": "", "cohort_year": "2026",
    })
    assert resp.status_code == 422


def test_batch_create_classes(admin_client, seed_basics):
    """批量创建同专业多个班级"""
    resp = admin_client.post("/api/v1/classes/batch", json={
        "cohort_year": "2026",
        "major": "计算机科学与技术",
        "names": ["1班", "2班", "3班"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["created_count"] == 3
    assert data["skipped"] == []
    names = [c["name"] for c in data["created"]]
    assert names == ["1班", "2班", "3班"]
    # display_name 由 届+专业+班级名 拼成
    assert data["created"][0]["display_name"] == "2026届计算机科学与技术1班"


def test_batch_create_skips_existing(admin_client, seed_basics):
    """已存在的班级跳过，不报错"""
    payload = {
        "cohort_year": "2026",
        "major": "软件工程",
        "names": ["1班", "2班"],
    }
    admin_client.post("/api/v1/classes/batch", json=payload)

    # 再来一次，其中 2班 已存在，3班 是新的
    resp = admin_client.post("/api/v1/classes/batch", json={
        **payload, "names": ["2班", "3班"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["created_count"] == 1
    assert data["skipped"] == ["2班"]


def test_batch_create_requires_cohort(admin_client):
    """届不存在 → 400"""
    resp = admin_client.post("/api/v1/classes/batch", json={
        "cohort_year": "1999", "major": "测试", "names": ["1班"],
    })
    assert resp.status_code == 400


def test_courses_crud(admin_client, seed_basics):
    """课程目录 CRUD"""
    resp = admin_client.post("/api/v1/courses", json={
        "code": "PHY1", "name": "大学物理", "department": "物理系",
    })
    assert resp.status_code == 200

    resp = admin_client.post("/api/v1/courses", json={
        "code": "PHY1", "name": "大学物理B",
    })
    assert resp.status_code == 409  # 编码重复

    resp = admin_client.get("/api/v1/courses")
    phy = next(c for c in resp.json()["data"] if c["code"] == "PHY1")
    resp = admin_client.put(f"/api/v1/courses/{phy['id']}", json={"status": "archived"})
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "archived"


def test_offerings_and_enrollments(admin_client, seed_basics, session):
    """教学班创建/名单导入/退课"""
    courses = admin_client.get("/api/v1/courses").json()["data"]
    sems = admin_client.get("/api/v1/semesters").json()["data"]
    course_id = courses[0]["id"]
    sem_id = sems[0]["id"]
    teacher = session.exec(select(User).where(User.username == "t1")).one()

    resp = admin_client.post("/api/v1/offerings", json={
        "course_id": course_id, "semester_id": sem_id,
        "teacher_id": teacher.id, "class_scope": "一班", "capacity": 60,
    })
    assert resp.status_code == 200
    offering_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["teacher_name"] == "张老师"

    # 批量导入选课
    resp = admin_client.post(f"/api/v1/offerings/{offering_id}/enrollments", json={
        "student_ids": ["S001", "NOPE"],
    })
    assert resp.status_code == 200
    assert resp.json()["data"] == {"imported": 1, "skipped": 1}

    # 名单
    resp = admin_client.get(f"/api/v1/offerings/{offering_id}/enrollments")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    assert resp.json()["data"][0]["student_id"] == "S001"

    # 退课
    enrollment_id = resp.json()["data"][0]["enrollment_id"]
    resp = admin_client.put(f"/api/v1/enrollments/{enrollment_id}/drop")
    assert resp.status_code == 200


def test_student_status_and_transfer(admin_client, seed_basics, session):
    """学籍状态 + 转班"""
    resp = admin_client.put("/api/v1/students/S001/status", json={"status": "suspended"})
    assert resp.status_code == 200

    resp = admin_client.put("/api/v1/students/S001/status", json={"status": "invalid"})
    assert resp.status_code == 400

    # 转班：建二班后转入
    session.add(Class_(name="二班", cohort_year="2026"))
    session.commit()
    target = session.exec(select(Class_).where(Class_.name == "二班")).one()

    resp = admin_client.put("/api/v1/students/S001/class", json={"class_id": target.id})
    assert resp.status_code == 200

    resp = admin_client.get("/api/v1/students/S001")
    assert resp.json()["data"]["class_name"] == "二班"


def test_management_requires_admin(teacher_client, student_client):
    """非管理员 403"""
    for client in (teacher_client, student_client):
        resp = client.post("/api/v1/semesters", json={
            "label": "X", "start_date": "2027-01-01", "total_weeks": 20,
        })
        assert resp.status_code == 403, client
