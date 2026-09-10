"""CRUD 学期过滤测试：上学期数据不出现在当前学期查询中"""
from datetime import date, datetime
import pytest
from sqlmodel import Session

from app.models import CourseSchedule, CourseSession, CheckinRecord
from app.models import Group, Question, Semester
from app.core.term import get_current_semester_id, invalidate_semester_cache
from app.crud.schedule import get_schedules
from app.crud.course_session import get_teacher_course_sessions
from app.crud.checkin import get_all_checkins
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
def two_term_data(session: Session, seed_refs):
    """造数据：上学期 + 当前学期各一批（当前学期实体驱动过滤）

    业务表为纯 FK 锚点：班级/学期一律引用 seed_refs 的 id（当前学期与一班）。
    """
    refs = seed_refs
    class_id = refs["一班"]
    new_sem_id = refs["semester_id"]

    old_sem = Semester(label="2025-2026-2", start_date=date(2026, 2, 23),
                       total_weeks=20, is_current=False)
    session.add(old_sem)
    session.commit()
    session.refresh(old_sem)
    old_sem_id = old_sem.id
    invalidate_semester_cache()

    # 上学期课表/课堂/签到/日志/小组/问答
    old_sched = CourseSchedule(course_name="数学", class_id=class_id, day_of_week=1,
                               start_time="08:00", end_time="09:40", semester_id=old_sem_id)
    new_sched = CourseSchedule(course_name="数学", class_id=class_id, day_of_week=1,
                               start_time="08:00", end_time="09:40", semester_id=new_sem_id)
    session.add_all([old_sched, new_sched])
    session.commit()

    old_session = CourseSession(session_code="OLD001", class_id=class_id, teacher_id=1,
                                semester_id=old_sem_id, status="ended")
    new_session = CourseSession(session_code="NEW001", class_id=class_id, teacher_id=1,
                                semester_id=new_sem_id, status="ended")
    session.add_all([old_session, new_session])
    session.commit()

    old_checkin = CheckinRecord(student_id="TEST001", session_id=old_session.id,
                                class_id=class_id, semester_id=old_sem_id,
                                checkin_time=datetime(2026, 3, 1))
    new_checkin = CheckinRecord(student_id="TEST001", session_id=new_session.id,
                                class_id=class_id, semester_id=new_sem_id,
                                checkin_time=datetime(2026, 9, 10))
    session.add_all([old_checkin, new_checkin])


    old_group = Group(class_id=class_id, name="上学期的组", leader_student_id="TEST001",
                      semester_id=old_sem_id, is_active=True)
    new_group = Group(class_id=class_id, name="新学期的组", leader_student_id="TEST001",
                      semester_id=new_sem_id, is_active=True)
    session.add_all([old_group, new_group])

    old_q = Question(teacher_id=1, class_id=class_id, content="上学期问题",
                     semester_id=old_sem_id)
    new_q = Question(teacher_id=1, class_id=class_id, content="新学期问题",
                     semester_id=new_sem_id)
    session.add_all([old_q, new_q])
    session.commit()
    return session


def test_schedules_filtered_by_current_term(two_term_data):
    schedules = get_schedules(two_term_data)
    assert len(schedules) == 1
    assert schedules[0].semester_id == get_current_semester_id(two_term_data)


def test_teacher_sessions_filtered_by_current_term(two_term_data):
    sessions = get_teacher_course_sessions(two_term_data, teacher_id=1)
    assert len(sessions) == 1
    assert sessions[0].semester_id == get_current_semester_id(two_term_data)


def test_checkins_filtered_by_current_term(two_term_data):
    checkins = get_all_checkins(two_term_data)
    assert len(checkins) == 1
    assert checkins[0].semester_id == get_current_semester_id(two_term_data)



def test_groups_filtered_by_current_term(two_term_data):
    groups = get_groups_by_class(two_term_data, "一班")
    assert len(groups) == 1
    assert groups[0].semester_id == get_current_semester_id(two_term_data)


def test_questions_filtered_by_current_term(two_term_data):
    questions = get_questions_by_class(two_term_data, "一班")
    assert len(questions) == 1
    assert questions[0].semester_id == get_current_semester_id(two_term_data)
