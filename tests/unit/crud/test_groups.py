import pytest
from sqlmodel import Session
from app.models import Student
from app.models.group import Group, GroupMember, GroupMembershipRequest, GroupDissolutionRequest
from app.crud import (
    create_group, get_student_active_group, get_group_members,
    create_membership_request, approve_membership_request, reject_membership_request,
    create_dissolution_request, approve_dissolution_request,
    auto_assign_unassigned_students, transfer_group_leader,
    get_or_create_class_group_settings, update_class_group_settings,
)


def test_create_group_and_leader_auto_joined(session: Session, seed_refs):
    group = create_group(session, seed_refs["一班"], "先锋组", "stu_001")
    assert group.name == "先锋组"
    assert group.class_id == seed_refs["一班"]
    assert group.semester_id == seed_refs["semester_id"]
    members = get_group_members(session, group.id)
    assert len(members) == 1
    assert members[0].student_id == "stu_001"


def test_get_student_active_group(session: Session, seed_refs):
    create_group(session, seed_refs["一班"], "先锋组", "stu_001")
    g = get_student_active_group(session, "stu_001", seed_refs["一班"])
    assert g is not None
    assert g.name == "先锋组"


def test_membership_request_approval_moves_student(session: Session, seed_refs):
    g1 = create_group(session, seed_refs["一班"], "先锋组", "stu_001")
    g2 = create_group(session, seed_refs["一班"], "勇者组", "stu_002")
    req = create_membership_request(session, g2.id, "stu_001")
    approved = approve_membership_request(session, req.id)
    assert approved is not None
    active = get_student_active_group(session, "stu_001", seed_refs["一班"])
    assert active.id == g2.id


def test_auto_assign_creates_groups(session: Session, seed_refs):
    for i in range(6):
        s = Student(student_id=f"s{i}", name=f"S{i}",
                    class_id=seed_refs["二班"])
        session.add(s)
    session.commit()
    new_groups = auto_assign_unassigned_students(session, seed_refs["二班"], group_size=3)
    assert len(new_groups) == 2
    members_count = sum(len(get_group_members(session, g.id)) for g in new_groups)
    assert members_count == 6


def test_transfer_leader(session: Session, seed_refs):
    g = create_group(session, seed_refs["一班"], "先锋组", "stu_001")
    # add another member
    session.add(GroupMember(group_id=g.id, student_id="stu_002"))
    session.commit()
    updated = transfer_group_leader(session, g.id, "stu_002")
    assert updated.leader_student_id == "stu_002"


def test_dissolution_approval(session: Session, seed_refs):
    g = create_group(session, seed_refs["一班"], "先锋组", "stu_001")
    req = create_dissolution_request(session, g.id, "组员都转学了")
    approved = approve_dissolution_request(session, req.id, "teacher_001")
    assert approved is not None
    assert approved.is_active is False


def test_get_or_create_class_group_settings_creates_default(session: Session, seed_refs):
    settings = get_or_create_class_group_settings(session, seed_refs["一班"])
    assert settings.class_id == seed_refs["一班"]
    assert settings.semester_id == seed_refs["semester_id"]
    assert settings.max_members_per_group == 5


def test_get_or_create_class_group_settings_returns_existing(session: Session, seed_refs):
    settings1 = get_or_create_class_group_settings(session, seed_refs["一班"])
    settings2 = get_or_create_class_group_settings(session, seed_refs["一班"])
    assert settings1.class_id == settings2.class_id
    assert settings2.max_members_per_group == 5


def test_update_class_group_settings(session: Session, seed_refs):
    get_or_create_class_group_settings(session, seed_refs["一班"])
    updated = update_class_group_settings(session, seed_refs["一班"], 8)
    assert updated.max_members_per_group == 8
