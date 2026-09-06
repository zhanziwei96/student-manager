"""科目管理 API 集成测试"""
import pytest
from sqlmodel import Session


@pytest.fixture
def session(test_engine):
    """绑定集成测试共享引擎的会话（API 客户端与测试读写同一数据库）"""
    with Session(test_engine) as s:
        yield s


def test_get_subjects(admin_client, session):
    """获取科目列表"""
    from app.models import Subject

    # 造数据
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    resp = admin_client.get("/api/v1/subjects")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "数学"


def test_update_subject_name(admin_client, session):
    """修改科目名称"""
    from app.models import Subject

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    resp = admin_client.put(f"/api/v1/subjects/{subject.id}", json={"name": "高等数学"})
    assert resp.status_code == 200

    # 验证
    session.refresh(subject)
    assert subject.name == "高等数学"


def test_derive_subjects(admin_client, session):
    """从课表推导科目"""
    from app.models import CourseSchedule

    # 造课表
    schedule = CourseSchedule(
        course_name="数学", class_name="1班", teacher_id=1,
        day_of_week=1, start_time="08:00", end_time="09:40",
        semester="2026-2027-1"
    )
    session.add(schedule)
    session.commit()

    resp = admin_client.post("/api/v1/subjects/derive")
    assert resp.status_code == 200

    # 验证：科目已创建
    from app.models import Subject
    subject = session.query(Subject).filter_by(name="数学", semester="2026-2027-1").first()
    assert subject is not None


def test_teacher_can_manage_subjects(teacher_client, session):
    """教师可管理科目"""
    resp = teacher_client.get("/api/v1/subjects")
    assert resp.status_code == 200


def test_student_cannot_manage_subjects(student_client):
    """学生不能管理科目"""
    resp = student_client.get("/api/v1/subjects")
    assert resp.status_code == 403
