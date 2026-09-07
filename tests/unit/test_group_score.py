"""小组分数 CRUD 测试"""
from app.models import Group, GroupScoreLog
from app.crud.group_score import update_group_score


def test_update_group_score(session):
    """更新小组分数（乐观锁 + 日志）"""
    group = Group(class_name="1班", name="第一组", leader_student_id="TEST001", score=0.0)
    session.add(group)
    session.commit()

    result = update_group_score(session, group.id, 5.0, "课堂表现", "张老师")
    assert result is not None
    assert result.score == 5.0

    # 验证日志
    log = session.query(GroupScoreLog).filter_by(group_id=group.id).first()
    assert log is not None
    assert log.old_score == 0.0
    assert log.new_score == 5.0
    assert log.delta == 5.0


def test_update_group_score_not_found(session):
    """小组不存在返回 None"""
    result = update_group_score(session, 999, 5.0, "测试", "张老师")
    assert result is None
