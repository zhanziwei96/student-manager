"""双写过渡期过滤器测试"""
from sqlalchemy import text
from sqlmodel import select

from app.core.transition_filters import class_filter, semester_filter
from app.models import CheckinRecord, CourseSchedule, Cohort, Class_, Semester


def _seed(session):
    from datetime import date

    session.add(Cohort(year="2026"))
    cls = Class_(name="一班", cohort_year="2026")
    session.add(cls)
    session.commit()
    session.add(Semester(
        label="2026-2027-1", start_date=date(2026, 9, 7),
        total_weeks=20, is_current=True,
    ))
    session.commit()
    return cls


def test_class_filter_matches_backfilled_rows(session):
    """已回填行按 class_id 精确匹配"""
    cls = _seed(session)
    session.add(CheckinRecord(student_id="S1", class_name="一班", class_id=cls.id))
    session.commit()

    rows = session.exec(select(CheckinRecord).where(
        class_filter(CheckinRecord.class_id, CheckinRecord.class_name, cls.id, "一班")
    )).all()
    assert len(rows) == 1


def test_class_filter_falls_back_to_name_for_unbackfilled(session):
    """未回填行（class_id NULL）回退 class_name 匹配"""
    _seed(session)
    session.add(CheckinRecord(student_id="S2", class_name="一班", class_id=None))
    session.commit()

    rows = session.exec(select(CheckinRecord).where(
        class_filter(CheckinRecord.class_id, CheckinRecord.class_name, 999, "一班")
    )).all()
    assert len(rows) == 1  # 未回填行通过字符串兜底可见


def test_class_filter_excludes_other_cohort_same_name(session):
    """跨届同名班：class_id 过滤不混淆"""
    cls = _seed(session)
    session.add(Cohort(year="2025"))
    other = Class_(name="一班", cohort_year="2025")
    session.add(other)
    session.commit()
    session.add(CheckinRecord(student_id="S3", class_name="一班", class_id=cls.id))
    session.add(CheckinRecord(student_id="S4", class_name="一班", class_id=other.id))
    session.commit()

    rows = session.exec(select(CheckinRecord).where(
        class_filter(CheckinRecord.class_id, CheckinRecord.class_name, cls.id, "一班")
    )).all()
    assert len(rows) == 1
    assert rows[0].student_id == "S3"


def test_semester_filter_backfilled_and_fallback(session):
    """semester 过滤：已回填按 FK，未回填回退字符串"""
    _seed(session)
    sem_id = session.exec(select(Semester).where(
        Semester.label == "2026-2027-1")).one().id
    session.add(CourseSchedule(
        course_name="数学", class_name="一班", day_of_week=1,
        start_time="08:00", end_time="09:40",
        semester="2026-2027-1", semester_id=sem_id,
    ))
    session.add(CourseSchedule(
        course_name="语文", class_name="一班", day_of_week=2,
        start_time="08:00", end_time="09:40",
        semester="2026-2027-1", semester_id=None,
    ))
    session.commit()

    rows = session.exec(select(CourseSchedule).where(
        semester_filter(
            CourseSchedule.semester_id, CourseSchedule.semester,
            sem_id, "2026-2027-1",
        )
    )).all()
    assert len(rows) == 2


def test_class_filter_degrades_to_string_when_unresolved(session):
    """class_id 未解析（班级不存在）时退化为纯字符串过滤"""
    session.add(CheckinRecord(student_id="S9", class_name="一班"))
    session.commit()

    cond = class_filter(
        CheckinRecord.class_id, CheckinRecord.class_name, None, "一班",
    )
    rows = session.exec(select(CheckinRecord).where(cond)).all()
    assert len(rows) == 1


def test_semester_filter_degrades_to_string_when_unresolved(session):
    """semester_id 未解析（无当前学期行）时退化为纯字符串过滤，不误匹配旧学期"""
    from sqlmodel import select

    session.add(CourseSchedule(
        course_name="数学", class_name="一班", day_of_week=1,
        start_time="08:00", end_time="09:40", semester="2025-2026-2",
    ))
    session.add(CourseSchedule(
        course_name="语文", class_name="一班", day_of_week=2,
        start_time="08:00", end_time="09:40", semester="2026-2027-1",
    ))
    session.commit()

    cond = semester_filter(
        CourseSchedule.semester_id, CourseSchedule.semester, None, "2026-2027-1",
    )
    rows = session.exec(select(CourseSchedule).where(cond)).all()
    assert len(rows) == 1
    assert rows[0].course_name == "语文"
