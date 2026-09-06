"""
学生科目分数 CRUD 操作

说明：
- 乐观锁使用 version 字段（UPDATE ... WHERE id = :id AND version = :expected_version），
  语义与 crud/student.py 的 update_student_score 一致：
  只有读取到的版本未被并发修改时才更新，否则报 409。
- 学期中换老师会新建记录（旧记录保留），查询时按 id 倒序取最新记录，
  保证加分落到新老师的记录上。
"""
from typing import Optional
from sqlmodel import Session, select
from app.models import StudentSubjectScore, StudentSubjectScoreLog, Subject, Student
from app.core.term import get_current_term
from app.core.timezone import get_now
from app.core.events import event_bus, ScoreUpdated


def init_student_subject_scores(session: Session, new_semester: str):
    """学期切换时初始化学生科目分数（清零为默认分数）

    前提：新学期课表已导入（科目和教师从课表推导）
    """
    from app.crud.subject import derive_subjects_and_teachers
    from app.core.config import get_settings

    # 推导科目和教师
    subject_teachers = derive_subjects_and_teachers(session)
    default_score = get_settings().score.default_score

    # 为每个学生每个科目新建记录（score=默认分数，teacher_id 从课表推导）
    students = session.exec(select(Student).where(Student.is_account_enabled.is_(True))).all()
    for student in students:
        class_name = student.class_name
        if class_name in subject_teachers:
            for subject_name, teacher_id in subject_teachers[class_name].items():
                # 查科目 ID
                subject = session.exec(
                    select(Subject).where(Subject.name == subject_name, Subject.semester == new_semester)
                ).first()
                if subject:
                    # 新建记录
                    score_record = StudentSubjectScore(
                        student_id=student.student_id,
                        subject_id=subject.id,
                        teacher_id=teacher_id,
                        score=default_score,
                        semester=new_semester,
                    )
                    session.add(score_record)

    session.commit()


def transfer_student_to_new_teacher(
    session: Session,
    subject_id: int,
    old_teacher_id: int,
    new_teacher_id: int,
):
    """学期中换老师（继承当前分数）"""
    # 查当前学期该科目该老师的所有学生
    students = session.exec(
        select(StudentSubjectScore).where(
            StudentSubjectScore.subject_id == subject_id,
            StudentSubjectScore.teacher_id == old_teacher_id,
            StudentSubjectScore.semester == get_current_term(),
        )
    ).all()

    for record in students:
        # 新建记录（新老师，继承当前分数）
        new_record = StudentSubjectScore(
            student_id=record.student_id,
            subject_id=subject_id,
            teacher_id=new_teacher_id,
            score=record.score,  # 继承当前分数
            semester=get_current_term(),
        )
        session.add(new_record)

    session.commit()


def update_student_subject_score(
    session: Session,
    student_id: str,
    subject_id: int,
    delta: float,
    reason: str,
    operator: str,
) -> Optional[StudentSubjectScore]:
    """更新学生科目分数（乐观锁 + 日志，复用学生分数逻辑）

    Raises:
        HTTPException: 409 冲突，如果检测到并发修改
    """
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SASession
    from fastapi import HTTPException
    from app.core.config import get_settings

    # 查当前记录（当前学期）
    # 注意：学期中换老师会新建记录（旧记录保留），同一 (student_id, subject_id, semester)
    # 可能存在多条记录，必须按 id 倒序取最新一条，保证加分落到新老师的记录上
    score_record = session.exec(
        select(StudentSubjectScore).where(
            StudentSubjectScore.student_id == student_id,
            StudentSubjectScore.subject_id == subject_id,
            StudentSubjectScore.semester == get_current_term(),
        ).order_by(StudentSubjectScore.id.desc())
    ).first()

    if not score_record:
        return None

    # 计算新分数（复用学生分数的范围限制逻辑）
    old_score = score_record.score
    settings = get_settings()
    new_score = max(settings.score.min_score, min(settings.score.max_score, old_score + delta))

    # 乐观锁：使用 version 字段（UPDATE ... WHERE id AND version = 期望值）
    # 相比分数 CAS 可避免 ABA 问题（80→90→80 时 CAS 无法察觉中间修改）
    # 只有读取到的版本未被并发修改时才更新，否则说明有其他事务已修改
    expected_version = score_record.version
    new_version = expected_version + 1

    sa_session: SASession = session
    result = sa_session.execute(
        text("""
            UPDATE student_subject_scores
            SET score = :score, version = :new_version, updated_at = :updated_at
            WHERE id = :id AND version = :expected_version
        """),
        {
            "score": new_score,
            "new_version": new_version,
            "updated_at": get_now(),
            "id": score_record.id,
            "expected_version": expected_version,
        }
    )

    # 检查是否有行被更新，如果没有说明分数已被并发修改
    if result.rowcount == 0:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="分数已被其他用户修改，请刷新后重试"
        )

    # 注意：不要在此处修改内存对象状态（score_record.score）。
    # 原生 UPDATE 已经正确更新了数据库，如果此时再修改内存对象，
    # session.commit() 的 dirty flush 会再次发起无条件 UPDATE，
    # 覆盖并发事务的乐观锁保护，导致 Lost Update。
    # commit() 后对象会被 expire，后续访问会自动读到最新值。

    # 创建领域事件
    event = ScoreUpdated(
        student_id=student_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator
    )

    # 核心副作用：记录分数日志（必须在同一事务中）
    log = StudentSubjectScoreLog(
        student_id=student_id,
        subject_id=subject_id,
        teacher_id=score_record.teacher_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator,
        semester=get_current_term(),
    )
    session.add(log)

    # 使用一次性事件发布机制，确保事件只在事务成功提交后发布一次
    _published_events = getattr(session, '_published_events', None)
    if _published_events is None:
        _published_events = set()
        session._published_events = _published_events

    event_id = id(event)

    def _publish_event_once(session):
        if event_id not in _published_events:
            _published_events.add(event_id)
            event_bus.publish(event)

    # 注册事务提交后的回调
    from sqlalchemy import event as sa_event
    sa_event.listen(session, "after_commit", _publish_event_once, once=True)

    session.commit()

    return score_record
