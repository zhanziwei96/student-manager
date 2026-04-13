import pytest
from sqlmodel import Session, select
from app.models import Student
from app.models.group import GroupTask, GroupEvaluationScore, EvaluationAssignment
from app.crud import (
    create_group_task, start_group_task, close_group_task,
    submit_teacher_score, submit_student_scores, get_task_results,
    create_group, get_task_dimensions, clone_group_task,
)


def test_create_group_task_and_dimensions(session: Session):
    task = create_group_task(session, "一班", "PPT大赛", "做一个PPT", "tea", ["创意", "表达"])
    assert task.status == "preparing"
    dims = get_task_dimensions(session, task.id)
    assert len(dims) == 2
    assert dims[0].name == "创意"


def test_start_group_task_generates_assignments(session: Session):
    task = create_group_task(session, "一班", "PPT大赛", None, "tea", ["创意"])
    g1 = create_group(session, "一班", "G1", "s1")
    g2 = create_group(session, "一班", "G2", "s2")
    g3 = create_group(session, "一班", "G3", "s3")
    started = start_group_task(session, task.id)
    assert started.status == "evaluating"
    assigns = session.exec(
        select(EvaluationAssignment).where(EvaluationAssignment.task_id == task.id)
    ).all()
    # 3 groups * 2 targets (n<=4 => evaluate all others) = 6
    assert len(assigns) == 6


def test_start_group_task_with_few_groups_fails(session: Session):
    task = create_group_task(session, "一班", "PPT大赛", None, "tea", ["创意"])
    create_group(session, "一班", "G1", "s1")
    with pytest.raises(ValueError, match="小组数量不足"):
        start_group_task(session, task.id)


def test_score_calculation_6_4(session: Session):
    task = create_group_task(session, "一班", "PPT大赛", None, "tea", ["创意"])
    g1 = create_group(session, "一班", "G1", "s1")
    g2 = create_group(session, "一班", "G2", "s2")
    start_group_task(session, task.id)
    dims = get_task_dimensions(session, task.id)
    dim_id = dims[0].id
    submit_teacher_score(session, task.id, g1.id, dim_id, 80, "tea")
    submit_student_scores(session, task.id, g1.id, "s2", {dim_id: 90})
    results = get_task_results(session, task.id)
    r = results[g1.id]
    assert r["teacher_scores"]["创意"] == 80.0
    assert r["peer_scores"]["创意"] == 90.0
    assert r["final_scores"]["创意"] == 84.0  # 80*0.6 + 90*0.4


def test_clone_group_task(session: Session):
    source = create_group_task(session, "一班", "PPT大赛", "做一个PPT", "tea", ["创意", "表达"])
    cloned = clone_group_task(session, source.id, "二班", "tea2")
    assert cloned.id != source.id
    assert cloned.title == "PPT大赛（复制）"
    assert cloned.description == "做一个PPT"
    assert cloned.class_name == "二班"
    assert cloned.created_by == "tea2"
    assert cloned.status == "preparing"

    dims = get_task_dimensions(session, cloned.id)
    assert len(dims) == 2
    assert dims[0].name == "创意"
    assert dims[1].name == "表达"
