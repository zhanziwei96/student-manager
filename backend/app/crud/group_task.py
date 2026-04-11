"""小组任务与评分 CRUD"""
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from app.core.timezone import get_now
from app.models.group import (
    GroupTask, GroupTaskDimension, EvaluationAssignment,
    GroupEvaluationScore, Group, GroupMember
)


def create_group_task(
    session: Session,
    class_name: str,
    title: str,
    description: Optional[str],
    created_by: str,
    dimensions: List[str],
) -> GroupTask:
    if not dimensions:
        raise ValueError("评分维度不能为空")
    task = GroupTask(
        class_name=class_name,
        title=title,
        description=description,
        status="preparing",
        created_by=created_by,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    for idx, name in enumerate(dimensions):
        dim = GroupTaskDimension(task_id=task.id, name=name, sort_order=idx)
        session.add(dim)
    session.commit()
    return task


def get_group_task(session: Session, task_id: int) -> Optional[GroupTask]:
    return session.get(GroupTask, task_id)


def get_group_tasks_by_class(session: Session, class_name: str) -> List[GroupTask]:
    return session.exec(
        select(GroupTask).where(GroupTask.class_name == class_name).order_by(GroupTask.created_at.desc())
    ).all()


def get_task_dimensions(session: Session, task_id: int) -> List[GroupTaskDimension]:
    return session.exec(
        select(GroupTaskDimension)
        .where(GroupTaskDimension.task_id == task_id)
        .order_by(GroupTaskDimension.sort_order)
    ).all()


def start_group_task(session: Session, task_id: int) -> Optional[GroupTask]:
    task = session.get(GroupTask, task_id)
    if not task or task.status != "preparing":
        return None
    groups = session.exec(
        select(Group).where(Group.class_name == task.class_name, Group.is_active.is_(True))
    ).all()
    if len(groups) < 2:
        raise ValueError("班级小组数量不足，无法启动互评")
    dimensions = get_task_dimensions(session, task_id)
    if len(dimensions) == 0:
        raise ValueError("任务未配置评分维度，无法启动互评")
    # 生成互评指派
    sorted_groups = sorted(groups, key=lambda g: g.id)
    n = len(sorted_groups)
    for i, g in enumerate(sorted_groups):
        if n <= 4:
            targets = [sorted_groups[j] for j in range(n) if j != i]
        else:
            targets = [sorted_groups[(i + k) % n] for k in range(1, 4)]
        for t in targets:
            assignment = EvaluationAssignment(
                task_id=task.id,
                evaluator_group_id=g.id,
                target_group_id=t.id,
            )
            session.add(assignment)
    task.status = "evaluating"
    task.started_at = get_now()
    session.add(task)
    session.commit()
    return task


def close_group_task(session: Session, task_id: int) -> Optional[GroupTask]:
    task = session.get(GroupTask, task_id)
    if not task or task.status != "evaluating":
        return None
    task.status = "closed"
    task.closed_at = get_now()
    session.add(task)
    session.commit()
    return task


def get_evaluation_assignments(session: Session, task_id: int, evaluator_group_id: int) -> List[EvaluationAssignment]:
    return session.exec(
        select(EvaluationAssignment).where(
            EvaluationAssignment.task_id == task_id,
            EvaluationAssignment.evaluator_group_id == evaluator_group_id,
        )
    ).all()


def _validate_dimension_belongs_to_task(session: Session, task_id: int, dimension_id: int) -> None:
    dim = session.exec(
        select(GroupTaskDimension).where(
            GroupTaskDimension.id == dimension_id,
            GroupTaskDimension.task_id == task_id,
        )
    ).first()
    if not dim:
        raise ValueError("评分维度不存在或不属于当前任务")


def submit_teacher_score(
    session: Session,
    task_id: int,
    target_group_id: int,
    dimension_id: int,
    score: int,
    teacher_username: str,
) -> GroupEvaluationScore:
    _validate_dimension_belongs_to_task(session, task_id, dimension_id)
    # 先删除旧记录（如果存在）
    old = session.exec(
        select(GroupEvaluationScore).where(
            GroupEvaluationScore.task_id == task_id,
            GroupEvaluationScore.target_group_id == target_group_id,
            GroupEvaluationScore.evaluator_type == "teacher",
            GroupEvaluationScore.evaluator_id == teacher_username,
            GroupEvaluationScore.dimension_id == dimension_id,
        )
    ).first()
    if old:
        session.delete(old)
    rec = GroupEvaluationScore(
        task_id=task_id,
        target_group_id=target_group_id,
        evaluator_type="teacher",
        evaluator_id=teacher_username,
        dimension_id=dimension_id,
        score=score,
    )
    session.add(rec)
    session.commit()
    return rec


def submit_student_scores(
    session: Session,
    task_id: int,
    target_group_id: int,
    student_id: str,
    scores: Dict[int, int],
) -> List[GroupEvaluationScore]:
    task = session.get(GroupTask, task_id)
    if not task:
        raise ValueError("任务不存在")
    # 验证学生所在小组是否有对被评小组的评估权限
    evaluator_group = session.exec(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.student_id == student_id,
            Group.class_name == task.class_name,
            Group.is_active.is_(True),
        )
    ).first()
    if not evaluator_group:
        raise ValueError("学生不在任何活跃小组中")
    assignment = session.exec(
        select(EvaluationAssignment).where(
            EvaluationAssignment.task_id == task_id,
            EvaluationAssignment.evaluator_group_id == evaluator_group.id,
            EvaluationAssignment.target_group_id == target_group_id,
        )
    ).first()
    if not assignment:
        raise ValueError("无评估权限")
    records = []
    for dim_id, score in scores.items():
        _validate_dimension_belongs_to_task(session, task_id, dim_id)
        old = session.exec(
            select(GroupEvaluationScore).where(
                GroupEvaluationScore.task_id == task_id,
                GroupEvaluationScore.target_group_id == target_group_id,
                GroupEvaluationScore.evaluator_type == "student",
                GroupEvaluationScore.evaluator_id == student_id,
                GroupEvaluationScore.dimension_id == dim_id,
            )
        ).first()
        if old:
            session.delete(old)
        rec = GroupEvaluationScore(
            task_id=task_id,
            target_group_id=target_group_id,
            evaluator_type="student",
            evaluator_id=student_id,
            dimension_id=dim_id,
            score=score,
        )
        session.add(rec)
        records.append(rec)
    session.commit()
    return records


def get_task_results(session: Session, task_id: int) -> Dict[int, Dict[str, Any]]:
    """返回各小组的任务成绩：{group_id: {teacher_scores, peer_scores, final_scores, task_final}}"""
    dimensions = get_task_dimensions(session, task_id)
    dim_ids = [d.id for d in dimensions]
    groups = session.exec(
        select(Group).join(
            EvaluationAssignment,
            EvaluationAssignment.target_group_id == Group.id,
        ).where(
            EvaluationAssignment.task_id == task_id,
        ).distinct()
    ).all()

    results = {}
    for group in groups:
        results[group.id] = {
            "group_id": group.id,
            "group_name": group.name,
            "teacher_scores": {},
            "peer_scores": {},
            "final_scores": {},
            "task_final": 0.0,
        }
        for dim in dimensions:
            # teacher score
            t_rec = session.exec(
                select(GroupEvaluationScore).where(
                    GroupEvaluationScore.task_id == task_id,
                    GroupEvaluationScore.target_group_id == group.id,
                    GroupEvaluationScore.evaluator_type == "teacher",
                    GroupEvaluationScore.dimension_id == dim.id,
                )
            ).first()
            teacher_score = float(t_rec.score) if t_rec else 0.0

            # peer avg
            peer_rows = session.exec(
                select(GroupEvaluationScore).where(
                    GroupEvaluationScore.task_id == task_id,
                    GroupEvaluationScore.target_group_id == group.id,
                    GroupEvaluationScore.evaluator_type == "student",
                    GroupEvaluationScore.dimension_id == dim.id,
                )
            ).all()
            peer_score = sum(r.score for r in peer_rows) / len(peer_rows) if peer_rows else 0.0

            final_score = teacher_score * 0.6 + peer_score * 0.4
            results[group.id]["teacher_scores"][dim.name] = teacher_score
            results[group.id]["peer_scores"][dim.name] = round(peer_score, 2)
            results[group.id]["final_scores"][dim.name] = round(final_score, 2)

        task_final = sum(results[group.id]["final_scores"].values()) / len(dimensions) if dimensions else 0.0
        results[group.id]["task_final"] = round(task_final, 2)

    return results
