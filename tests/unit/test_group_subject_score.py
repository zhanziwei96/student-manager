"""小组科目分数模型测试"""
from app.models import Group, GroupScoreLog


def test_group_has_subject_score_fields():
    """小组有科目和分数字段"""
    group = Group(
        class_name="1班", name="第一组", leader_student_id="TEST001",
        subject_id=1, score=0.0
    )
    assert group.subject_id == 1
    assert group.score == 0.0
    assert group.version == 1


def test_group_score_default_zero():
    """小组分数默认 0"""
    group = Group(class_name="1班", name="第一组", leader_student_id="TEST001")
    assert group.score == 0.0


def test_group_score_log_creation():
    """小组分数日志创建"""
    log = GroupScoreLog(
        group_id=1, subject_id=1,
        old_score=0.0, new_score=5.0, delta=5.0,
        reason="课堂表现", operator="张老师", semester="2026-2027-1"
    )
    assert log.group_id == 1
    assert log.old_score == 0.0
    assert log.new_score == 5.0
    assert log.delta == 5.0
