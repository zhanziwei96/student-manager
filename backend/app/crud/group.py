"""小组 CRUD"""
from datetime import datetime
from typing import List, Optional
import random
from sqlmodel import Session, select
from app.core.timezone import get_now
from app.models.group import (
    Group, GroupMember, GroupMembershipRequest,
    GroupDissolutionRequest, GroupTask
)


def get_group(session: Session, group_id: int) -> Optional[Group]:
    return session.get(Group, group_id)


def get_groups_by_class(session: Session, class_name: str) -> List[Group]:
    return session.exec(
        select(Group).where(Group.class_name == class_name, Group.is_active.is_(True))
    ).all()


def get_student_active_group(session: Session, student_id: str, class_name: str) -> Optional[Group]:
    """获取学生在某班的活跃小组"""
    statement = (
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.student_id == student_id,
            Group.class_name == class_name,
            Group.is_active.is_(True),
        )
    )
    return session.exec(statement).first()


def get_group_members(session: Session, group_id: int) -> List[GroupMember]:
    return session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id)
    ).all()


def create_group(session: Session, class_name: str, name: str, leader_student_id: str) -> Group:
    group = Group(
        class_name=class_name,
        name=name,
        leader_student_id=leader_student_id,
        is_active=True,
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    # 组长自动加入
    member = GroupMember(group_id=group.id, student_id=leader_student_id)
    session.add(member)
    session.commit()
    return group


def _remove_student_from_class_groups(session: Session, student_id: str, class_name: str) -> None:
    """将学生从某班所有活跃小组中移除"""
    groups = get_groups_by_class(session, class_name)
    for group in groups:
        members = session.exec(
            select(GroupMember).where(
                GroupMember.group_id == group.id,
                GroupMember.student_id == student_id,
            )
        ).all()
        for m in members:
            session.delete(m)
    session.commit()


def create_membership_request(session: Session, group_id: int, student_id: str) -> GroupMembershipRequest:
    req = GroupMembershipRequest(group_id=group_id, student_id=student_id, status="pending")
    session.add(req)
    session.commit()
    session.refresh(req)
    return req


def get_pending_membership_requests(session: Session, group_id: int) -> List[GroupMembershipRequest]:
    return session.exec(
        select(GroupMembershipRequest)
        .where(
            GroupMembershipRequest.group_id == group_id,
            GroupMembershipRequest.status == "pending",
        )
    ).all()


def approve_membership_request(session: Session, request_id: int) -> Optional[GroupMember]:
    req = session.get(GroupMembershipRequest, request_id)
    if not req or req.status != "pending":
        return None
    group = session.get(Group, req.group_id)
    if not group or not group.is_active:
        return None
    req.status = "approved"
    req.resolved_at = get_now()
    # 先退出旧组
    _remove_student_from_class_groups(session, req.student_id, group.class_name)
    # 加入新组
    member = GroupMember(group_id=group.id, student_id=req.student_id)
    session.add(member)
    session.commit()
    return member


def reject_membership_request(session: Session, request_id: int) -> Optional[GroupMembershipRequest]:
    req = session.get(GroupMembershipRequest, request_id)
    if not req or req.status != "pending":
        return None
    req.status = "rejected"
    req.resolved_at = get_now()
    session.add(req)
    session.commit()
    return req


def create_dissolution_request(session: Session, group_id: int, reason: str) -> GroupDissolutionRequest:
    req = GroupDissolutionRequest(group_id=group_id, reason=reason, status="pending")
    session.add(req)
    session.commit()
    session.refresh(req)
    return req


def get_pending_dissolution_requests(session: Session) -> List[GroupDissolutionRequest]:
    return session.exec(
        select(GroupDissolutionRequest).where(GroupDissolutionRequest.status == "pending")
    ).all()


def approve_dissolution_request(session: Session, request_id: int, teacher_username: str) -> Optional[Group]:
    req = session.get(GroupDissolutionRequest, request_id)
    if not req or req.status != "pending":
        return None
    group = session.get(Group, req.group_id)
    if not group:
        return None
    req.status = "approved"
    req.resolved_at = get_now()
    req.resolved_by = teacher_username
    group.is_active = False
    session.add(req)
    session.add(group)
    session.commit()
    return group


def reject_dissolution_request(session: Session, request_id: int, teacher_username: str) -> Optional[GroupDissolutionRequest]:
    req = session.get(GroupDissolutionRequest, request_id)
    if not req or req.status != "pending":
        return None
    req.status = "rejected"
    req.resolved_at = get_now()
    req.resolved_by = teacher_username
    session.add(req)
    session.commit()
    return req


def transfer_group_leader(session: Session, group_id: int, new_leader_id: str) -> Optional[Group]:
    group = session.get(Group, group_id)
    if not group or not group.is_active:
        return None
    # 确认新组长是组员
    member = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.student_id == new_leader_id,
        )
    ).first()
    if not member:
        return None
    group.leader_student_id = new_leader_id
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def auto_assign_unassigned_students(session: Session, class_name: str, group_size: int = 4) -> List[Group]:
    """将某班未组队学生随机分配成新小组"""
    from app.models import Student
    # 找出该班所有学生
    all_students = session.exec(
        select(Student).where(Student.class_name == class_name)
    ).all()
    # 找出已在活跃小组的学生
    active_groups = get_groups_by_class(session, class_name)
    assigned_ids = set()
    for g in active_groups:
        for m in get_group_members(session, g.id):
            assigned_ids.add(m.student_id)
    # 未组队学生
    unassigned = [s for s in all_students if s.student_id not in assigned_ids]
    if len(unassigned) < 2:
        return []
    random.shuffle(unassigned)
    groups = []
    for i in range(0, len(unassigned), group_size):
        chunk = unassigned[i:i + group_size]
        leader = random.choice(chunk)
        group = create_group(
            session,
            class_name=class_name,
            name=f"第 {len(active_groups) + len(groups) + 1} 组",
            leader_student_id=leader.student_id,
        )
        # 组长已自动加入，再将其余人加入
        for s in chunk:
            if s.student_id != leader.student_id:
                member = GroupMember(group_id=group.id, student_id=s.student_id)
                session.add(member)
        session.commit()
        groups.append(group)
    return groups
