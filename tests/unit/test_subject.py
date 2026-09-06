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


def test_derive_subjects_from_schedules(session):
    """从课表推导科目和教师"""
    from app.crud.subject import derive_subjects_and_teachers
    from app.models import CourseSchedule

    # 造课表数据
    schedule1 = CourseSchedule(
        course_name="数学", class_name="1班", teacher_id=1,
        day_of_week=1, start_time="08:00", end_time="09:40",
        semester="2026-2027-1"
    )
    schedule2 = CourseSchedule(
        course_name="语文", class_name="1班", teacher_id=2,
        day_of_week=2, start_time="10:00", end_time="11:40",
        semester="2026-2027-1"
    )
    session.add_all([schedule1, schedule2])
    session.commit()

    result = derive_subjects_and_teachers(session)
    assert "1班" in result
    assert "数学" in result["1班"]
    assert result["1班"]["数学"] == 1
    assert result["1班"]["语文"] == 2


def test_get_subjects_by_semester(session):
    """按学期查询科目"""
    from app.crud.subject import get_subjects_by_semester

    subject1 = Subject(name="数学", semester="2026-2027-1")
    subject2 = Subject(name="语文", semester="2026-2027-1")
    subject3 = Subject(name="数学", semester="2025-2026-2")  # 上学期
    session.add_all([subject1, subject2, subject3])
    session.commit()

    subjects = get_subjects_by_semester(session, "2026-2027-1")
    assert len(subjects) == 2
    assert all(s.semester == "2026-2027-1" for s in subjects)


def test_create_subject(session):
    """创建科目"""
    from app.crud.subject import create_subject

    subject = create_subject(session, "英语")
    assert subject.name == "英语"
    assert subject.semester == "2026-2027-1"  # 默认当前学期


def test_update_subject_name(session):
    """修改科目名称"""
    from app.crud.subject import update_subject_name

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    updated = update_subject_name(session, subject.id, "高等数学")
    assert updated is not None
    assert updated.name == "高等数学"
