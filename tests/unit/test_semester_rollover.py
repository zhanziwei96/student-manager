"""学期切换脚本测试：前置安全校验"""
from datetime import date

import pytest
from sqlmodel import select
from app.models import CourseSchedule, Semester, Student
from app.core.security import hash_password
from scripts.semester_rollover import (
    _previous_term_label,
    _validate_term_combination,
)


def _make_student(session, student_id="TEST001"):
    student = Student(
        student_id=student_id, name="测试学生", class_name="测试班级",
        password_hash=hash_password("pass123"),
        is_account_enabled=True,
    )
    session.add(student)
    session.commit()
    return student


def _make_schedule(session, refs, semester="2025-2026-2"):
    """造一条指定学期的课表：学期按 label 建 Semester 行，课表引用 FK"""
    sem = session.exec(select(Semester).where(Semester.label == semester)).first()
    if sem is None:
        sem = Semester(label=semester, start_date=date(2026, 2, 23),
                       total_weeks=20, is_current=False)
        session.add(sem)
        session.commit()
        session.refresh(sem)
    schedule = CourseSchedule(
        course_name="数学", class_id=refs["一班"],
        day_of_week=1, start_time="08:00", end_time="08:45",
        semester_id=sem.id,
    )
    session.add(schedule)
    session.commit()
    return schedule


def test_previous_term_label_derives_previous_semester():
    assert _previous_term_label("2026-2027-1") == "2025-2026-2"  # 秋季 -> 上一学年下学期
    assert _previous_term_label("2025-2026-2") == "2025-2026-1"  # 春季 -> 同学年上学期
    assert _previous_term_label("bad-label") is None
    assert _previous_term_label("") is None


def test_validate_term_combination_rejects_same_term(session):
    """old == new（忘切换当前学期或忘传参数）必须拒绝"""
    with pytest.raises(SystemExit) as excinfo:
        _validate_term_combination(session, "2026-2027-1", "2026-2027-1")
    assert excinfo.value.code == 1


def test_validate_term_combination_rejects_term_without_data(session, seed_refs):
    """库中不存在该学期的数据（打错学期号）必须拒绝"""
    _make_schedule(session, seed_refs, semester="2025-2026-2")
    with pytest.raises(SystemExit) as excinfo:
        _validate_term_combination(session, "2025-2026-1", "2026-2027-1")
    assert excinfo.value.code == 1


def test_validate_term_combination_passes_with_data(session, seed_refs):
    """old != new 且库中存在 old 学期数据时放行"""
    _make_schedule(session, seed_refs, semester="2025-2026-2")
    _validate_term_combination(session, "2025-2026-2", "2026-2027-1")
