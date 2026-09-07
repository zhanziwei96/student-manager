"""小组分数 API 集成测试"""
import pytest
from sqlmodel import Session


@pytest.fixture
def session(test_engine):
    """绑定集成测试共享引擎的会话（API 客户端与测试读写同一数据库）"""
    with Session(test_engine) as s:
        yield s


def test_update_group_score(teacher_client, session):
    """教师给小组加减分"""
    from app.models import Group

    group = Group(class_name="一班", name="第一组", leader_student_id="S001", score=0.0)
    session.add(group)
    session.commit()

    resp = teacher_client.put(
        f"/api/v1/groups/{group.id}/score",
        json={"score_change": 5, "reason": "课堂表现"}
    )
    assert resp.status_code == 200

    session.refresh(group)
    assert group.score == 5.0


def test_get_group_score_logs(teacher_client, session):
    """获取小组分数日志"""
    from app.models import Group, GroupScoreLog

    group = Group(class_name="一班", name="第一组", leader_student_id="S001")
    session.add(group)
    session.commit()

    log = GroupScoreLog(group_id=group.id, old_score=0.0, new_score=5.0, delta=5.0, reason="课堂表现", operator="张老师", semester="2026-2027-1")
    session.add(log)
    session.commit()

    resp = teacher_client.get(f"/api/v1/groups/{group.id}/score-logs")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["old_score"] == 0.0


def test_group_leaderboard(teacher_client, session):
    """小组排行榜（按科目+班级）"""
    from app.models import Group, Subject

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    group1 = Group(class_name="一班", name="第一组", leader_student_id="S001", subject_id=subject.id, score=10.0)
    group2 = Group(class_name="一班", name="第二组", leader_student_id="S002", subject_id=subject.id, score=20.0)
    session.add_all([group1, group2])
    session.commit()

    resp = teacher_client.get(f"/api/v1/groups/leaderboard?subject_id={subject.id}&class_name=一班")
    assert resp.status_code == 200
    data = resp.json()["data"]
    groups = data["groups"]
    assert len(groups) == 2
    assert groups[0]["group_name"] == "第二组"  # 分数高的排前
    assert groups[0]["score"] == 20.0


def test_group_leaderboard_teacher_cross_class_forbidden(teacher_client, session):
    """教师访问非本班排行榜 → 403"""
    from app.models import Group, Subject

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    group = Group(class_name="三班", name="其他班小组", leader_student_id="S003", subject_id=subject.id, score=10.0)
    session.add(group)
    session.commit()

    resp = teacher_client.get(f"/api/v1/groups/leaderboard?subject_id={subject.id}&class_name=三班")
    assert resp.status_code == 403


def test_group_leaderboard_teacher_without_class_restricted(teacher_client, session):
    """教师未传 class_name 时仅返回本班小组（限制在 assigned_classes 内）"""
    from app.models import Group, Subject

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    own = Group(class_name="一班", name="本班小组", leader_student_id="S001", subject_id=subject.id, score=10.0)
    other = Group(class_name="三班", name="他班小组", leader_student_id="S003", subject_id=subject.id, score=30.0)
    session.add_all([own, other])
    session.commit()

    resp = teacher_client.get(f"/api/v1/groups/leaderboard?subject_id={subject.id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    groups = data["groups"]
    class_names = {g["class_name"] for g in groups}
    assert "一班" in class_names
    assert "三班" not in class_names
