"""学期切换脚本测试：分数归档幂等性 + 前置安全校验"""
import pytest
from sqlmodel import select
from app.models import CourseSchedule, ScoreLog, Student
from app.core.security import hash_password
from scripts.semester_rollover import (
    ARCHIVE_REASON_PREFIX,
    _archive_scores,
    _previous_term_label,
    _validate_term_combination,
)


def _make_student(session, student_id="TEST001", score=85.0):
    student = Student(
        student_id=student_id, name="测试学生", class_name="测试班级",
        score=score, password_hash=hash_password("pass123"),
        is_account_enabled=True,
    )
    session.add(student)
    session.commit()
    return student


def _make_schedule(session, semester="2025-2026-2"):
    schedule = CourseSchedule(
        course_name="数学", class_name="测试班级",
        day_of_week=1, start_time="08:00", end_time="08:45",
        semester=semester,
    )
    session.add(schedule)
    session.commit()
    return schedule


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


def test_archive_scores_log_operator_is_system(session):
    """归档记录的 operator 应为 system（系统归档而非人工操作）"""
    _make_student(session, score=80.0)
    _archive_scores(session, "2025-2026-2")

    log = session.exec(
        select(ScoreLog).where(ScoreLog.student_id == "TEST001")
    ).one()
    assert log.operator == "system"


def test_previous_term_label_derives_previous_semester():
    assert _previous_term_label("2026-2027-1") == "2025-2026-2"  # 秋季 -> 上一学年下学期
    assert _previous_term_label("2025-2026-2") == "2025-2026-1"  # 春季 -> 同学年上学期
    assert _previous_term_label("bad-label") is None
    assert _previous_term_label("") is None


def test_validate_term_combination_rejects_same_term(session):
    """old == new（忘更新 TERM_CFG__LABEL 或忘传参数）必须拒绝"""
    with pytest.raises(SystemExit) as excinfo:
        _validate_term_combination(session, "2026-2027-1", "2026-2027-1")
    assert excinfo.value.code == 1


def test_validate_term_combination_rejects_term_without_data(session):
    """库中不存在该学期的数据（打错学期号）必须拒绝"""
    _make_schedule(session, semester="2025-2026-2")
    with pytest.raises(SystemExit) as excinfo:
        _validate_term_combination(session, "2025-2026-1", "2026-2027-1")
    assert excinfo.value.code == 1


def test_validate_term_combination_passes_with_data(session):
    """old != new 且库中存在 old 学期数据时放行"""
    _make_schedule(session, semester="2025-2026-2")
    _validate_term_combination(session, "2025-2026-2", "2026-2027-1")
