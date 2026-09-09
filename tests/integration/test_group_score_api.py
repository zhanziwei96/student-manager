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
