"""小组 CRUD"""
from typing import List, Optional
import random
from sqlmodel import Session, select
from app.core.class_cache import get_class_id_by_name
from app.core.term import get_current_term, get_current_semester_id
from app.core.transition_filters import class_filter, semester_filter
from app.core.timezone import get_now
from app.models.group import (
    Group, GroupMember, GroupMembershipRequest,
    GroupDissolutionRequest, ClassGroupSettings
)


def get_group(session: Session, group_id: int) -> Optional[Group]:
    """根据 ID 获取小组"""
    return session.get(Group, group_id)


def get_groups_by_class(
    session: Session,
    class_name: str,
    course_id: Optional[int] = None,
) -> List[Group]:
    """获取某班当前学期所有活跃小组（可按课程过滤）"""
    query = select(Group).where(
        class_filter(
            Group.class_id, Group.class_name,
            get_class_id_by_name(session, class_name), class_name,
        ),
        Group.is_active.is_(True),
        semester_filter(
            Group.semester_id, Group.semester,
            get_current_semester_id(session), get_current_term(),
        ),
    )
    if course_id is not None:
        query = query.where(Group.course_id == course_id)
    return session.exec(query.order_by(Group.id)).all()


def get_student_active_group(
    session: Session,
    student_id: str,
    class_name: str,
    course_id: Optional[int] = None,
) -> Optional[Group]:
    """获取学生在某班当前学期的活跃小组（小组按科目划分：同科目唯一）"""
    statement = (
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.student_id == student_id,
            class_filter(
                Group.class_id, Group.class_name,
                get_class_id_by_name(session, class_name), class_name,
            ),
            Group.is_active.is_(True),
            semester_filter(
                Group.semester_id, Group.semester,
                get_current_semester_id(session), get_current_term(),
            ),
        )
    )
    if course_id is not None:
        statement = statement.where(Group.course_id == course_id)
    return session.exec(statement).first()


def get_student_groups(session: Session, student_id: str, class_name: str) -> List[Group]:
    """获取学生在某班当前学期的全部活跃小组（每科一个）"""
    statement = (
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(
            GroupMember.student_id == student_id,
            class_filter(
                Group.class_id, Group.class_name,
                get_class_id_by_name(session, class_name), class_name,
            ),
            Group.is_active.is_(True),
            semester_filter(
                Group.semester_id, Group.semester,
                get_current_semester_id(session), get_current_term(),
            ),
        )
        .order_by(Group.id)
    )
    return session.exec(statement).all()


def get_group_members(session: Session, group_id: int) -> List[GroupMember]:
    """获取小组所有成员"""
    return session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id)
    ).all()


def create_group(
    session: Session,
    class_name: str,
    name: str,
    leader_student_id: str,
    course_id: Optional[int] = None,
) -> Group:
    """创建小组（按科目划分），组长自动加入"""
    group = Group(
        class_name=class_name,
        class_id=get_class_id_by_name(session, class_name),     # 双写：FK 列
        semester_id=get_current_semester_id(session),           # 双写：FK 列
        name=name,
        leader_student_id=leader_student_id,
        course_id=course_id,
        is_active=True,
    )
    session.add(group)
    session.commit()
    session.refresh(group)
    # 组长自动加入（教师建空组时组长为空，等待学生申请加入）
    if leader_student_id:
        member = GroupMember(group_id=group.id, student_id=leader_student_id)
        session.add(member)
        session.commit()
    return group


def _remove_student_from_course_groups(
    session: Session, student_id: str, class_name: str, course_id: Optional[int],
) -> None:
    """将学生从某班指定科目（或全部科目）的活跃小组中移除；若小组无人则自动解散"""
    groups = get_groups_by_class(session, class_name, course_id=course_id)
    for group in groups:
        members = session.exec(
            select(GroupMember).where(
                GroupMember.group_id == group.id,
                GroupMember.student_id == student_id,
            )
        ).all()
        if not members:
            continue
        for m in members:
            session.delete(m)
        # 检查小组是否还有其他成员
        remaining = session.exec(
            select(GroupMember).where(GroupMember.group_id == group.id)
        ).all()
        if not remaining:
            group.is_active = False
            session.add(group)
    session.commit()


def create_membership_request(session: Session, group_id: int, student_id: str) -> GroupMembershipRequest:
    """创建入组申请"""
    req = GroupMembershipRequest(group_id=group_id, student_id=student_id, status="pending")
    session.add(req)
    session.commit()
    session.refresh(req)
    return req


def get_pending_membership_requests(session: Session, group_id: int) -> List[GroupMembershipRequest]:
    """获取小组待处理的入组申请"""
    return session.exec(
        select(GroupMembershipRequest)
        .where(
            GroupMembershipRequest.group_id == group_id,
            GroupMembershipRequest.status == "pending",
        )
    ).all()


def approve_membership_request(session: Session, request_id: int) -> Optional[GroupMember]:
    """批准入组申请，先退出旧组再加入新组"""
    req = session.get(GroupMembershipRequest, request_id)
    if not req or req.status != "pending":
        return None
    group = session.get(Group, req.group_id)
    if not group or not group.is_active:
        return None
    req.status = "approved"
    req.resolved_at = get_now()
    # 先退出同科目旧组（小组按科目划分）
    _remove_student_from_course_groups(session, req.student_id, group.class_name, group.course_id)
    # 加入新组
    member = GroupMember(group_id=group.id, student_id=req.student_id)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def reject_membership_request(session: Session, request_id: int) -> Optional[GroupMembershipRequest]:
    """拒绝入组申请"""
    req = session.get(GroupMembershipRequest, request_id)
    if not req or req.status != "pending":
        return None
    req.status = "rejected"
    req.resolved_at = get_now()
    session.add(req)
    session.commit()
    return req


def create_dissolution_request(session: Session, group_id: int, reason: str) -> GroupDissolutionRequest:
    """创建解散小组申请"""
    req = GroupDissolutionRequest(group_id=group_id, reason=reason, status="pending")
    session.add(req)
    session.commit()
    session.refresh(req)
    return req


def get_pending_dissolution_requests(session: Session) -> List[GroupDissolutionRequest]:
    """获取所有待处理的解散申请"""
    return session.exec(
        select(GroupDissolutionRequest).where(GroupDissolutionRequest.status == "pending")
    ).all()


def approve_dissolution_request(session: Session, request_id: int, teacher_username: str) -> Optional[Group]:
    """批准解散申请"""
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
    """拒绝解散申请"""
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
    """转让组长"""
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


def auto_assign_unassigned_students(
    session: Session, class_name: str, group_size: int = 4, course_id: Optional[int] = None,
) -> List[Group]:
    """将某班未组队学生随机分配成新小组（按课程）"""
    from app.models import Student
    # 找出该班所有启用学生（禁用学生不参与自动分组）
    all_students = session.exec(
        select(Student).where(
            class_filter(
                Student.class_id, Student.class_name,
                get_class_id_by_name(session, class_name), class_name,
            ),
            Student.is_account_enabled.is_(True),
        )
    ).all()
    # 找出已在活跃小组的学生（同科目）
    active_groups = get_groups_by_class(session, class_name, course_id=course_id)
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
            course_id=course_id,
        )
        # 组长已自动加入，再将其余人加入
        for s in chunk:
            if s.student_id != leader.student_id:
                member = GroupMember(group_id=group.id, student_id=s.student_id)
                session.add(member)
        session.commit()
        groups.append(group)
    return groups


def _get_class_group_settings(session: Session, class_name: str) -> Optional[ClassGroupSettings]:
    """按 class_name 解析 (class_id, semester_id) 后按复合主键查询；
    无法解析（班级/学期不存在）时回退按 class_name 过滤（过渡期）"""
    class_id = get_class_id_by_name(session, class_name)
    semester_id = get_current_semester_id(session)
    if class_id is not None and semester_id is not None:
        return session.get(ClassGroupSettings, (class_id, semester_id))
    return session.exec(select(ClassGroupSettings).where(
        ClassGroupSettings.class_name == class_name)).first()


def get_class_group_settings(session: Session, class_name: str) -> Optional[ClassGroupSettings]:
    """获取班级小组设置"""
    return _get_class_group_settings(session, class_name)


def get_or_create_class_group_settings(session: Session, class_name: str) -> ClassGroupSettings:
    """获取或创建班级小组设置（复合主键 (class_id, semester_id)）"""
    settings = _get_class_group_settings(session, class_name)
    if not settings:
        settings = ClassGroupSettings(
            class_id=get_class_id_by_name(session, class_name) or 0,  # 无法解析占位（无实际场景）
            semester_id=get_current_semester_id(session) or 0,
            class_name=class_name,
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def update_class_group_settings(session: Session, class_name: str, max_members: int) -> ClassGroupSettings:
    """更新班级小组人数上限"""
    settings = get_or_create_class_group_settings(session, class_name)
    settings.max_members_per_group = max_members
    settings.updated_at = get_now()
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def get_group_with_members(session: Session, group_id: int) -> Optional[dict]:
    """获取小组详情，包含成员列表和学生姓名"""
    from app.models import Student
    from sqlmodel import col

    group = session.get(Group, group_id)
    if not group:
        return None

    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id)
    ).all()

    # 批量查询学生姓名，避免 N+1
    student_ids = {m.student_id for m in members}
    students = session.exec(
        select(Student).where(col(Student.student_id).in_(student_ids))
    ).all() if student_ids else []
    student_map = {s.student_id: s.name for s in students}

    member_list = [
        {
            "student_id": m.student_id,
            "student_name": student_map.get(m.student_id, "未知"),
            "joined_at": m.joined_at,
        }
        for m in members
    ]

    return {
        "id": group.id,
        "class_name": group.class_name,
        "name": group.name,
        "leader_student_id": group.leader_student_id,
        "is_active": group.is_active,
        "created_at": group.created_at,
        "members": member_list,
    }


def remove_group_member(session: Session, group_id: int, student_id: str) -> bool:
    """踢出小组成员；若踢出的是组长则自动转让"""
    group = session.get(Group, group_id)
    if not group or not group.is_active:
        return False

    member = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.student_id == student_id,
        )
    ).first()
    if not member:
        return False

    # 若踢出的是组长，自动转让
    if group.leader_student_id == student_id:
        other_members = session.exec(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.student_id != student_id,
            )
        ).all()
        if other_members:
            group.leader_student_id = other_members[0].student_id
            session.add(group)
        else:
            # 无其他成员，解散小组
            group.is_active = False
            session.add(group)

    session.delete(member)
    session.commit()
    return True


def dissolve_group(session: Session, group_id: int) -> bool:
    """解散小组（标记为非活跃）"""
    group = session.get(Group, group_id)
    if not group or not group.is_active:
        return False

    group.is_active = False
    session.add(group)
    session.commit()
    return True
