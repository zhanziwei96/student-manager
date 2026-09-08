import pytest
from sqlmodel import Session, select
from app.models import Student
from app.models.group import Group, GroupMember, GroupMembershipRequest, GroupDissolutionRequest, GroupTask


def _seed_class_and_semester(session):
    """seed 届/班/当前学期（复合主键设置表依赖）"""
    from datetime import date
    from app.models import Cohort, Class_, Semester

    if session.exec(select(Cohort).where(Cohort.year == "2026")).first() is None:
        session.add(Cohort(year="2026"))
    if session.exec(select(Class_).where(Class_.name == "一班")).first() is None:
        session.add(Class_(name="一班", cohort_year="2026"))
    if session.exec(select(Semester).where(Semester.is_current.is_(True))).first() is None:
        session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                             total_weeks=20, is_current=True))
    session.commit()
from app.crud import (
    create_group, get_student_active_group, get_group_members,
    create_membership_request, approve_membership_request, reject_membership_request,
    create_dissolution_request, approve_dissolution_request,
    auto_assign_unassigned_students, transfer_group_leader,
    get_or_create_class_group_settings, update_class_group_settings,
    create_group_task, start_group_task,
)


@pytest.fixture
def evaluating_task(session: Session):
    """创建一个处于 evaluating 状态的合作任务"""
    # 先创建学生记录，再创建小组，避免 GroupMember 引用不存在的 Student
    for sid, name in [("assigned_stu", "已组队学生"), ("assigned_stu2", "已组队学生2")]:
        session.add(Student(student_id=sid, name=name, class_name="互评班"))
    session.commit()
    task = create_group_task(session, "互评班", "PPT大赛", None, "tea", ["创意"])
    g1 = create_group(session, "互评班", "G1", "assigned_stu")
    g2 = create_group(session, "互评班", "G2", "assigned_stu2")
    started = start_group_task(session, task.id)
    assert started.status == "evaluating"
    return started


@pytest.fixture
def unassigned_student(session: Session):
    """创建一个未分配小组的学生"""
    student = Student(student_id="unassigned_001", name="未组队学生", class_name="互评班")
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


@pytest.fixture
def assigned_student(session: Session, evaluating_task):
    """返回已有小组的学生（在 evaluating_task 创建时已写入 DB）"""
    student = session.exec(
        select(Student).where(Student.student_id == "assigned_stu")
    ).first()
    assert student is not None, "assigned_stu 应在 evaluating_task fixture 中已创建"
    return student


def test_create_group_and_leader_auto_joined(session: Session):
    group = create_group(session, "一班", "先锋组", "stu_001")
    assert group.name == "先锋组"
    members = get_group_members(session, group.id)
    assert len(members) == 1
    assert members[0].student_id == "stu_001"


def test_get_student_active_group(session: Session):
    create_group(session, "一班", "先锋组", "stu_001")
    g = get_student_active_group(session, "stu_001", "一班")
    assert g is not None
    assert g.name == "先锋组"


def test_membership_request_approval_moves_student(session: Session):
    g1 = create_group(session, "一班", "先锋组", "stu_001")
    g2 = create_group(session, "一班", "勇者组", "stu_002")
    req = create_membership_request(session, g2.id, "stu_001")
    approved = approve_membership_request(session, req.id)
    assert approved is not None
    active = get_student_active_group(session, "stu_001", "一班")
    assert active.id == g2.id


def test_auto_assign_creates_groups(session: Session):
    for i in range(6):
        s = Student(student_id=f"s{i}", name=f"S{i}", class_name="二班")
        session.add(s)
    session.commit()
    new_groups = auto_assign_unassigned_students(session, "二班", group_size=3)
    assert len(new_groups) == 2
    members_count = sum(len(get_group_members(session, g.id)) for g in new_groups)
    assert members_count == 6


def test_transfer_leader(session: Session):
    g = create_group(session, "一班", "先锋组", "stu_001")
    # add another member
    session.add(GroupMember(group_id=g.id, student_id="stu_002"))
    session.commit()
    updated = transfer_group_leader(session, g.id, "stu_002")
    assert updated.leader_student_id == "stu_002"


def test_dissolution_approval(session: Session):
    g = create_group(session, "一班", "先锋组", "stu_001")
    req = create_dissolution_request(session, g.id, "组员都转学了")
    approved = approve_dissolution_request(session, req.id, "teacher_001")
    assert approved is not None
    assert approved.is_active is False


def test_get_or_create_class_group_settings_creates_default(session: Session):
    _seed_class_and_semester(session)
    settings = get_or_create_class_group_settings(session, "一班")
    assert settings.class_name == "一班"
    assert settings.max_members_per_group == 5


def test_get_or_create_class_group_settings_returns_existing(session: Session):
    _seed_class_and_semester(session)
    settings1 = get_or_create_class_group_settings(session, "一班")
    settings2 = get_or_create_class_group_settings(session, "一班")
    assert settings1.class_name == settings2.class_name
    assert settings2.max_members_per_group == 5


def test_update_class_group_settings(session: Session):
    _seed_class_and_semester(session)
    get_or_create_class_group_settings(session, "一班")
    updated = update_class_group_settings(session, "一班", 8)
    assert updated.max_members_per_group == 8


def test_check_class_not_evaluating_allows_unassigned_student(session, evaluating_task, unassigned_student):
    """测试未分配小组学生在互评阶段可以创建和加入小组"""
    from app.api.routes.groups import _check_class_not_evaluating

    # 不应抛出异常
    _check_class_not_evaluating(session, evaluating_task.class_name, unassigned_student.student_id)


def test_check_class_not_evaluating_blocks_assigned_student(session, evaluating_task, assigned_student):
    """测试已有小组学生在互评阶段不能进行操作"""
    from app.api.routes.groups import _check_class_not_evaluating

    # 应该抛出 HTTPException
    with pytest.raises(Exception) as exc_info:
        _check_class_not_evaluating(session, evaluating_task.class_name, assigned_student.student_id)
    assert "班级正在互评阶段，不可变更小组" in str(exc_info.value.detail)


def test_check_class_not_evaluating_blocks_without_student_id(session, evaluating_task):
    """测试不提供学生ID时，互评阶段禁止操作"""
    from app.api.routes.groups import _check_class_not_evaluating

    with pytest.raises(Exception) as exc_info:
        _check_class_not_evaluating(session, evaluating_task.class_name)
    assert "班级正在互评阶段，不可变更小组" in str(exc_info.value.detail)


def test_check_class_not_evaluating_allows_when_no_evaluation(session):
    """测试非互评阶段，所有操作都允许"""
    from app.api.routes.groups import _check_class_not_evaluating

    # 不应抛出异常
    _check_class_not_evaluating(session, "普通班")
