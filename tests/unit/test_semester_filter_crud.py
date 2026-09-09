"""CRUD 学期过滤测试：上学期数据不出现在当前学期查询中"""
from datetime import datetime
import pytest
from sqlmodel import Session, select

from app.models import CourseSchedule, CourseSession, CheckinRecord, ScoreLog
from app.models import Group, Question
from app.crud.schedule import get_schedules
from app.crud.course_session import get_teacher_course_sessions
from app.crud.checkin import get_all_checkins, get_student_score_logs
from app.crud.group import dissolve_group, get_groups_by_class
from app.crud.question import get_questions_by_class


@pytest.fixture(autouse=True)
def _seed_teacher(session):
    """PG 强制 FK：questions/course_sessions 的 teacher_id → users.id"""
    from app.models import User
    from app.core.security import hash_password
    session.add(User(
        id=1, username="teacher1", name="教师1",
        password_hash=hash_password("pass123"), role="teacher",
    ))
    session.commit()


@pytest.fixture
def two_term_data(session: Session):
    """造数据：上学期 + 当前学期各一批"""
    # 上学期课表/课堂/签到/日志/小组/任务/问答
    old_sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                               start_time="08:00", end_time="09:40", semester="2025-2026-2")
    new_sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                               start_time="08:00", end_time="09:40", semester="2026-2027-1")
    session.add_all([old_sched, new_sched])
    session.commit()

    old_session = CourseSession(session_code="OLD001", class_name="1班", teacher_id=1,
                                semester="2025-2026-2", status="ended")
    new_session = CourseSession(session_code="NEW001", class_name="1班", teacher_id=1,
                                semester="2026-2027-1", status="ended")
    session.add_all([old_session, new_session])
    session.commit()

    old_checkin = CheckinRecord(student_id="TEST001", session_id=old_session.id,
                                checkin_time=datetime(2026, 3, 1), semester="2025-2026-2")
    new_checkin = CheckinRecord(student_id="TEST001", session_id=new_session.id,
                                checkin_time=datetime(2026, 9, 10), semester="2026-2027-1")
    session.add_all([old_checkin, new_checkin])

    old_log = ScoreLog(student_id="TEST001", old_score=80.0, new_score=90.0, delta=10.0,
                       semester="2025-2026-2")
    new_log = ScoreLog(student_id="TEST001", old_score=90.0, new_score=95.0, delta=5.0,
                       semester="2026-2027-1")
    session.add_all([old_log, new_log])

    old_group = Group(class_name="1班", name="上学期的组", leader_student_id="TEST001",
                      semester="2025-2026-2", is_active=True)
    new_group = Group(class_name="1班", name="新学期的组", leader_student_id="TEST001",
                      semester="2026-2027-1", is_active=True)
    session.add_all([old_group, new_group])

    old_q = Question(teacher_id=1, class_name="1班", content="上学期问题", semester="2025-2026-2")
    new_q = Question(teacher_id=1, class_name="1班", content="新学期问题", semester="2026-2027-1")
    session.add_all([old_q, new_q])
    session.commit()
    return session


def test_schedules_filtered_by_current_term(two_term_data):
    schedules = get_schedules(two_term_data)
    assert len(schedules) == 1
    assert schedules[0].semester == "2026-2027-1"


def test_teacher_sessions_filtered_by_current_term(two_term_data):
    sessions = get_teacher_course_sessions(two_term_data, teacher_id=1)
    assert len(sessions) == 1
    assert sessions[0].semester == "2026-2027-1"


def test_checkins_filtered_by_current_term(two_term_data):
    checkins = get_all_checkins(two_term_data)
    assert len(checkins) == 1
    assert checkins[0].semester == "2026-2027-1"


def test_score_logs_filtered_by_current_term(two_term_data):
    logs = get_student_score_logs(two_term_data, "TEST001")
    assert len(logs) == 1
    assert logs[0].semester == "2026-2027-1"


def test_groups_filtered_by_current_term(two_term_data):
    groups = get_groups_by_class(two_term_data, "1班")
    assert len(groups) == 1
    assert groups[0].semester == "2026-2027-1"


def test_questions_filtered_by_current_term(two_term_data):
    questions = get_questions_by_class(two_term_data, "1班")
    assert len(questions) == 1
    assert questions[0].semester == "2026-2027-1"
