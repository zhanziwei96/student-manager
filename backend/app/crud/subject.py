"""
科目 CRUD 操作
"""
from typing import List, Optional, Dict
from sqlmodel import Session, select
from app.models import Subject, CourseSchedule
from app.core.term import get_current_term


def derive_subjects_and_teachers(session: Session) -> Dict[str, Dict[str, int]]:
    """从课表推导科目和教师（当前学期）

    Returns:
        Dict[class_name, Dict[subject_name, teacher_id]]
        如：{"1班": {"数学": 张老师id, "语文": 李老师id}}
    """
    schedules = session.exec(
        select(CourseSchedule).where(CourseSchedule.semester == get_current_term())
    ).all()

    result = {}
    for schedule in schedules:
        if schedule.class_name not in result:
            result[schedule.class_name] = {}
        # 同一班级同一科目可能有多个老师（正课+实验），取第一个
        if schedule.course_name not in result[schedule.class_name]:
            result[schedule.class_name][schedule.course_name] = schedule.teacher_id

    return result


def get_subjects_by_semester(session: Session, semester: Optional[str] = None) -> List[Subject]:
    """按学期查询科目"""
    if semester is None:
        semester = get_current_term()
    query = select(Subject).where(Subject.semester == semester).order_by(Subject.name)
    return list(session.exec(query).all())


def create_subject(session: Session, name: str, semester: Optional[str] = None) -> Subject:
    """创建科目"""
    if semester is None:
        semester = get_current_term()
    subject = Subject(name=name, semester=semester)
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject


def update_subject_name(session: Session, subject_id: int, new_name: str) -> Optional[Subject]:
    """修改科目名称"""
    subject = session.get(Subject, subject_id)
    if not subject:
        return None
    subject.name = new_name
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject
