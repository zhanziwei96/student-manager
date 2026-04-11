"""小组合作评分 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user, require_teacher
from app.models.constants import ApiResponseConst, MessageConst, ApiResponse
from app.models.group import GroupMember, GroupMembershipRequest, GroupTask, Group, GroupEvaluationScore
from app.crud import (
    create_group_task, get_group_task, get_group_tasks_by_class,
    get_task_dimensions, start_group_task, close_group_task,
    submit_teacher_score, get_task_results,
    get_groups_by_class, get_group_members, transfer_group_leader,
    auto_assign_unassigned_students,
    get_pending_dissolution_requests, approve_dissolution_request,
    reject_dissolution_request,
    create_group, get_student_active_group, create_membership_request,
    get_pending_membership_requests, approve_membership_request,
    reject_membership_request, create_dissolution_request,
    get_evaluation_assignments, submit_student_scores, get_group,
    get_class_group_settings, get_or_create_class_group_settings,
    update_class_group_settings,
)

router = APIRouter(tags=["groups"])


class CreateGroupTaskRequest(BaseModel):
    class_name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    dimensions: List[str] = Field(..., min_length=1, max_length=5)


class TeacherScoreRequest(BaseModel):
    target_group_id: int
    dimension_id: int
    score: int = Field(..., ge=0, le=100)


class AutoAssignRequest(BaseModel):
    class_name: str = Field(..., min_length=1)
    group_size: Optional[int] = Field(default=None, ge=2, le=10)


class UpdateClassGroupSettingsRequest(BaseModel):
    class_name: str = Field(..., min_length=1)
    max_members_per_group: int = Field(..., ge=2, le=10)


class TransferLeaderRequest(BaseModel):
    new_leader_id: str = Field(..., min_length=1)


class CreateGroupRequest(BaseModel):
    class_name: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class StudentScoreItem(BaseModel):
    dimension_id: int
    score: int = Field(..., ge=0, le=100)


class StudentScoresSubmit(BaseModel):
    target_group_id: int
    scores: List[StudentScoreItem]


class DissolutionRequestCreate(BaseModel):
    reason: str = Field(..., min_length=1)


def _check_class_not_evaluating(session: Session, class_name: str) -> None:
    """检查班级是否处于互评阶段，若是则拒绝组队操作"""
    evaluating_task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == class_name,
            GroupTask.status == "evaluating",
        )
    ).first()
    if evaluating_task:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="班级正在互评阶段，不可变更小组")


# ============================================================
# Teacher endpoints — 使用 require_teacher 校验角色
# ============================================================

@router.get("/teacher/group-tasks", response_model=ApiResponse[list])
async def api_teacher_group_tasks(
    class_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    tasks = get_group_tasks_by_class(session, class_name)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {"id": t.id, "title": t.title, "status": t.status, "class_name": t.class_name}
            for t in tasks
        ],
    }


@router.post("/teacher/group-tasks", response_model=ApiResponse[dict])
async def api_create_group_task(
    data: CreateGroupTaskRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    username = user.get("username", "")
    task = create_group_task(
        session, data.class_name, data.title, data.description, username, data.dimensions
    )
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"task_id": task.id, "status": task.status},
    }


@router.post("/teacher/group-tasks/{task_id}/start", response_model=ApiResponse[dict])
async def api_start_group_task(
    task_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    task = get_group_task(session, task_id)
    if not task:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="任务不存在")
    try:
        start_group_task(session, task_id)
    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail=str(e))
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "任务已启动",
        ApiResponseConst.DATA: {"task_id": task_id, "status": "evaluating"},
    }


@router.post("/teacher/group-tasks/{task_id}/close", response_model=ApiResponse[dict])
async def api_close_group_task(
    task_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    task = close_group_task(session, task_id)
    if not task:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="任务不存在或状态错误")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "任务已结束",
        ApiResponseConst.DATA: {"task_id": task_id, "status": "closed"},
    }


@router.get("/teacher/group-tasks/{task_id}/results", response_model=ApiResponse[dict])
async def api_get_task_results(
    task_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    task = get_group_task(session, task_id)
    if not task:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="任务不存在")
    results = get_task_results(session, task_id)
    dimensions = get_task_dimensions(session, task_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "task": {"id": task.id, "title": task.title, "status": task.status},
            "dimensions": [{"id": d.id, "name": d.name} for d in dimensions],
            "results": results,
        },
    }


@router.post("/teacher/group-tasks/{task_id}/scores", response_model=ApiResponse[dict])
async def api_submit_teacher_score(
    task_id: int,
    data: TeacherScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    # C3: 校验任务必须在 evaluating 状态才允许评分
    task = get_group_task(session, task_id)
    if not task:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="任务不存在")
    if task.status != "evaluating":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="任务不在评分阶段")
    username = user.get("username", "")
    submit_teacher_score(
        session, task_id, data.target_group_id, data.dimension_id, data.score, username
    )
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "评分已保存",
    }


@router.get("/teacher/groups", response_model=ApiResponse[list])
async def api_teacher_groups(
    class_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    from app.models import Student
    from sqlmodel import col, select as sql_select
    groups = get_groups_by_class(session, class_name)
    # 批量查询所有相关学生姓名
    all_member_ids = []
    for g in groups:
        all_member_ids.extend(m.student_id for m in get_group_members(session, g.id))
    student_map = {}
    if all_member_ids:
        students = session.exec(sql_select(Student).where(col(Student.student_id).in_(set(all_member_ids)))).all()
        student_map = {s.student_id: s.name for s in students}
    result = []
    for g in groups:
        members = get_group_members(session, g.id)
        result.append({
            "id": g.id,
            "name": g.name,
            "leader_student_id": g.leader_student_id,
            "leader_name": student_map.get(g.leader_student_id, g.leader_student_id),
            "members": [{"student_id": m.student_id, "name": student_map.get(m.student_id, m.student_id)} for m in members],
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}


@router.post("/teacher/groups/auto-assign", response_model=ApiResponse[list])
async def api_auto_assign(
    data: AutoAssignRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    settings = get_or_create_class_group_settings(session, data.class_name)
    group_size = data.group_size if data.group_size is not None else settings.max_members_per_group
    new_groups = auto_assign_unassigned_students(session, data.class_name, group_size)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [{"id": g.id, "name": g.name} for g in new_groups],
    }


@router.get("/teacher/class-group-settings", response_model=ApiResponse[dict])
async def api_get_class_group_settings(
    class_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    settings = get_class_group_settings(session, class_name)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "class_name": class_name,
            "max_members_per_group": settings.max_members_per_group if settings else 5,
        },
    }


@router.put("/teacher/class-group-settings", response_model=ApiResponse[dict])
async def api_update_class_group_settings(
    data: UpdateClassGroupSettingsRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    # 校验：新上限 >= 该班所有小组中当前最大成员数
    groups = get_groups_by_class(session, data.class_name)
    max_current = 0
    for g in groups:
        count = len(get_group_members(session, g.id))
        if count > max_current:
            max_current = count
    if data.max_members_per_group < max_current:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"当前有小组已有 {max_current} 人，上限不能小于此值",
        )
    settings = update_class_group_settings(session, data.class_name, data.max_members_per_group)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "class_name": settings.class_name,
            "max_members_per_group": settings.max_members_per_group,
        },
    }


@router.post("/teacher/groups/{group_id}/transfer-leader", response_model=ApiResponse[dict])
async def api_transfer_leader(
    group_id: int,
    data: TransferLeaderRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    group = transfer_group_leader(session, group_id, data.new_leader_id)
    if not group:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="转让失败")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"leader_student_id": group.leader_student_id},
    }


@router.get("/teacher/group-dissolution-requests", response_model=ApiResponse[list])
async def api_dissolution_requests(
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    reqs = get_pending_dissolution_requests(session)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "id": r.id,
                "group_id": r.group_id,
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
            }
            for r in reqs
        ],
    }


@router.post("/teacher/group-dissolution-requests/{req_id}/approve", response_model=ApiResponse[dict])
async def api_approve_dissolution(
    req_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    username = user.get("username", "")
    group = approve_dissolution_request(session, req_id, username)
    if not group:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="审批失败")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "已批准解散",
    }


@router.post("/teacher/group-dissolution-requests/{req_id}/reject", response_model=ApiResponse[dict])
async def api_reject_dissolution(
    req_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    username = user.get("username", "")
    req = reject_dissolution_request(session, req_id, username)
    if not req:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="审批失败")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "已拒绝解散",
    }


# ============================================================
# Student endpoints
# ============================================================

@router.post("/student/groups", response_model=ApiResponse[dict])
async def api_student_create_group(
    data: CreateGroupRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    from app.models.constants import UserRoleConst
    role = user.get("role", "")
    if role != UserRoleConst.STUDENT:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="仅限学生")
    # C2: 组队锁定 — evaluating 状态下禁止创建小组
    _check_class_not_evaluating(session, data.class_name)
    student_id = user.get("sub", "")
    existing = get_student_active_group(session, student_id, data.class_name)
    if existing:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已在一个小组中")
    group = create_group(session, data.class_name, data.name, student_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"group_id": group.id, "name": group.name},
    }


@router.get("/student/groups", response_model=ApiResponse[list])
async def api_student_groups(
    class_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    groups = get_groups_by_class(session, class_name)
    settings = get_class_group_settings(session, class_name)
    max_m = settings.max_members_per_group if settings else None
    result = []
    for g in groups:
        members = get_group_members(session, g.id)
        member_count = len(members)
        result.append({
            "id": g.id,
            "name": g.name,
            "leader_student_id": g.leader_student_id,
            "member_count": member_count,
            "max_members": max_m,
            "is_full": max_m is not None and member_count >= max_m,
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}


@router.post("/student/groups/{group_id}/join-requests", response_model=ApiResponse[dict])
async def api_create_join_request(
    group_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student_id = user.get("sub", "")
    group = get_group(session, group_id)
    if not group or not group.is_active:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")
    # C2: 组队锁定 — evaluating 状态下禁止申请加入
    _check_class_not_evaluating(session, group.class_name)
    # 检查小组是否已满
    settings = get_class_group_settings(session, group.class_name)
    if settings:
        current_count = len(get_group_members(session, group.id))
        if current_count >= settings.max_members_per_group:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="该小组已满，无法申请加入",
            )
    existing = session.exec(
        select(GroupMembershipRequest).where(
            GroupMembershipRequest.group_id == group_id,
            GroupMembershipRequest.student_id == student_id,
            GroupMembershipRequest.status == "pending",
        )
    ).first()
    if existing:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已提交申请")
    req = create_membership_request(session, group_id, student_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"request_id": req.id},
    }


@router.post("/student/groups/join-requests/{req_id}/approve", response_model=ApiResponse[dict])
async def api_approve_join_request(
    req_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student_id = user.get("sub", "")
    req = session.get(GroupMembershipRequest, req_id)
    if not req:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="申请不存在")
    group = get_group(session, req.group_id)
    if not group or group.leader_student_id != student_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权审批")
    # C2: 组队锁定 — evaluating 状态下禁止批准入组
    _check_class_not_evaluating(session, group.class_name)
    # 检查小组是否已满
    settings = get_class_group_settings(session, group.class_name)
    if settings:
        current_count = len(get_group_members(session, group.id))
        if current_count >= settings.max_members_per_group:
            raise HTTPException(
                status_code=HttpStatus.BAD_REQUEST,
                detail="该小组已满，无法批准加入",
            )
    member = approve_membership_request(session, req_id)
    if not member:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="审批失败")
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.MESSAGE: "已批准加入"}


@router.post("/student/groups/join-requests/{req_id}/reject", response_model=ApiResponse[dict])
async def api_reject_join_request(
    req_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student_id = user.get("sub", "")
    req = session.get(GroupMembershipRequest, req_id)
    if not req:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="申请不存在")
    group = get_group(session, req.group_id)
    if not group or group.leader_student_id != student_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权审批")
    req = reject_membership_request(session, req_id)
    if not req:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="审批失败")
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.MESSAGE: "已拒绝加入"}


@router.post("/student/groups/dissolution-requests", response_model=ApiResponse[dict])
async def api_create_dissolution(
    data: DissolutionRequestCreate,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student_id = user.get("sub", "")
    group = session.exec(
        select(Group).join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.student_id == student_id,
            Group.is_active.is_(True),
        )
    ).first()
    if not group:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="未在活跃小组中")
    if group.leader_student_id != student_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="仅组长可申请")
    task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == group.class_name,
            GroupTask.status.in_(["evaluating", "closed"]),
        )
    ).first()
    if task:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="该小组已参与进行中的任务，无法解散")
    req = create_dissolution_request(session, group.id, data.reason)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"request_id": req.id},
    }


@router.get("/student/group-tasks", response_model=ApiResponse[list])
async def api_student_tasks(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    from app.models import Student
    student_id = user.get("sub", "")
    stu = session.get(Student, student_id)
    if not stu:
        return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: []}
    tasks = get_group_tasks_by_class(session, stu.class_name)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {"id": t.id, "title": t.title, "status": t.status, "class_name": t.class_name}
            for t in tasks
        ],
    }


@router.get("/student/group-tasks/{task_id}/evaluations", response_model=ApiResponse[list])
async def api_student_evaluations(
    task_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student_id = user.get("sub", "")
    task = get_group_task(session, task_id)
    if not task:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="任务不存在")
    from app.models import Student
    stu = session.get(Student, student_id)
    if not stu:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="学生信息异常")
    my_group = get_student_active_group(session, student_id, stu.class_name)
    if not my_group:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="未在小组中")
    assignments = get_evaluation_assignments(session, task_id, my_group.id)
    dimensions = get_task_dimensions(session, task_id)
    # 优化 N+1 查询：一次查出该学生对当前任务的所有评分
    all_my_scores = session.exec(
        select(GroupEvaluationScore).where(
            GroupEvaluationScore.task_id == task_id,
            GroupEvaluationScore.evaluator_type == "student",
            GroupEvaluationScore.evaluator_id == student_id,
        )
    ).all()
    scored_set = {(s.target_group_id, s.dimension_id) for s in all_my_scores}
    result = []
    for assign in assignments:
        target = get_group(session, assign.target_group_id)
        result.append({
            "target_group_id": assign.target_group_id,
            "target_group_name": target.name if target else "",
            "dimensions": [
                {"id": d.id, "name": d.name, "scored": (assign.target_group_id, d.id) in scored_set}
                for d in dimensions
            ],
            "all_scored": all(
                (assign.target_group_id, d.id) in scored_set for d in dimensions
            ),
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}


@router.post("/student/group-tasks/{task_id}/scores", response_model=ApiResponse[dict])
async def api_submit_student_scores(
    task_id: int,
    data: StudentScoresSubmit,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    # C3: 校验任务必须在 evaluating 状态才允许评分
    task = get_group_task(session, task_id)
    if not task:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="任务不存在")
    if task.status != "evaluating":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="任务不在评分阶段")
    student_id = user.get("sub", "")
    scores_map = {item.dimension_id: item.score for item in data.scores}
    submit_student_scores(session, task_id, data.target_group_id, student_id, scores_map)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.MESSAGE: "评分已提交"}


@router.get("/student/groups/my-group/results", response_model=ApiResponse[list])
async def api_student_my_group_results(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student_id = user.get("sub", "")
    from app.models import Student
    stu = session.get(Student, student_id)
    if not stu:
        return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: []}
    my_group = get_student_active_group(session, student_id, stu.class_name)
    if not my_group:
        return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: []}
    tasks = get_group_tasks_by_class(session, stu.class_name)
    result = []
    for task in tasks:
        if task.status == "preparing":
            continue
        task_results = get_task_results(session, task.id)
        group_result = task_results.get(my_group.id, {})
        if group_result:
            result.append({
                "task_id": task.id,
                "title": task.title,
                "status": task.status,
                "group_name": my_group.name,
                "teacher_scores": group_result.get("teacher_scores", {}),
                "peer_scores": group_result.get("peer_scores", {}),
                "final_scores": group_result.get("final_scores", {}),
                "task_final": group_result.get("task_final", 0.0),
            })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}


@router.get("/student/groups/my-group", response_model=ApiResponse[dict])
async def api_student_my_group(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    student_id = user.get("sub", "")
    from app.models import Student
    stu = session.get(Student, student_id)
    if not stu:
        return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: None}
    my_group = get_student_active_group(session, student_id, stu.class_name)
    if not my_group:
        return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: None}
    members = get_group_members(session, my_group.id)
    pending_reqs = get_pending_membership_requests(session, my_group.id)
    # 批量查询成员姓名
    member_ids = [m.student_id for m in members]
    student_map = {}
    if member_ids:
        from sqlmodel import col
        students = session.exec(select(Student).where(col(Student.student_id).in_(member_ids))).all()
        student_map = {s.student_id: s.name for s in students}
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "id": my_group.id,
            "name": my_group.name,
            "class_name": my_group.class_name,
            "leader_student_id": my_group.leader_student_id,
            "is_leader": my_group.leader_student_id == student_id,
            "members": [{"student_id": m.student_id, "name": student_map.get(m.student_id, m.student_id)} for m in members],
            "pending_requests": [
                {"id": r.id, "student_id": r.student_id, "created_at": r.created_at.isoformat()}
                for r in pending_reqs
            ],
        },
    }
