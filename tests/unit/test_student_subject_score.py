"""学生科目分数 CRUD 测试"""
from app.models import (
    StudentSubjectScore, StudentSubjectScoreLog, Subject, Student, CourseSchedule,
)
from app.crud.student_subject_score import (
    init_student_subject_scores,
    transfer_student_to_new_teacher,
    update_student_subject_score,
)


def test_init_student_subject_scores(session):
    """学期切换时初始化学生科目分数"""
    from app.core.security import hash_password

    # 造数据：1 个学生 + 1 个科目 + 1 条课表（供推导科目和教师）
    student = Student(
        student_id="TEST001", name="测试学生", class_name="1班",
        score=80.0, password_hash=hash_password("pass123"), is_account_enabled=True
    )
    subject = Subject(name="数学", semester="2026-2027-1")
    schedule = CourseSchedule(
        course_name="数学", class_name="1班", teacher_id=1,
        day_of_week=1, start_time="08:00", end_time="09:40",
        semester="2026-2027-1"
    )
    session.add_all([student, subject, schedule])
    session.commit()

    # 初始化
    init_student_subject_scores(session, "2026-2027-1")

    # 验证：新建记录
    score = session.query(StudentSubjectScore).filter_by(
        student_id="TEST001", subject_id=subject.id, semester="2026-2027-1"
    ).first()
    assert score is not None
    assert score.score == 70.0  # 默认分数
    assert score.teacher_id == 1  # 教师从课表推导


def test_transfer_student_to_new_teacher(session):
    """学期中换老师（继承当前分数）"""
    # 造数据：1 个科目 + 当前分数记录
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="TEST001", subject_id=subject.id, teacher_id=1,
        score=85.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    # 换老师
    transfer_student_to_new_teacher(session, subject.id, 1, 2)

    # 验证：新建记录（新老师，继承当前分数）
    new_score = session.query(StudentSubjectScore).filter_by(
        student_id="TEST001", subject_id=subject.id, teacher_id=2, semester="2026-2027-1"
    ).first()
    assert new_score is not None
    assert new_score.score == 85.0  # 继承当前分数


def test_update_student_subject_score(session):
    """更新学生科目分数（乐观锁 + 日志）"""
    # 造数据
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="TEST001", subject_id=subject.id, teacher_id=1,
        score=80.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    # 更新分数
    result = update_student_subject_score(session, "TEST001", subject.id, 5.0, "课堂表现", "张老师")
    assert result is not None
    assert result.score == 85.0
    assert result.version == 2  # 乐观锁版本号自增

    # 验证日志
    log = session.query(StudentSubjectScoreLog).filter_by(
        student_id="TEST001", subject_id=subject.id
    ).first()
    assert log is not None
    assert log.old_score == 80.0
    assert log.new_score == 85.0
    assert log.delta == 5.0


def test_update_after_transfer_lands_on_new_teacher_record(session):
    """换老师后加分应落到新老师的记录上（按 id 倒序取最新记录）"""
    # 造数据：旧老师记录
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    old_score = StudentSubjectScore(
        student_id="TEST001", subject_id=subject.id, teacher_id=1,
        score=80.0, semester="2026-2027-1"
    )
    session.add(old_score)
    session.commit()

    # 换老师：新建新老师记录（旧记录保留）
    transfer_student_to_new_teacher(session, subject.id, 1, 2)

    # 加分
    result = update_student_subject_score(session, "TEST001", subject.id, 5.0, "课堂表现", "李老师")
    assert result is not None
    assert result.score == 85.0

    # 验证：新老师记录被更新，旧老师记录不变
    new_record = session.query(StudentSubjectScore).filter_by(
        student_id="TEST001", subject_id=subject.id, teacher_id=2, semester="2026-2027-1"
    ).first()
    assert new_record is not None
    assert new_record.score == 85.0
    assert new_record.version == 2

    session.expire(old_score)
    assert old_score.score == 80.0  # 旧老师记录未被修改

    # 验证日志记录的是新老师
    log = session.query(StudentSubjectScoreLog).filter_by(
        student_id="TEST001", subject_id=subject.id
    ).first()
    assert log is not None
    assert log.teacher_id == 2
