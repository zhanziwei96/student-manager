"""学生科目分数 API 集成测试"""
import pytest
from sqlmodel import Session


@pytest.fixture
def session(test_engine):
    """绑定集成测试共享引擎的会话（API 客户端与测试读写同一数据库）"""
    with Session(test_engine) as s:
        yield s


def test_get_student_subjects(student_client, teacher_user, session):
    """学生获取自己所有科目分数"""
    from app.models import Subject, StudentSubjectScore

    # 造数据
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="S001", subject_id=subject.id, teacher_id=teacher_user.id,
        score=85.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    resp = student_client.get("/api/v1/students/S001/subjects")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["subject_name"] == "数学"
    assert data[0]["score"] == 85.0


def test_update_student_subject_score(teacher_client, student_user, session):
    """教师给学生某科目加减分"""
    from app.models import Subject, StudentSubjectScore

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="S001", subject_id=subject.id, teacher_id=1,
        score=80.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    resp = teacher_client.put(
        f"/api/v1/students/S001/subjects/{subject.id}/score",
        json={"score_change": 5, "reason": "课堂表现"}
    )
    assert resp.status_code == 200

    # 验证分数已更新
    session.refresh(score)
    assert score.score == 85.0


def test_get_student_subject_score_logs(student_client, session):
    """学生查看自己某科目分数历史"""
    from app.models import Subject, StudentSubjectScoreLog

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    log = StudentSubjectScoreLog(
        student_id="S001", subject_id=subject.id, teacher_id=1,
        old_score=80.0, new_score=85.0, delta=5.0,
        reason="课堂表现", operator="张老师", semester="2026-2027-1"
    )
    session.add(log)
    session.commit()

    resp = student_client.get(f"/api/v1/students/S001/subjects/{subject.id}/logs")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["old_score"] == 80.0
    assert data[0]["new_score"] == 85.0
