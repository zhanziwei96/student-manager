"""学期切换脚本测试：分数归档幂等性"""
from sqlmodel import select
from app.models import Student, ScoreLog
from app.core.security import hash_password
from scripts.semester_rollover import _archive_scores, ARCHIVE_REASON_PREFIX


def _make_student(session, student_id="TEST001", score=85.0):
    student = Student(
        student_id=student_id, name="测试学生", class_name="测试班级",
        score=score, password_hash=hash_password("pass123"),
        is_account_enabled=True,
    )
    session.add(student)
    session.commit()
    return student


def test_archive_scores_writes_archive_log_and_resets(session):
    _make_student(session, score=85.0)
    archived, skipped = _archive_scores(session, "2025-2026-2")
    assert archived == 1
    assert skipped == 0

    student = session.get(Student, "TEST001")
    assert student.score == 0.0

    logs = session.exec(
        select(ScoreLog).where(ScoreLog.student_id == "TEST001")
    ).all()
    assert len(logs) == 1
    assert logs[0].reason == f"{ARCHIVE_REASON_PREFIX} 2025-2026-2"
    assert logs[0].old_score == 85.0
    assert logs[0].new_score == 0.0
    assert logs[0].delta == -85.0
    assert logs[0].semester == "2025-2026-2"


def test_archive_scores_is_idempotent(session):
    """重复执行不产生二次归档"""
    _make_student(session, score=85.0)
    _archive_scores(session, "2025-2026-2")
    # 模拟第二次执行：分数已重置为 0
    archived, skipped = _archive_scores(session, "2025-2026-2")
    assert archived == 0
    assert skipped == 1

    logs = session.exec(select(ScoreLog).where(ScoreLog.student_id == "TEST001")).all()
    assert len(logs) == 1
