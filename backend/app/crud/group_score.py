"""
小组分数 CRUD 操作
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
from app.models import Group, GroupScoreLog
from app.core.term import get_current_term
from app.core.config import get_settings


def update_group_score(
    session: Session,
    group_id: int,
    delta: float,
    reason: str,
    operator: str,
) -> Optional[Group]:
    """更新小组分数（乐观锁 + 日志，复用学生分数模式）"""
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SASession
    from fastapi import HTTPException

    group = session.get(Group, group_id)
    if not group:
        return None

    settings = get_settings()
    old_score = group.score
    # 使用 Decimal 精确计算，避免浮点精度问题（与学生分数模式一致）
    old_score_dec = Decimal(str(old_score))
    min_score = Decimal(str(settings.score.min_score))
    max_score = Decimal(str(settings.score.max_score))
    delta_dec = Decimal(str(delta))
    new_score_dec = max(min_score, min(max_score, old_score_dec + delta_dec))
    new_score_dec = new_score_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    new_score = float(new_score_dec)

    expected_version = group.version
    new_version = expected_version + 1

    sa_session: SASession = session
    result = sa_session.execute(
        text("""
            UPDATE groups
            SET score = :score, version = :new_version
            WHERE id = :group_id AND version = :expected_version
        """),
        {
            "score": new_score,
            "new_version": new_version,
            "group_id": group_id,
            "expected_version": expected_version
        }
    )

    if result.rowcount == 0:
        session.rollback()
        raise HTTPException(status_code=409, detail="分数已被其他用户修改，请刷新后重试")

    log = GroupScoreLog(
        group_id=group_id,
        subject_id=group.subject_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator,
        semester=get_current_term(),
    )
    session.add(log)
    session.commit()

    return group


def get_group_score_logs(session: Session, group_id: int, limit: int = 50, offset: int = 0) -> List[GroupScoreLog]:
    """获取小组分数日志"""
    query = (
        select(GroupScoreLog)
        .where(GroupScoreLog.group_id == group_id)
        .order_by(GroupScoreLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(session.exec(query).all())


def get_group_leaderboard(
    session: Session,
    subject_id: Optional[int] = None,
    class_name: Optional[str] = None,
    class_names: Optional[List[str]] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """小组排行榜（按科目+班级，分数降序）

    class_name 与 class_names 二选一：class_name 精确匹配单个班级，
    class_names 用于限制在多个班级范围内（教师未指定班级时）。
    """
    query = select(Group).where(
        Group.is_active.is_(True),
        Group.semester == get_current_term(),
    )
    if subject_id:
        query = query.where(Group.subject_id == subject_id)
    if class_name:
        query = query.where(Group.class_name == class_name)
    elif class_names is not None:
        query = query.where(Group.class_name.in_(class_names))
    query = query.order_by(Group.score.desc()).limit(limit)

    groups = session.exec(query).all()

    return [
        {
            "rank": i + 1,
            "group_id": g.id,
            "group_name": g.name,
            "class_name": g.class_name,
            "subject_id": g.subject_id,
            "score": g.score,
        }
        for i, g in enumerate(groups)
    ]
