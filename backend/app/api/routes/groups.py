"""小组合作评分 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.class_cache import get_class_display_name_by_id, get_class_display_names
from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user, require_teacher
from app.api.deps import verify_class_has_active_students
from app.models.constants import ApiResponseConst, MessageConst, ApiResponse
from app.models.group import GroupMember, GroupMembershipRequest, Group
from app.crud import (
    get_groups_by_class, get_group_members, transfer_group_leader,
    auto_assign_unassigned_students,
    get_pending_dissolution_requests, approve_dissolution_request,
    reject_dissolution_request,
    create_group, get_student_active_group, get_student_groups, create_membership_request,
    get_pending_membership_requests, approve_membership_request,
    reject_membership_request, create_dissolution_request,
    get_group,
    get_class_group_settings, get_or_create_class_group_settings,
    update_class_group_settings,
    get_group_with_members, remove_group_member, dissolve_group,
)

router = APIRouter(tags=["groups"])





class AutoAssignRequest(BaseModel):
    class_id: int = Field(..., description="班级ID")
    course_id: int = Field(..., description="课程ID（小组按科目划分）")
    group_size: Optional[int] = Field(default=None, ge=2, le=10)


class UpdateClassGroupSettingsRequest(BaseModel):
    class_id: int = Field(..., description="班级ID")
    max_members_per_group: int = Field(..., ge=2, le=10)


class TransferLeaderRequest(BaseModel):
    new_leader_id: str = Field(..., min_length=1)


class CreateGroupRequest(BaseModel):
    class_id: int = Field(..., description="班级ID")
    name: str = Field(..., min_length=1)
    course_id: int = Field(..., description="课程ID（小组按科目划分）")




class DissolutionRequestCreate(BaseModel):
    reason: str = Field(..., min_length=1)


@router.get("/teacher/groups", response_model=ApiResponse[list])
async def api_teacher_groups(
    class_id: int,
    course_id: Optional[int] = Query(None, description="按课程过滤"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """获取班级小组列表（小组按课程划分）"""
    from app.models import Student, Course
    from sqlmodel import col, select as sql_select
    groups = get_groups_by_class(session, class_id, course_id=course_id)
    # 批量查询所有相关学生姓名
    all_member_ids = []
    for g in groups:
        all_member_ids.extend(m.student_id for m in get_group_members(session, g.id))
    student_map = {}
    if all_member_ids:
        students = session.exec(sql_select(Student).where(col(Student.student_id).in_(set(all_member_ids)))).all()
        student_map = {s.student_id: s.name for s in students}
    # 批量查询课程名称（小组按课程划分）
    course_ids = {g.course_id for g in groups if g.course_id is not None}
    course_map = {}
    if course_ids:
        courses = session.exec(sql_select(Course).where(col(Course.id).in_(course_ids))).all()
        course_map = {c.id: c.name for c in courses}
    group_class_names = get_class_display_names(session, (g.class_id for g in groups))
    result = []
    for g in groups:
        members = get_group_members(session, g.id)
        result.append({
            "id": g.id,
            "name": g.name,
            "class_name": group_class_names.get(g.class_id),
            "leader_student_id": g.leader_student_id,
            "leader_name": student_map.get(g.leader_student_id, g.leader_student_id),
            "course_id": g.course_id,
            "course_name": course_map.get(g.course_id) if g.course_id is not None else None,
            "score": g.score,
            "members": [{"student_id": m.student_id, "name": student_map.get(m.student_id, m.student_id)} for m in members],
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}


@router.post("/teacher/groups", response_model=ApiResponse[dict])
async def api_teacher_create_group(
    data: CreateGroupRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """教师建组（按课程划分，组长自动加入）"""
    from app.models import Course

    if session.get(Course, data.course_id) is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="课程不存在")
    verify_class_has_active_students(data.class_id, session)

    group = create_group(session, data.class_id, data.name, "", course_id=data.course_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"group_id": group.id, "name": group.name},
        ApiResponseConst.MESSAGE: "小组创建成功",
    }


@router.post("/teacher/groups/auto-assign", response_model=ApiResponse[list])
async def api_auto_assign(
    data: AutoAssignRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """自动分配未组队学生（按课程）"""
    # 校验班级存在且有启用学生（防止对已归档班级分组）
    verify_class_has_active_students(data.class_id, session)
    settings = get_or_create_class_group_settings(session, data.class_id)
    group_size = data.group_size if data.group_size is not None else settings.max_members_per_group
    new_groups = auto_assign_unassigned_students(session, data.class_id, group_size, course_id=data.course_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [{"id": g.id, "name": g.name} for g in new_groups],
    }


@router.get("/teacher/class-group-settings", response_model=ApiResponse[dict])
async def api_get_class_group_settings(
    class_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """获取班级小组设置"""
    settings = get_class_group_settings(session, class_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "class_name": get_class_display_name_by_id(session, class_id),
            "max_members_per_group": settings.max_members_per_group if settings else 5,
        },
    }


@router.put("/teacher/class-group-settings", response_model=ApiResponse[dict])
async def api_update_class_group_settings(
    data: UpdateClassGroupSettingsRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """更新班级小组人数上限"""
    # 校验：新上限 >= 该班所有小组中当前最大成员数
    groups = get_groups_by_class(session, data.class_id)
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
    settings = update_class_group_settings(session, data.class_id, data.max_members_per_group)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "class_name": get_class_display_name_by_id(session, data.class_id),
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
    """转让小组组长"""
    group = transfer_group_leader(session, group_id, data.new_leader_id)
    if not group:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="转让失败")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"leader_student_id": group.leader_student_id},
    }


@router.get("/teacher/groups/{group_id}", response_model=ApiResponse[dict])
async def api_get_group_detail(
    group_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """获取小组详情，包含成员列表"""
    group_data = get_group_with_members(session, group_id)
    if not group_data:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: group_data,
    }


@router.delete("/teacher/groups/{group_id}/members/{student_id}", response_model=ApiResponse[dict])
async def api_remove_member(
    group_id: int,
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """踢出小组成员"""
    success = remove_group_member(session, group_id, student_id)
    if not success:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="踢出失败，成员可能不存在")
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "成员已踢出",
    }


@router.delete("/teacher/groups/{group_id}", response_model=ApiResponse[dict])
async def api_dissolve_group(
    group_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """解散小组"""
    try:
        success = dissolve_group(session, group_id)
        if not success:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")
    except ValueError as e:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail=str(e))
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "小组已解散",
    }


@router.get("/teacher/group-dissolution-requests", response_model=ApiResponse[list])
async def api_dissolution_requests(
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """获取待处理的解散申请"""
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
    """批准解散申请"""
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
    """拒绝解散申请"""
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
    """学生创建小组（按科目划分：同科目仅一个小组）"""
    from app.models.constants import UserRoleConst
    from app.models import Course

    role = user.get("role", "")
    if role != UserRoleConst.STUDENT:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="仅限学生")
    if session.get(Course, data.course_id) is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="课程不存在")
    student_id = user.get("sub", "")
    existing = get_student_active_group(session, student_id, data.class_id, course_id=data.course_id)
    if existing:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已在该科目的一个小组中")
    group = create_group(session, data.class_id, data.name, student_id, course_id=data.course_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"group_id": group.id, "name": group.name},
    }


@router.get("/student/groups", response_model=ApiResponse[list])
async def api_student_groups(
    class_id: int,
    course_id: Optional[int] = Query(None, description="按课程过滤"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """获取班级可加入小组列表（小组按课程划分）"""
    groups = get_groups_by_class(session, class_id, course_id=course_id)
    settings = get_class_group_settings(session, class_id)
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
    """提交入组申请"""
    student_id = user.get("sub", "")
    group = get_group(session, group_id)
    if not group or not group.is_active:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")
    # 检查小组是否已满
    settings = get_class_group_settings(session, group.class_id)
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
    """组长批准入组申请"""
    student_id = user.get("sub", "")
    req = session.get(GroupMembershipRequest, req_id)
    if not req:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="申请不存在")
    group = get_group(session, req.group_id)
    if not group or group.leader_student_id != student_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权审批")
    # 检查小组是否已满
    settings = get_class_group_settings(session, group.class_id)
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
    """组长拒绝入组申请"""
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
    """组长提交解散申请"""
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
    req = create_dissolution_request(session, group.id, data.reason)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"request_id": req.id},
    }


@router.post("/student/groups/leave", response_model=ApiResponse)
async def api_leave_group(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生退出小组"""
    student_id = user.get("sub", "")
    # Find the student's active group
    group = session.exec(
        select(Group).join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.student_id == student_id,
            Group.is_active.is_(True),
        )
    ).first()
    if not group:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="未在任何小组中")
    if group.leader_student_id == student_id:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="组长不可退出，请先转让组长或申请解散")

    # 学生退出仅离开当前科目的小组（小组按科目划分）
    from app.crud.group import _remove_student_from_course_groups
    _remove_student_from_course_groups(
        session, student_id, group.class_id, group.course_id)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "已退出小组",
    }


@router.get("/student/groups/my-group", response_model=ApiResponse[list])
async def api_student_my_group(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """获取学生当前学期全部小组信息（小组按科目划分，每科一个）"""
    student_id = user.get("sub", "")
    from app.models import Student, Course
    stu = session.get(Student, student_id)
    if not stu or stu.class_id is None:
        return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: []}
    my_groups = get_student_groups(session, student_id, stu.class_id)
    if not my_groups:
        return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: []}

    # 批量查询课程名称与成员姓名
    course_ids = {g.course_id for g in my_groups if g.course_id is not None}
    course_map = {}
    if course_ids:
        from sqlmodel import col
        courses = session.exec(select(Course).where(col(Course.id).in_(course_ids))).all()
        course_map = {c.id: c.name for c in courses}
    all_member_ids = set()
    for g in my_groups:
        all_member_ids.update(m.student_id for m in get_group_members(session, g.id))
    student_map = {}
    if all_member_ids:
        from sqlmodel import col
        students = session.exec(select(Student).where(col(Student.student_id).in_(all_member_ids))).all()
        student_map = {s.student_id: s.name for s in students}

    my_class_names = get_class_display_names(session, (g.class_id for g in my_groups))
    result = []
    for g in my_groups:
        members = get_group_members(session, g.id)
        pending_reqs = get_pending_membership_requests(session, g.id)
        result.append({
            "id": g.id,
            "name": g.name,
            "class_name": my_class_names.get(g.class_id),
            "course_id": g.course_id,
            "course_name": course_map.get(g.course_id),
            "score": g.score,
            "leader_student_id": g.leader_student_id,
            "leader_name": student_map.get(g.leader_student_id, g.leader_student_id),
            "is_leader": g.leader_student_id == student_id,
            "members": [{"student_id": m.student_id, "name": student_map.get(m.student_id, m.student_id)} for m in members],
            "pending_requests": [
                {"id": r.id, "student_id": r.student_id, "created_at": r.created_at.isoformat()}
                for r in pending_reqs
            ],
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}
