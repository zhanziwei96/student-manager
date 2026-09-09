"""成绩排行榜查询 — 个人榜（enrollments.score）/ 小组榜（groups.score），按科目"""
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.models import CourseOffering, Enrollment, Group, GroupMember, Student


def _rank(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """标准竞赛排名：并列同分名次相同，后续名次跳过"""
    if not entries:
        return []
    entries.sort(key=lambda e: e["score"], reverse=True)
    rank, prev_score, i = 0, None, 0
    for entry in entries:
        i += 1
        if prev_score is None or entry["score"] != prev_score:
            rank = i
        entry["rank"] = rank
        prev_score = entry["score"]
    return entries


def get_individual_ranking(
    session: Session,
    course_id: int,
    scope: str,
    class_name: Optional[str],
    semester_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """个人成绩榜：按科目聚合 enrollments（scope=class 时按行政班过滤）"""
    query = (
        select(Enrollment.student_id, Enrollment.score, Student.name, Student.class_name)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
        .where(
            CourseOffering.course_id == course_id,
            Enrollment.semester_id == semester_id,
            Enrollment.status == "enrolled",
        )
    )
    if scope == "class" and class_name:
        query = query.where(Student.class_name == class_name)
    rows = session.exec(query).all()
    entries = [
        {"student_id": sid, "name": name, "class_name": cls_name, "score": score}
        for sid, score, name, cls_name in rows
    ]
    return _rank(entries)[:limit]


def get_group_ranking(
    session: Session,
    course_id: int,
    scope: str,
    class_name: Optional[str],
    semester_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """小组成绩榜：按科目聚合 groups（小组累计分，含成员名单）"""
    query = select(Group).where(
        Group.course_id == course_id,
        Group.semester_id == semester_id,
        Group.is_active.is_(True),
    )
    if scope == "class" and class_name:
        query = query.where(Group.class_name == class_name)
    groups = session.exec(query).all()
    member_rows = session.exec(
        select(GroupMember.group_id, Student.name)
        .join(Student, GroupMember.student_id == Student.student_id)
        .where(GroupMember.group_id.in_([g.id for g in groups]))
    ).all()
    members: Dict[int, List[str]] = {}
    for group_id, name in member_rows:
        members.setdefault(group_id, []).append(name)
    entries = [
        {"group_id": g.id, "name": g.name, "class_name": g.class_name,
         "score": g.score, "members": members.get(g.id, [])}
        for g in groups
    ]
    return _rank(entries)[:limit]
