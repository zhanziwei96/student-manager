"""科目模型测试"""
from app.models import Subject, StudentSubjectScore, StudentSubjectScoreLog


def test_subject_creation():
    """科目创建"""
    subject = Subject(name="数学", semester="2026-2027-1")
    assert subject.name == "数学"
    assert subject.semester == "2026-2027-1"


def test_student_subject_score_creation():
    """学生科目分数创建"""
    score = StudentSubjectScore(
        student_id="TEST001",
        subject_id=1,
        teacher_id=1,
        score=85.0,
        semester="2026-2027-1"
    )
    assert score.student_id == "TEST001"
    assert score.subject_id == 1
    assert score.teacher_id == 1
    assert score.score == 85.0


def test_student_subject_score_log_creation():
    """学生科目分数日志创建"""
    log = StudentSubjectScoreLog(
        student_id="TEST001",
        subject_id=1,
        teacher_id=1,
        old_score=80.0,
        new_score=85.0,
        delta=5.0,
        reason="课堂表现",
        operator="张老师",
        semester="2026-2027-1"
    )
    assert log.old_score == 80.0
    assert log.new_score == 85.0
    assert log.delta == 5.0
