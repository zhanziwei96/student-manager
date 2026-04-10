"""小组合作评分 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user
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
    group_size: int = Field(default=4, ge=2, le=10)


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


# Teacher endpoints

@router.post("/teacher/group-tasks", response_model=ApiResponse[dict])
async def api_create_group_task(
    data: CreateGroupTaskRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
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
    user: dict = Depends(get_current_user),
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
    user: dict = Depends(get_current_user),
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
    user: dict = Depends(get_current_user),
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
            "dimensions": [d.name for d in dimensions],
            "results": results,
        },
    }


@router.post("/teacher/group-tasks/{task_id}/scores", response_model=ApiResponse[dict])
async def api_submit_teacher_score(
    task_id: int,
    data: TeacherScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
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
    user: dict = Depends(get_current_user),
):
    groups = get_groups_by_class(session, class_name)
    result = []
    for g in groups:
        members = get_group_members(session, g.id)
        result.append({
            "id": g.id,
            "name": g.name,
            "leader_student_id": g.leader_student_id,
            "members": [{"student_id": m.student_id} for m in members],
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}


@router.post("/teacher/groups/auto-assign", response_model=ApiResponse[list])
async def api_auto_assign(
    data: AutoAssignRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    new_groups = auto_assign_unassigned_students(session, data.class_name, data.group_size)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [{"id": g.id, "name": g.name} for g in new_groups],
    }


@router.post("/teacher/groups/{group_id}/transfer-leader", response_model=ApiResponse[dict])
async def api_transfer_leader(
    group_id: int,
    data: TransferLeaderRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
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
    user: dict = Depends(get_current_user),
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
    user: dict = Depends(get_current_user),
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
    user: dict = Depends(get_current_user),
):
    username = user.get("username", "")
    req = reject_dissolution_request(session, req_id, username)
    if not req:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="审批失败")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "已拒绝解散",
    }


# Student endpoints

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
    result = []
    for g in groups:
        members = get_group_members(session, g.id)
        result.append({
            "id": g.id,
            "name": g.name,
            "leader_student_id": g.leader_student_id,
            "member_count": len(members),
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
    result = []
    for assign in assignments:
        target = get_group(session, assign.target_group_id)
        scored_dims = set()
        for d in dimensions:
            has_score = session.exec(
                select(GroupEvaluationScore).where(
                    GroupEvaluationScore.task_id == task_id,
                    GroupEvaluationScore.target_group_id == assign.target_group_id,
                    GroupEvaluationScore.evaluator_type == "student",
                    GroupEvaluationScore.evaluator_id == student_id,
                    GroupEvaluationScore.dimension_id == d.id,
                )
            ).first()
            if has_score:
                scored_dims.add(d.id)
        result.append({
            "target_group_id": assign.target_group_id,
            "target_group_name": target.name if target else "",
            "dimensions": [
                {"id": d.id, "name": d.name, "scored": d.id in scored_dims}
                for d in dimensions
            ],
            "all_scored": len(scored_dims) == len(dimensions),
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}


@router.post("/student/group-tasks/{task_id}/scores", response_model=ApiResponse[dict])
async def api_submit_student_scores(
    task_id: int,
    data: StudentScoresSubmit,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
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
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "id": my_group.id,
            "name": my_group.name,
            "class_name": my_group.class_name,
            "leader_student_id": my_group.leader_student_id,
            "is_leader": my_group.leader_student_id == student_id,
            "members": [{"student_id": m.student_id} for m in members],
            "pending_requests": [
                {"id": r.id, "student_id": r.student_id, "created_at": r.created_at.isoformat()}
                for r in pending_reqs
            ],
        },
    }
