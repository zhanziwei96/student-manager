# backend/app/crud/leaderboard.py
from typing import List, Optional, Dict, Any
from sqlalchemy import func
from sqlmodel import Session, select
from app.models import Student


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
