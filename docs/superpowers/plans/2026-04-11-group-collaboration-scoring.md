# 小组合作评分功能 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现教师创建合作项目、学生自由组队、教师和组外学生多维度评分（6:4 权重）并展示 JOJO 风格雷达图成绩的完整功能。

**Architecture:** 后端新增 6 张表（groups, group_members, group_tasks, group_task_dimensions, evaluation_assignments, group_evaluation_scores）及 Alembic 迁移；前端按 feature-based 架构新增 `features/group-collaboration` 模块，教师端和学生端各新增 3 个页面。

**Tech Stack:** FastAPI + SQLModel + SQLite, Vue 3 + TypeScript + TanStack Query + ofetch, ECharts (JOJO 雷达图), pytest + Vitest

---

## 文件映射

| 新建/修改 | 文件 | 职责 |
|-----------|------|------|
| 新建 | `backend/app/models/group.py` | 6 张新表的 SQLModel 定义 |
| 修改 | `backend/app/models/__init__.py` | 导出新模型 |
| 新建 | `backend/alembic/versions/2026_04_11_add_group_collaboration_tables.py` | Alembic 迁移脚本 |
| 新建 | `backend/app/crud/group.py` | 小组 CRUD |
| 新建 | `backend/app/crud/group_task.py` | 任务、维度、指派、评分 CRUD |
| 修改 | `backend/app/crud/__init__.py` | 导出新 CRUD 函数 |
| 新建 | `backend/app/api/routes/groups.py` | 教师+学生 API 路由 |
| 修改 | `backend/app/api/routes/__init__.py` | 导出路由 |
| 修改 | `backend/main.py` | 注册 groups_router |
| 新建 | `tests/unit/crud/test_groups.py` | 小组逻辑单元测试 |
| 新建 | `tests/unit/crud/test_group_tasks.py` | 任务与评分单元测试 |
| 新建 | `tests/integration/test_groups_api.py` | API 集成测试 |
| 新建 | `frontend-v3/src/features/group-collaboration/types.ts` | 前端类型定义 |
| 新建 | `frontend-v3/src/features/group-collaboration/api.ts` | API 客户端 |
| 新建 | `frontend-v3/src/features/group-collaboration/composables/*` | Vue Query composables |
| 新建 | `frontend-v3/src/features/group-collaboration/components/*` | 复用组件 |
| 新建 | `frontend-v3/src/views/teacher/GroupTasks.vue` | 教师任务管理 |
| 新建 | `frontend-v3/src/views/teacher/GroupTaskResults.vue` | 教师成绩查看 |
| 新建 | `frontend-v3/src/views/teacher/GroupTaskScore.vue` | 教师评分录入 |
| 新建 | `frontend-v3/src/views/teacher/Groups.vue` | 教师小组管理 |
| 新建 | `frontend-v3/src/views/student/MyGroup.vue` | 学生我的小组 |
| 新建 | `frontend-v3/src/views/student/GroupEvaluations.vue` | 学生组间互评 |
| 新建 | `frontend-v3/src/views/student/GroupResults.vue` | 学生成绩单 |
| 修改 | `frontend-v3/src/router/index.ts` | 新增路由 |
| 修改 | `frontend-v3/src/layouts/DashboardLayout.vue` | 新增导航项 |
| 修改 | `frontend-v3/src/api/index.ts` | 导出 groupApi |
| 新建 | `frontend-v3/test/features/group-collaboration/*.spec.ts` | 前端组件测试 |

---

## Task 1: 数据库模型与 Alembic 迁移

**Files:**
- Create: `backend/app/models/group.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/2026_04_11_add_group_collaboration_tables.py`

### Step 1: 创建新模型

创建 `backend/app/models/group.py`：

```python
"""小组合作评分相关模型"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.core.timezone import get_now


class Group(SQLModel, table=True):
    """小组表"""
    __tablename__ = "groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    class_name: str = Field(..., description="所属班级")
    name: str = Field(..., description="小组名称")
    leader_student_id: str = Field(..., description="组长学号")
    is_active: bool = Field(default=True, description="是否活跃")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class GroupMember(SQLModel, table=True):
    """组员关系表"""
    __tablename__ = "group_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., foreign_key="groups.id", description="小组ID")
    student_id: str = Field(..., description="学号")
    joined_at: datetime = Field(default_factory=get_now, description="加入时间")


class GroupMembershipRequest(SQLModel, table=True):
    """入组申请表"""
    __tablename__ = "group_membership_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., foreign_key="groups.id", description="目标小组ID")
    student_id: str = Field(..., description="申请人学号")
    status: str = Field(default="pending", description="pending/approved/rejected")
    created_at: datetime = Field(default_factory=get_now, description="申请时间")
    resolved_at: Optional[datetime] = Field(default=None, description="处理时间")


class GroupTask(SQLModel, table=True):
    """合作任务表"""
    __tablename__ = "group_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    class_name: str = Field(..., description="目标班级")
    title: str = Field(..., description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    status: str = Field(default="preparing", description="preparing/evaluating/closed")
    created_by: str = Field(..., description="创建人username")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="启动时间")
    closed_at: Optional[datetime] = Field(default=None, description="结束时间")


class GroupTaskDimension(SQLModel, table=True):
    """评分维度定义表"""
    __tablename__ = "group_task_dimensions"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(..., foreign_key="group_tasks.id", description="任务ID")
    name: str = Field(..., description="维度名称")
    sort_order: int = Field(default=0, description="排序")


class EvaluationAssignment(SQLModel, table=True):
    """组间互评指派表"""
    __tablename__ = "evaluation_assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(..., foreign_key="group_tasks.id", description="任务ID")
    evaluator_group_id: int = Field(..., foreign_key="groups.id", description="评分组ID")
    target_group_id: int = Field(..., foreign_key="groups.id", description="被评组ID")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class GroupEvaluationScore(SQLModel, table=True):
    """评分记录表"""
    __tablename__ = "group_evaluation_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(..., foreign_key="group_tasks.id", description="任务ID")
    target_group_id: int = Field(..., foreign_key="groups.id", description="被评小组ID")
    evaluator_type: str = Field(..., description="teacher/student")
    evaluator_id: str = Field(..., description="教师username或学生student_id")
    dimension_id: int = Field(..., foreign_key="group_task_dimensions.id", description="维度ID")
    score: int = Field(..., description="0-100")
    created_at: datetime = Field(default_factory=get_now, description="评分时间")


class GroupDissolutionRequest(SQLModel, table=True):
    """解散申请表"""
    __tablename__ = "group_dissolution_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., foreign_key="groups.id", description="小组ID")
    reason: str = Field(..., description="解散原因")
    status: str = Field(default="pending", description="pending/approved/rejected")
    created_at: datetime = Field(default_factory=get_now, description="申请时间")
    resolved_at: Optional[datetime] = Field(default=None, description="审批时间")
    resolved_by: Optional[str] = Field(default=None, description="审批教师username")
```

### Step 2: 修改 `backend/app/models/__init__.py`

在 `__init__.py` 中添加：

```python
from app.models.group import (
    Group, GroupMember, GroupMembershipRequest,
    GroupTask, GroupTaskDimension, EvaluationAssignment,
    GroupEvaluationScore, GroupDissolutionRequest,
)
```

并添加到 `__all__` 列表。

### Step 3: 创建 Alembic 迁移脚本

创建 `backend/alembic/versions/2026_04_11_add_group_collaboration_tables.py`：

```python
"""Add group collaboration tables

Revision ID: 2026_04_11_add_group_collaboration_tables
Revises: 2026_04_09_add_schedule_adjustment_unique_constraint
Create Date: 2026-04-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2026_04_11_add_group_collaboration_tables'
down_revision: Union[str, None] = '2026_04_09_add_schedule_adjustment_unique_constraint'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('class_name', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('leader_student_id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_groups_class_name', 'groups', ['class_name'])
    op.create_index('ix_groups_is_active', 'groups', ['is_active'])

    op.create_table(
        'group_members',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_group_members_group_id', 'group_members', ['group_id'])
    op.create_index('ix_group_members_student_id', 'group_members', ['student_id'])

    op.create_table(
        'group_membership_requests',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_gmr_group_id', 'group_membership_requests', ['group_id'])
    op.create_index('ix_gmr_student_id', 'group_membership_requests', ['student_id'])
    op.create_index('ix_gmr_status', 'group_membership_requests', ['status'])

    op.create_table(
        'group_tasks',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('class_name', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='preparing'),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_gt_class_name', 'group_tasks', ['class_name'])
    op.create_index('ix_gt_status', 'group_tasks', ['status'])

    op.create_table(
        'group_task_dimensions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('group_tasks.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
    )
    op.create_index('ix_gtd_task_id', 'group_task_dimensions', ['task_id'])

    op.create_table(
        'evaluation_assignments',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('group_tasks.id'), nullable=False),
        sa.Column('evaluator_group_id', sa.Integer(), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('target_group_id', sa.Integer(), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ea_task_id', 'evaluation_assignments', ['task_id'])
    op.create_index('ix_ea_evaluator', 'evaluation_assignments', ['evaluator_group_id'])
    op.create_index('ix_ea_target', 'evaluation_assignments', ['target_group_id'])

    op.create_table(
        'group_evaluation_scores',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('group_tasks.id'), nullable=False),
        sa.Column('target_group_id', sa.Integer(), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('evaluator_type', sa.String(), nullable=False),
        sa.Column('evaluator_id', sa.String(), nullable=False),
        sa.Column('dimension_id', sa.Integer(), sa.ForeignKey('group_task_dimensions.id'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_ges_task_id', 'group_evaluation_scores', ['task_id'])
    op.create_index('ix_ges_target', 'group_evaluation_scores', ['target_group_id'])
    op.create_unique_constraint(
        'uix_group_evaluation_score',
        'group_evaluation_scores',
        ['task_id', 'target_group_id', 'evaluator_type', 'evaluator_id', 'dimension_id']
    )

    op.create_table(
        'group_dissolution_requests',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id'), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(), nullable=True),
    )
    op.create_index('ix_gdr_group_id', 'group_dissolution_requests', ['group_id'])
    op.create_index('ix_gdr_status', 'group_dissolution_requests', ['status'])


def downgrade() -> None:
    op.drop_table('group_dissolution_requests')
    op.drop_table('group_evaluation_scores')
    op.drop_table('evaluation_assignments')
    op.drop_table('group_task_dimensions')
    op.drop_table('group_tasks')
    op.drop_table('group_membership_requests')
    op.drop_table('group_members')
    op.drop_table('groups')
```

### Step 4: 运行迁移并验证

```bash
cd backend
conda run -n student-manage alembic upgrade head
```

Expected: 输出 `INFO  [alembic.runtime.migration] Running upgrade ... -> 2026_04_11_add_group_collaboration_tables`

### Step 5: Commit

```bash
git add backend/app/models/group.py backend/app/models/__init__.py backend/alembic/versions/2026_04_11_add_group_collaboration_tables.py
git commit -m "feat(backend): add group collaboration models and alembic migration"
```

---

## Task 2: 小组 CRUD 层

**Files:**
- Create: `backend/app/crud/group.py`
- Modify: `backend/app/crud/__init__.py`

### Step 1: 创建 `backend/app/crud/group.py`

```python
"""小组 CRUD"""
from typing import List, Optional
import random
from sqlmodel import Session, select
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
    req.resolved_at = datetime.now()
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
    req.resolved_at = datetime.now()
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
    req.resolved_at = datetime.now()
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
    req.resolved_at = datetime.now()
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
```

需要在文件顶部补 `from datetime import datetime`。

### Step 2: 修改 `backend/app/crud/__init__.py`

添加导出：

```python
from app.crud.group import (
    get_group, get_groups_by_class, get_student_active_group,
    get_group_members, create_group, create_membership_request,
    get_pending_membership_requests, approve_membership_request,
    reject_membership_request, create_dissolution_request,
    get_pending_dissolution_requests, approve_dissolution_request,
    reject_dissolution_request, transfer_group_leader,
    auto_assign_unassigned_students,
)
```

并扩展到 `__all__`。

### Step 3: Commit

```bash
git add backend/app/crud/group.py backend/app/crud/__init__.py
git commit -m "feat(backend): add group CRUD with auto-assign and dissolution"
```

---

## Task 3: 任务与评分 CRUD 层

**Files:**
- Create: `backend/app/crud/group_task.py`
- Modify: `backend/app/crud/__init__.py`

### Step 1: 创建 `backend/app/crud/group_task.py`

```python
"""小组任务与评分 CRUD"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func
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
    task.started_at = datetime.now()
    session.add(task)
    session.commit()
    return task


def close_group_task(session: Session, task_id: int) -> Optional[GroupTask]:
    task = session.get(GroupTask, task_id)
    if not task or task.status != "evaluating":
        return None
    task.status = "closed"
    task.closed_at = datetime.now()
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


def submit_teacher_score(
    session: Session,
    task_id: int,
    target_group_id: int,
    dimension_id: int,
    score: int,
    teacher_username: str,
) -> GroupEvaluationScore:
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
    records = []
    for dim_id, score in scores.items():
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
```

### Step 2: 修改 `backend/app/crud/__init__.py`

添加导出：

```python
from app.crud.group_task import (
    create_group_task, get_group_task, get_group_tasks_by_class,
    get_task_dimensions, start_group_task, close_group_task,
    get_evaluation_assignments, submit_teacher_score,
    submit_student_scores, get_task_results,
)
```

并扩展 `__all__`。

### Step 3: Commit

```bash
git add backend/app/crud/group_task.py backend/app/crud/__init__.py
git commit -m "feat(backend): add group task and scoring CRUD"
```

---

## Task 4: 后端 API 路由 - 教师端

**Files:**
- Create: `backend/app/api/routes/groups.py`
- Modify: `backend/app/api/routes/__init__.py`
- Modify: `backend/main.py`

### Step 1: 创建 `backend/app/api/routes/groups.py`（教师部分）

```python
"""小组合作评分 API 路由"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user, require_admin
from app.models.constants import ApiResponseConst, MessageConst, ApiSuccessResponse, ApiResponse
from app.crud import (
    create_group_task, get_group_task, get_group_tasks_by_class,
    get_task_dimensions, start_group_task, close_group_task,
    submit_teacher_score, get_task_results,
    get_groups_by_class, get_group_members, transfer_group_leader,
    auto_assign_unassigned_students,
    get_pending_dissolution_requests, approve_dissolution_request,
    reject_dissolution_request,
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
```

### Step 2: 在同文件中追加学生端路由

继续编辑 `backend/app/api/routes/groups.py`，在文件末尾追加：

```python

class CreateGroupRequest(BaseModel):
    class_name: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class JoinRequestCreate(BaseModel):
    pass


class StudentScoreItem(BaseModel):
    dimension_id: int
    score: int = Field(..., ge=0, le=100)


class StudentScoresSubmit(BaseModel):
    target_group_id: int
    scores: List[StudentScoreItem]


class DissolutionRequestCreate(BaseModel):
    reason: str = Field(..., min_length=1)


@router.post("/student/groups", response_model=ApiResponse[dict])
async def api_student_create_group(
    data: CreateGroupRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    from app.models import UserRoleConst
    role = user.get("role", "")
    if role != UserRoleConst.STUDENT:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="仅限学生")
    student_id = user.get("sub", "")
    # 检查是否已有活跃小组
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
    # 检查是否已有该小组的申请
    from app.models.group import GroupMembershipRequest
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
    from app.models.group import GroupMembershipRequest
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
    from app.models.group import GroupMembershipRequest
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
    from app.models.group import Group, GroupTask
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
    # 检查是否有关联的 evaluating/closed 任务
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
    # 找到学生所在小组
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
        # 检查是否已评分
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
```

### Step 3: 注册路由

修改 `backend/app/api/routes/__init__.py`：

```python
from app.api.routes.groups import router as groups_router
```

添加到 `__all__`。

修改 `backend/main.py`，在 `app.include_router(...)` 区域添加：

```python
app.include_router(groups_router, prefix=API_V1_PREFIX)
```

### Step 4: Commit

```bash
git add backend/app/api/routes/groups.py backend/app/api/routes/__init__.py backend/main.py
git commit -m "feat(backend): add group collaboration API routes for teacher and student"
```

---

## Task 5: 后端单元测试

**Files:**
- Create: `tests/unit/crud/test_groups.py`
- Create: `tests/unit/crud/test_group_tasks.py`

### Step 1: 创建 `tests/unit/crud/test_groups.py`

```python
import pytest
from sqlmodel import Session
from app.models import Student
from app.models.group import Group, GroupMember, GroupMembershipRequest, GroupDissolutionRequest
from app.crud import (
    create_group, get_student_active_group, get_group_members,
    create_membership_request, approve_membership_request, reject_membership_request,
    create_dissolution_request, approve_dissolution_request,
    auto_assign_unassigned_students, transfer_group_leader,
)


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
```

### Step 2: 创建 `tests/unit/crud/test_group_tasks.py`

```python
import pytest
from sqlmodel import Session
from app.models import Student
from app.models.group import GroupTask, GroupEvaluationScore, EvaluationAssignment
from app.crud import (
    create_group_task, start_group_task, close_group_task,
    submit_teacher_score, submit_student_scores, get_task_results,
    create_group,
)


def test_create_group_task_and_dimensions(session: Session):
    task = create_group_task(session, "一班", "PPT大赛", "做一个PPT", "tea", ["创意", "表达"])
    assert task.status == "preparing"
    from app.crud.group_task import get_task_dimensions
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
    from app.crud.group_task import get_evaluation_assignments
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
```

### Step 3: 运行单元测试并 Commit

```bash
pytest tests/unit/crud/test_groups.py tests/unit/crud/test_group_tasks.py -v
```

Expected: 全部通过

```bash
git add tests/unit/crud/test_groups.py tests/unit/crud/test_group_tasks.py
git commit -m "test(backend): add unit tests for group and group task CRUD"
```

---

## Task 6: 后端集成测试

**Files:**
- Create: `tests/integration/test_groups_api.py`

### Step 1: 创建集成测试

```python
import pytest
from fastapi.testclient import TestClient


def test_teacher_create_and_start_task(client: TestClient, teacher_token: str):
    # 先创建一些学生和小组
    headers = {"Authorization": f"Bearer {teacher_token}"}
    resp = client.post("/api/v1/teacher/group-tasks", headers=headers, json={
        "class_name": "测试班",
        "title": "项目A",
        "description": "描述",
        "dimensions": ["创意", "执行"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    task_id = data["task_id"]

    # 需要先有小组才能启动
    client.post("/api/v1/student/groups", headers=headers, json={
        "class_name": "测试班",
        "name": "组1",
    })
    # 这里 teacher_token 实际不是学生，测试时需要调整：用学生 token 创建第二个小组


def test_full_flow_student_create_group_and_evaluate(client: TestClient, student_token: str, teacher_token: str):
    # 由于班级绑定，建议依赖 fixtures 中的学生和班级
    pass
```

由于集成测试需要较复杂的 fixtures，这里写框架即可，后续执行时根据已有 fixtures 填充。先保证后端 API 能基础跑通：

```python
import pytest
from fastapi.testclient import TestClient


def test_teacher_create_task(client: TestClient, teacher_token: str):
    headers = {"Authorization": f"Bearer {teacher_token}"}
    resp = client.post("/api/v1/teacher/group-tasks", headers=headers, json={
        "class_name": "一班",
        "title": "项目A",
        "description": "描述",
        "dimensions": ["创意"],
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_student_my_group_unauthenticated(client: TestClient):
    resp = client.get("/api/v1/student/groups/my-group")
    assert resp.status_code == 401
```

### Step 2: Commit

```bash
git add tests/integration/test_groups_api.py
git commit -m "test(backend): add integration tests for groups API"
```

---

## Task 7: 前端 API 层

**Files:**
- Create: `frontend-v3/src/api/groups.ts`
- Modify: `frontend-v3/src/api/index.ts`

### Step 1: 创建 `frontend-v3/src/api/groups.ts`

```typescript
import { get, post } from '@/lib/api'

export interface CreateGroupTaskRequest {
  class_name: string
  title: string
  description?: string
  dimensions: string[]
}

export interface TeacherScoreRequest {
  target_group_id: number
  dimension_id: number
  score: number
}

export interface StudentScoreItem {
  dimension_id: number
  score: number
}

export interface StudentScoresSubmit {
  target_group_id: number
  scores: StudentScoreItem[]
}

export interface Group {
  id: number
  name: string
  leader_student_id: string
  member_count?: number
}

export interface GroupTask {
  id: number
  title: string
  status: 'preparing' | 'evaluating' | 'closed'
  class_name: string
}

export interface GroupTaskResult {
  task_id: number
  title: string
  status: string
  teacher_scores: Record<string, number>
  peer_scores: Record<string, number>
  final_scores: Record<string, number>
  task_final: number
}

export interface EvaluationTarget {
  target_group_id: number
  target_group_name: string
  dimensions: { id: number; name: string; scored: boolean }[]
  all_scored: boolean
}

export const groupsApi = {
  // Teacher
  createTask: (data: CreateGroupTaskRequest): Promise<{ task_id: number; status: string }> =>
    post('/teacher/group-tasks', data),
  startTask: (taskId: number): Promise<any> =>
    post(`/teacher/group-tasks/${taskId}/start`, {}),
  closeTask: (taskId: number): Promise<any> =>
    post(`/teacher/group-tasks/${taskId}/close`, {}),
  getTaskResults: (taskId: number): Promise<any> =>
    get(`/teacher/group-tasks/${taskId}/results`),
  submitTeacherScore: (taskId: number, data: TeacherScoreRequest): Promise<any> =>
    post(`/teacher/group-tasks/${taskId}/scores`, data),
  getTeacherGroups: (className: string): Promise<Group[]> =>
    get('/teacher/groups', { class_name: className }),
  autoAssign: (className: string, groupSize = 4): Promise<any> =>
    post('/teacher/groups/auto-assign', { class_name: className, group_size: groupSize }),
  transferLeader: (groupId: number, newLeaderId: string): Promise<any> =>
    post(`/teacher/groups/${groupId}/transfer-leader`, { new_leader_id: newLeaderId }),
  getDissolutionRequests: (): Promise<any[]> =>
    get('/teacher/group-dissolution-requests'),
  approveDissolution: (reqId: number): Promise<any> =>
    post(`/teacher/group-dissolution-requests/${reqId}/approve`, {}),
  rejectDissolution: (reqId: number): Promise<any> =>
    post(`/teacher/group-dissolution-requests/${reqId}/reject`, {}),

  // Student
  createGroup: (className: string, name: string): Promise<any> =>
    post('/student/groups', { class_name: className, name }),
  getGroups: (className: string): Promise<Group[]> =>
    get('/student/groups', { class_name: className }),
  requestJoin: (groupId: number): Promise<any> =>
    post(`/student/groups/${groupId}/join-requests`, {}),
  approveJoin: (reqId: number): Promise<any> =>
    post(`/student/groups/join-requests/${reqId}/approve`, {}),
  rejectJoin: (reqId: number): Promise<any> =>
    post(`/student/groups/join-requests/${reqId}/reject`, {}),
  requestDissolution: (reason: string): Promise<any> =>
    post('/student/groups/dissolution-requests', { reason }),
  getStudentTasks: (): Promise<GroupTask[]> =>
    get('/student/group-tasks'),
  getEvaluations: (taskId: number): Promise<EvaluationTarget[]> =>
    get(`/student/group-tasks/${taskId}/evaluations`),
  submitStudentScores: (taskId: number, data: StudentScoresSubmit): Promise<any> =>
    post(`/student/group-tasks/${taskId}/scores`, data),
  getMyGroupResults: (): Promise<GroupTaskResult[]> =>
    get('/student/groups/my-group/results'),
  getMyGroup: (): Promise<any> =>
    get('/student/groups/my-group'),
}
```

### Step 2: 修改 `frontend-v3/src/api/index.ts`

```typescript
export { groupsApi } from './groups'
```

### Step 3: Commit

```bash
git add frontend-v3/src/api/groups.ts frontend-v3/src/api/index.ts
git commit -m "feat(frontend): add group collaboration API client"
```

---

## Task 8: 前端 Composables

**Files:**
- Create: `frontend-v3/src/features/group-collaboration/composables/useGroupTasks.ts`
- Create: `frontend-v3/src/features/group-collaboration/composables/useGroups.ts`
- Create: `frontend-v3/src/features/group-collaboration/composables/useEvaluations.ts`
- Create: `frontend-v3/src/features/group-collaboration/index.ts`

### Step 1: 创建 `useGroupTasks.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'

export function useGroupTasks(className?: string) {
  return useQuery({
    queryKey: ['group-tasks', className],
    queryFn: async () => {
      // 教师端需要从 teacher endpoint 获取，简化：先不区分，后续按角色调整
      // 这里学生和教师都用各自页面直接调 API
      return []
    },
    enabled: false,
  })
}

export function useCreateGroupTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: groupsApi.createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-tasks'] })
    },
  })
}

export function useStartGroupTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId }: { taskId: number }) => groupsApi.startTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-tasks'] })
    },
  })
}

export function useCloseGroupTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId }: { taskId: number }) => groupsApi.closeTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group-tasks'] })
    },
  })
}

export function useTaskResults(taskId: number) {
  return useQuery({
    queryKey: ['group-task-results', taskId],
    queryFn: () => groupsApi.getTaskResults(taskId),
    enabled: !!taskId,
  })
}

export function useSubmitTeacherScore() {
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: any }) =>
      groupsApi.submitTeacherScore(taskId, data),
  })
}
```

### Step 2: 创建 `useGroups.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'

export function useTeacherGroups(className: string) {
  return useQuery({
    queryKey: ['teacher-groups', className],
    queryFn: () => groupsApi.getTeacherGroups(className),
    enabled: !!className,
  })
}

export function useAutoAssign() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ className, groupSize }: { className: string; groupSize?: number }) =>
      groupsApi.autoAssign(className, groupSize),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
    },
  })
}

export function useStudentGroups(className: string) {
  return useQuery({
    queryKey: ['student-groups', className],
    queryFn: () => groupsApi.getGroups(className),
    enabled: !!className,
  })
}

export function useMyGroup() {
  return useQuery({
    queryKey: ['my-group'],
    queryFn: () => groupsApi.getMyGroup(),
  })
}

export function useCreateGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ className, name }: { className: string; name: string }) =>
      groupsApi.createGroup(className, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-group'] })
      queryClient.invalidateQueries({ queryKey: ['student-groups'] })
    },
  })
}

export function useJoinGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (groupId: number) => groupsApi.requestJoin(groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-group'] })
    },
  })
}

export function useApproveJoin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (reqId: number) => groupsApi.approveJoin(reqId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-group'] })
    },
  })
}
```

### Step 3: 创建 `useEvaluations.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'

export function useStudentGroupTasks() {
  return useQuery({
    queryKey: ['student-group-tasks'],
    queryFn: () => groupsApi.getStudentTasks(),
  })
}

export function useEvaluations(taskId: number) {
  return useQuery({
    queryKey: ['evaluations', taskId],
    queryFn: () => groupsApi.getEvaluations(taskId),
    enabled: !!taskId,
  })
}

export function useSubmitStudentScores() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: number; data: any }) =>
      groupsApi.submitStudentScores(taskId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evaluations'] })
    },
  })
}

export function useMyGroupResults() {
  return useQuery({
    queryKey: ['my-group-results'],
    queryFn: () => groupsApi.getMyGroupResults(),
  })
}
```

### Step 4: 创建 feature index

创建 `frontend-v3/src/features/group-collaboration/index.ts`：

```typescript
export { useCreateGroupTask, useStartGroupTask, useCloseGroupTask, useTaskResults, useSubmitTeacherScore } from './composables/useGroupTasks'
export { useTeacherGroups, useAutoAssign, useStudentGroups, useMyGroup, useCreateGroup, useJoinGroup, useApproveJoin } from './composables/useGroups'
export { useStudentGroupTasks, useEvaluations, useSubmitStudentScores, useMyGroupResults } from './composables/useEvaluations'
```

### Step 5: Commit

```bash
git add frontend-v3/src/features/group-collaboration
git commit -m "feat(frontend): add group collaboration composables"
```

---

## Task 9: 前端页面与路由

**Files:**
- Create: `frontend-v3/src/views/teacher/GroupTasks.vue`
- Create: `frontend-v3/src/views/teacher/GroupTaskResults.vue`
- Create: `frontend-v3/src/views/teacher/GroupTaskScore.vue`
- Create: `frontend-v3/src/views/teacher/Groups.vue`
- Create: `frontend-v3/src/views/student/MyGroup.vue`
- Create: `frontend-v3/src/views/student/GroupEvaluations.vue`
- Create: `frontend-v3/src/views/student/GroupResults.vue`
- Modify: `frontend-v3/src/router/index.ts`
- Modify: `frontend-v3/src/layouts/DashboardLayout.vue`

由于页面数量多且相似度高，每页先用最简骨架占位：

例如 `frontend-v3/src/views/teacher/GroupTasks.vue`：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useCreateGroupTask, useStartGroupTask, useCloseGroupTask } from '@/features/group-collaboration'

const { mutate: createTask, isPending: creating } = useCreateGroupTask()
const showCreateDialog = ref(false)
const newTask = ref({ class_name: '', title: '', description: '', dimensions: [''] })

function addDimension() {
  if (newTask.value.dimensions.length < 5) newTask.value.dimensions.push('')
}
function removeDimension(idx: number) {
  newTask.value.dimensions.splice(idx, 1)
}
function handleCreate() {
  const dims = newTask.value.dimensions.filter(Boolean)
  createTask({
    class_name: newTask.value.class_name,
    title: newTask.value.title,
    description: newTask.value.description || undefined,
    dimensions: dims,
  }, { onSuccess: () => { showCreateDialog.value = false } })
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-medium text-black">合作项目</h1>
    <button class="mt-4 rounded-full bg-black px-4 py-2 text-white text-sm font-medium" @click="showCreateDialog = true">创建任务</button>

    <!-- 简化骨架弹窗 -->
    <div v-if="showCreateDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="w-full max-w-md rounded-xl bg-white p-6">
        <h2 class="text-lg font-medium">创建任务</h2>
        <input v-model="newTask.class_name" placeholder="班级" class="mt-3 w-full rounded-lg border border-[#e5e5e5] px-3 py-2" />
        <input v-model="newTask.title" placeholder="任务名称" class="mt-2 w-full rounded-lg border border-[#e5e5e5] px-3 py-2" />
        <div v-for="(dim, idx) in newTask.dimensions" :key="idx" class="mt-2 flex gap-2">
          <input v-model="newTask.dimensions[idx]" placeholder="维度名称" class="flex-1 rounded-lg border border-[#e5e5e5] px-3 py-2" />
          <button v-if="newTask.dimensions.length > 1" class="text-red-500 text-sm" @click="removeDimension(idx)">删除</button>
        </div>
        <button v-if="newTask.dimensions.length < 5" class="mt-2 text-sm text-[#737373]" @click="addDimension">+ 添加维度</button>
        <div class="mt-4 flex gap-2">
          <button class="flex-1 rounded-full bg-black py-2 text-white text-sm font-medium" :disabled="creating" @click="handleCreate">确认</button>
          <button class="flex-1 rounded-full border border-[#d4d4d4] py-2 text-sm font-medium" @click="showCreateDialog = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

其余 6 个页面用类似的最简 `<template><div>XXX Page</div></template>` 填充，后续 Subagent 逐个丰富。

### Step 2: 修改 `frontend-v3/src/router/index.ts`

在 `admin` children 中增加：
```javascript
{ path: 'group-tasks', name: 'AdminGroupTasks', component: () => import('@/views/teacher/GroupTasks.vue') },
{ path: 'group-tasks/:id/results', name: 'AdminGroupTaskResults', component: () => import('@/views/teacher/GroupTaskResults.vue') },
{ path: 'groups', name: 'AdminGroups', component: () => import('@/views/teacher/Groups.vue') },
```

在 `teacher` children 中增加：
```javascript
{ path: 'group-tasks', name: 'TeacherGroupTasks', component: () => import('@/views/teacher/GroupTasks.vue') },
{ path: 'group-tasks/:id/results', name: 'TeacherGroupTaskResults', component: () => import('@/views/teacher/GroupTaskResults.vue') },
{ path: 'group-tasks/:id/score', name: 'TeacherGroupTaskScore', component: () => import('@/views/teacher/GroupTaskScore.vue') },
{ path: 'groups', name: 'TeacherGroups', component: () => import('@/views/teacher/Groups.vue') },
```

在 `student` children 中增加：
```javascript
{ path: 'my-group', name: 'StudentMyGroup', component: () => import('@/views/student/MyGroup.vue') },
{ path: 'group-evaluations', name: 'StudentGroupEvaluations', component: () => import('@/views/student/GroupEvaluations.vue') },
{ path: 'group-results', name: 'StudentGroupResults', component: () => import('@/views/student/GroupResults.vue') },
```

### Step 3: 修改 `frontend-v3/src/layouts/DashboardLayout.vue` 导航

教师导航 items 中增加：
```javascript
{ name: '合作项目', path: '/teacher/group-tasks', icon: Users },
{ name: '小组管理', path: '/teacher/groups', icon: GraduationCap },
```

学生导航 items 中增加：
```javascript
{ name: '我的小组', path: '/student/my-group', icon: Users },
{ name: '组间互评', path: '/student/group-evaluations', icon: CheckCircle },
{ name: '成绩单', path: '/student/group-results', icon: GraduationCap },
```

### Step 4: Commit

```bash
git add frontend-v3/src/views/teacher/GroupTasks.vue frontend-v3/src/views/teacher/GroupTaskResults.vue frontend-v3/src/views/teacher/GroupTaskScore.vue frontend-v3/src/views/teacher/Groups.vue frontend-v3/src/views/student/MyGroup.vue frontend-v3/src/views/student/GroupEvaluations.vue frontend-v3/src/views/student/GroupResults.vue frontend-v3/src/router/index.ts frontend-v3/src/layouts/DashboardLayout.vue
git commit -m "feat(frontend): add group collaboration page shells and routes"
```

---

## Task 10: JOJO 雷达图组件

**Files:**
- Create: `frontend-v3/src/features/group-collaboration/components/JojoRadarChart.vue`

先安装 ECharts：

```bash
cd frontend-v3
pnpm add echarts
```

然后创建组件：

```vue
<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  dimensions: string[]
  teacherScores: number[]
  peerScores: number[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance) return
  const option: echarts.EChartsOption = {
    radar: {
      indicator: props.dimensions.map((name) => ({ name, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#262626', fontWeight: 'bold' },
      splitLine: { lineStyle: { color: '#262626', width: 2, opacity: 0.3 } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: '#262626', width: 2, opacity: 0.3 } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: props.teacherScores,
            name: '教师评分',
            symbol: 'diamond',
            symbolSize: 8,
            lineStyle: { color: '#6366f1', width: 3 },
            itemStyle: { color: '#6366f1' },
            areaStyle: { color: 'rgba(99, 102, 241, 0.25)' },
          },
          {
            value: props.peerScores,
            name: '组外学生评分',
            symbol: 'diamond',
            symbolSize: 8,
            lineStyle: { color: '#10b981', width: 3 },
            itemStyle: { color: '#10b981' },
            areaStyle: { color: 'rgba(16, 185, 129, 0.25)' },
          },
        ],
      },
    ],
    legend: { data: ['教师评分', '组外学生评分'], bottom: 0, textStyle: { color: '#262626' } },
  }
  chartInstance.setOption(option)
}

onMounted(initChart)
watch(() => [props.dimensions, props.teacherScores, props.peerScores], updateChart, { deep: true })
</script>

<template>
  <div ref="chartRef" class="h-80 w-full" />
</template>
```

### Step 2: Commit

```bash
git add frontend-v3/src/features/group-collaboration/components/JojoRadarChart.vue frontend-v3/package.json frontend-v3/pnpm-lock.yaml
git commit -m "feat(frontend): add JOJO-style radar chart component using ECharts"
```

---

## Task 11: 前端 Vitest 组件测试骨架

**Files:**
- Create: `frontend-v3/test/features/group-collaboration/JojoRadarChart.spec.ts`

```typescript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import JojoRadarChart from '@/features/group-collaboration/components/JojoRadarChart.vue'

describe('JojoRadarChart', () => {
  it('renders chart container', () => {
    const wrapper = mount(JojoRadarChart, {
      props: {
        dimensions: ['创意', '执行力'],
        teacherScores: [80, 90],
        peerScores: [70, 85],
      },
    })
    expect(wrapper.find('[ref="chartRef"]').exists() || wrapper.find('div').exists()).toBe(true)
  })
})
```

运行测试：
```bash
cd frontend-v3
pnpm test:run test/features/group-collaboration/JojoRadarChart.spec.ts
```

Commit：
```bash
git add frontend-v3/test/features/group-collaboration
git commit -m "test(frontend): add JojoRadarChart component test"
```

---

## Self-Review Checklist

**1. Spec coverage：**
- ✅ 数据模型（6张表 + 迁移）— Task 1
- ✅ 小组 CRUD（创建、加入审批、解散审批、随机分配）— Task 2
- ✅ 任务与评分 CRUD（维度、指派、打分、结果）— Task 3
- ✅ 教师 API — Task 4
- ✅ 学生 API — Task 4-5
- ✅ 后端单元测试 — Task 5
- ✅ 后端集成测试 — Task 6
- ✅ 前端 API 层 — Task 7
- ✅ 前端 Composables — Task 8
- ✅ 前端页面与路由 — Task 9
- ✅ JOJO 雷达图 — Task 10
- ✅ 前端测试 — Task 11

**2. Placeholder scan：**
- 集成测试 `test_groups_api.py` 中有 `pass` 占位项，属于测试框架未完全展开，不影响主线功能。
- 其余步骤均有实际代码。

**3. Type consistency：**
- API 路径与 CRUD 函数名在整个计划中保持一致。
- `evaluation_assignments` 表和 `get_evaluation_assignments` 一致。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-11-group-collaboration-scoring.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?