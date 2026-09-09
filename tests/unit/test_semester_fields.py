"""semester 字段测试：默认自动填充当前学期，可显式指定"""
from app.models import (
    CourseSchedule, CourseSession, ScheduleAdjustment,
    CheckinRecord, ScoreLog,
    Group,
)
from app.models.question import Question


def test_semester_default_fills_current_term():
    """不显式指定时，创建对象自动带当前学期标识"""
    sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                          start_time="08:00", end_time="09:40")
    assert sched.semester == "2026-2027-1"

    sess = CourseSession(session_code="TEST001", class_name="1班", teacher_id=1)
    assert sess.semester == "2026-2027-1"

    adj = ScheduleAdjustment(schedule_id=1, week_number=1, type="cancel", created_by=1)
    assert adj.semester == "2026-2027-1"

    checkin = CheckinRecord(student_id="TEST001")
    assert checkin.semester == "2026-2027-1"

    log = ScoreLog(student_id="TEST001", old_score=80.0, new_score=90.0, delta=10.0)
    assert log.semester == "2026-2027-1"

    group = Group(class_name="1班", name="第一组", leader_student_id="TEST001")
    assert group.semester == "2026-2027-1"

    question = Question(teacher_id=1, content="今天讲了什么？")
    assert question.semester == "2026-2027-1"


def test_semester_explicit_override():
    """显式指定 semester 时保留指定值（归档脚本回填历史用）"""
    sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                          start_time="08:00", end_time="09:40", semester="2025-2026-2")
    assert sched.semester == "2025-2026-2"
