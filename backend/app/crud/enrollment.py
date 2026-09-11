"""
选课成绩 CRUD — 个人成绩（score）与期末成绩（final_score）

乐观锁模式统一（Decimal 精确计算 + version CAS + 409 冲突，
与 crud/group_score.py 一致）。
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.class_cache import get_class_display_names
from app.core.config import get_settings, HttpStatus
from app.core.term import get_current_semester_id
from app.models import (
    Course, CourseOffering, CourseOfferingClass, Enrollment, EnrollmentScoreLog,
    GroupMember,
)


def _clamp(new_value: Decimal) -> float:
    """钳制到 [min_score, max_score]，保留两位小数"""
    settings = get_settings()
    min_score = Decimal(str(settings.score.min_score))
    max_score = Decimal(str(settings.score.max_score))
    new_value = max(min_score, min(max_score, new_value))
    return float(new_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def update_enrollment_score(
    session: Session,
    enrollment_id: int,
    delta: float,
    reason: str,
    operator: str,
    expected_version: Optional[int] = None,
) -> Optional[Enrollment]:
    """个人成绩加减分（乐观锁 + 日志），无记录返回 None，并发冲突抛 409

    expected_version：调用方持有的旧版本（乐观锁 CAS）；None 时用当前值。
    """
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment is None:
        return None

    old_score = enrollment.score
    new_score = _clamp(Decimal(str(old_score)) + Decimal(str(delta)))
    if expected_version is None:
        expected_version = enrollment.version

    result = session.execute(
        text("""
            UPDATE enrollments
            SET score = :score, version = version + 1, updated_at = now()
            WHERE id = :eid AND version = :ver
        """),
        {"score": new_score, "eid": enrollment_id, "ver": expected_version},
    )
    if result.rowcount == 0:
        session.rollback()
        raise HTTPException(
            status_code=HttpStatus.CONFLICT, detail="分数已被其他用户修改，请刷新后重试",
        )

    # 防 Lost Update：不在原生 UPDATE 后修改内存对象状态
    session.add(EnrollmentScoreLog(
        enrollment_id=enrollment_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator,
        semester_id=get_current_semester_id(session),
    ))
    session.commit()

    updated = session.get(Enrollment, enrollment_id)
    return updated


def set_final_score(
    session: Session,
    enrollment_id: int,
    final_score: float,
    operator: str,
) -> Optional[Enrollment]:
    """期末成绩登记（试卷个人分）——直接赋值，独立于个人成绩；无记录返回 None"""
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment is None:
        return None

    old_score = enrollment.final_score
    enrollment.final_score = final_score
    session.add(EnrollmentScoreLog(
        enrollment_id=enrollment_id,
        old_score=old_score,
        new_score=final_score,
        reason="期末成绩登记",
        operator=operator,
        semester_id=get_current_semester_id(session),
    ))
    session.commit()
    session.refresh(enrollment)
    return enrollment


def set_final_scores_for_group(
    session: Session,
    offering_id: int,
    group_id: int,
    final_score: float,
    operator: str,
) -> int:
    """期末成绩登记（任务小组同分）：组员∩该教学班选课名单全部写同分，返回受影响行数"""
    member_student_ids = select(GroupMember.student_id).where(
        GroupMember.group_id == group_id
    )
    enrollments = session.exec(select(Enrollment).where(
        Enrollment.offering_id == offering_id,
        Enrollment.student_id.in_(member_student_ids),
    )).all()

    for e in enrollments:
        session.add(EnrollmentScoreLog(
            enrollment_id=e.id,
            old_score=e.final_score,
            new_score=final_score,
            reason="期末成绩登记（小组同分）",
            operator=operator,
            semester_id=get_current_semester_id(session),
        ))
        e.final_score = final_score
    session.commit()
    return len(enrollments)


def get_student_enrollments(
    session: Session,
    student_id: str,
    semester_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """我的成绩：当前学期选课列表（课程名/教师名/范围/score/final_score/status）

    class_scope 响应键由 course_offering_classes 关联表运行时拼装
    （教学班无关联行 = 面向全部班级 → "所有班级"）。
    """
    if semester_id is None:
        semester_id = get_current_semester_id(session)

    query = (
        select(
            Enrollment,
            Course.id,
            Course.name,
            CourseOffering.teacher_name,
        )
        .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
        .join(Course, CourseOffering.course_id == Course.id)
        .where(
            Enrollment.student_id == student_id,
            Enrollment.semester_id == semester_id,
        )
        .order_by(Course.name)
    )
    rows = session.exec(query).all()

    # 批量拼装教学班范围展示串
    scope_by_offering = resolve_offering_scopes(
        session, [e.offering_id for e, _, _, _ in rows])
    return [
        {
            "enrollment_id": e.id,
            "course_id": course_id,
            "course_name": course_name,
            "teacher_name": teacher_name,
            "class_scope": scope_by_offering.get(e.offering_id, "所有班级"),
            "score": e.score,
            "final_score": e.final_score,
            "status": e.status,
        }
        for e, course_id, course_name, teacher_name in rows
    ]


def _class_ids_by_offering(
    session: Session, offering_ids: List[int],
) -> Dict[int, List[int]]:
    """批量查教学班关联的班级 ID（无关联行的教学班不出现在结果中）"""
    if not offering_ids:
        return {}
    assoc = session.exec(select(CourseOfferingClass).where(
        CourseOfferingClass.offering_id.in_(offering_ids),
    )).all()
    grouped: Dict[int, List[int]] = {}
    for a in assoc:
        grouped.setdefault(a.offering_id, []).append(a.class_id)
    return grouped


def resolve_offering_scopes(
    session: Session, offering_ids: List[int],
) -> Dict[int, str]:
    """批量拼装教学班范围展示串（无关联行 = 通配 → "所有班级"）"""
    scopes: Dict[int, str] = {oid: "所有班级" for oid in offering_ids}
    class_ids_by_offering = _class_ids_by_offering(session, offering_ids)
    names = get_class_display_names(
        session, [cid for cids in class_ids_by_offering.values() for cid in cids])
    for oid, cids in class_ids_by_offering.items():
        scopes[oid] = "、".join(names[c] for c in sorted(cids) if c in names)
    return scopes


def resolve_offering_class_ids(
    session: Session, offering_ids: List[int],
) -> Dict[int, List[int]]:
    """批量解析教学班关联的班级 ID（无关联行 = 通配，返回空列表）"""
    grouped = _class_ids_by_offering(session, offering_ids)
    return {oid: sorted(grouped.get(oid, [])) for oid in offering_ids}
