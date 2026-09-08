# backend/app/crud/leaderboard.py
from typing import List, Optional, Dict, Any
from sqlalchemy import func, or_
from sqlmodel import Session, select
from app.core.term import get_current_semester_id
from app.models import (
    Student, Subject, Course, CourseOffering, Enrollment,
)


def get_leaderboard(
    session: Session,
    scope: str = "class",
    class_name: Optional[str] = None,
    limit: int = 50,
    current_student_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取排行榜数据

    Args:
        session: 数据库会话
        scope: "class" 或 "school"
        class_name: 班级名称（scope=class 时必填）
        limit: 返回数量限制
        current_student_id: 当前登录学生ID（用于获取个人排名）

    Returns:
        {
            "scope": str,
            "students": List[dict],
            "total": int,
            "my_rank": Optional[dict]
        }
    """
    # 构建查询
    query = select(Student).where(Student.is_account_enabled.is_(True))

    if scope == "class" and class_name:
        query = query.where(Student.class_name == class_name)

    # 按分数降序排序
    query = query.order_by(Student.score.desc())

    # 获取前 limit 条
    students = session.exec(query.limit(limit)).all()

    # 计算排名（标准竞赛排名 - 并列后跳过分支）
    # 例如：第1名95分，第2名88分（并列2人），第4名75分（跳过第3名）
    ranked_students = []
    current_rank = 0
    same_rank_count = 0  # 记录相同排名的学生数

    for i, student in enumerate(students):
        if i == 0:
            # 第一名
            current_rank = 1
            same_rank_count = 1
        elif student.score == students[i-1].score:
            # 与上一位并列，排名相同
            same_rank_count += 1
        else:
            # 新排名 = 当前位置 + 1
            current_rank = i + 1
            same_rank_count = 1

        ranked_students.append({
            "rank": current_rank,
            "student_id": student.student_id,
            "name": student.name,
            "class_name": student.class_name,
            "score": student.score
        })

    # 获取当前学生的排名
    my_rank = None
    if current_student_id:
        my_rank = _get_student_rank(session, current_student_id, scope, class_name)

    return {
        "scope": scope,
        "students": ranked_students,
        "total": len(ranked_students),
        "my_rank": my_rank
    }


def _get_student_rank(
    session: Session,
    student_id: str,
    scope: str,
    class_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """获取单个学生的排名信息（使用子查询优化，避免N+1问题）"""
    # 使用子查询一次性获取学生信息和排名
    # 子查询：获取目标学生的分数
    score_subquery = (
        select(Student.score)
        .where(Student.student_id == student_id)
        .scalar_subquery()
    )

    # 主查询：获取学生信息
    student_query = select(Student).where(Student.student_id == student_id)
    student = session.exec(student_query).first()

    if not student:
        return None

    # 子查询：计算排名（分数更高的学生数量）
    rank_query = select(func.count()).where(
        Student.is_account_enabled.is_(True),
        Student.score > score_subquery
    )

    if scope == "class" and class_name:
        rank_query = rank_query.where(Student.class_name == class_name)

    higher_count = session.exec(rank_query).one()

    return {
        "rank": higher_count + 1,
        "student_id": student.student_id,
        "name": student.name,
        "score": student.score
    }


def get_subject_leaderboard(
    session: Session,
    subject_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    limit: int = 50,
    current_student_id: Optional[str] = None,
    accessible_classes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    科目个人成绩榜（enrollments 数据源，竞赛排名并列跳位）

    Args:
        session: 数据库会话
        subject_id: 科目ID（旧参数桥接：subjects.name → courses.name 同名课程）
        teacher_id: 教师ID（可选，不传则跨教师）
        limit: 返回数量限制
        current_student_id: 当前登录学生ID（用于获取个人排名）
        accessible_classes: 教师可见班级范围（None=不限，admin）

    Returns:
        {
            "students": List[dict],
            "total": int,
            "my_rank": Optional[dict]
        }
    """
    base_filter = [
        Enrollment.semester_id == get_current_semester_id(session),
        Enrollment.status == "enrolled",
        Student.is_account_enabled.is_(True),
    ]
    if subject_id is not None:
        subject = session.get(Subject, subject_id)
        if subject is None:
            return {"students": [], "total": 0, "my_rank": None}
        base_filter.append(Course.name == subject.name)
    if teacher_id is not None:
        base_filter.append(CourseOffering.teacher_id == teacher_id)
    if accessible_classes:
        base_filter.append(or_(*[
            CourseOffering.class_scope.contains(c) for c in accessible_classes
        ]))

    query = (
        select(Enrollment, Student, Course, CourseOffering)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
        .join(Course, CourseOffering.course_id == Course.id)
        .where(*base_filter)
        .order_by(Enrollment.score.desc())
    )
    results = session.exec(query.limit(limit)).all()

    # 竞赛排名（并列跳位：1,2,2,4）
    ranked_students = []
    prev_score = None
    for i, (e, student, course, offering) in enumerate(results):
        rank = i + 1 if (i == 0 or e.score != prev_score) else ranked_students[-1]["rank"]
        ranked_students.append({
            "rank": rank,
            "student_id": student.student_id,
            "name": student.name,
            "class_name": student.class_name,
            "subject_name": course.name,
            "teacher_name": offering.teacher_name,
            "score": e.score,
        })
        prev_score = e.score

    # 获取当前学生的排名（取该生最高分记录，score > 计数实现并列修正）
    my_rank = None
    if current_student_id:
        my_score = session.exec(
            select(Enrollment.score)
            .join(Student, Enrollment.student_id == Student.student_id)
            .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
            .join(Course, CourseOffering.course_id == Course.id)
            .where(Enrollment.student_id == current_student_id, *base_filter)
            .order_by(Enrollment.score.desc()).limit(1)
        ).first()

        # 该生在过滤范围内无成绩记录时，my_rank 返回 None（而不是误报第 1 名）
        if my_score is not None:
            higher_count = session.exec(
                select(func.count()).select_from(Enrollment)
                .join(Student, Enrollment.student_id == Student.student_id)
                .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
                .join(Course, CourseOffering.course_id == Course.id)
                .where(*base_filter, Enrollment.score > my_score)
            ).one()
            my_rank = {"rank": higher_count + 1, "student_id": current_student_id}

    return {
        "students": ranked_students,
        "total": len(ranked_students),
        "my_rank": my_rank
    }
