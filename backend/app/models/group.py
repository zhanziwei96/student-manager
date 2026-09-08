"""
小组协作模型 - SQLModel 版本
"""
from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlmodel import SQLModel, Field
from sqlalchemy import Index, desc
from app.core.timezone import get_now
from app.core.term import get_current_term


class Group(SQLModel, table=True):
    """小组表"""
    __tablename__ = "groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    semester: Optional[str] = Field(
        default_factory=get_current_term,
        description="学期标识（如 2026-2027-1）",
        max_length=20,
        index=True
    )
    class_name: str = Field(..., description="班级名称", max_length=100, index=True)
    class_id: Optional[int] = Field(
        default=None, foreign_key="classes.id", index=True,
        description="班级ID（FK，双写过渡期可空）",
    )
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True,
        description="学期ID（FK，双写过渡期可空）",
    )
    subject_id: Optional[int] = Field(default=None, foreign_key="subjects.id", description="科目ID（过渡期保留，Phase 4 删除）", index=True)
    course_id: Optional[int] = Field(default=None, foreign_key="courses.id", description="课程ID（小组按科目划分）", index=True)
    name: str = Field(..., description="小组名称", max_length=100)
    leader_student_id: str = Field(..., description="组长学号", max_length=50, index=True)
    score: float = Field(default=0.0, description="小组平时分", index=True)
    version: int = Field(default=1, description="乐观锁版本号")
    is_active: bool = Field(default=True, description="是否有效")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class GroupMember(SQLModel, table=True):
    """小组成员表"""
    __tablename__ = "group_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., foreign_key="groups.id", description="小组ID", index=True)
    student_id: str = Field(..., description="学号", max_length=50, index=True)
    joined_at: datetime = Field(default_factory=get_now, description="加入时间")


class GroupMembershipRequest(SQLModel, table=True):
    """入组申请表"""
    __tablename__ = "group_membership_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., foreign_key="groups.id", description="小组ID", index=True)
    student_id: str = Field(..., description="学号", max_length=50, index=True)
    status: str = Field(default="pending", description="状态: pending|approved|rejected", max_length=20)
    created_at: datetime = Field(default_factory=get_now, description="申请时间")
    resolved_at: Optional[datetime] = Field(default=None, description="处理时间")


class GroupTask(SQLModel, table=True):
    """小组任务表"""
    __tablename__ = "group_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    semester: Optional[str] = Field(
        default_factory=get_current_term,
        description="学期标识（如 2026-2027-1）",
        max_length=20,
        index=True
    )
    class_name: str = Field(..., description="班级名称", max_length=100, index=True)
    title: str = Field(..., description="任务标题", max_length=200)
    description: Optional[str] = Field(default=None, description="任务描述")
    status: str = Field(default="preparing", description="状态: preparing|evaluating|closed", max_length=20)
    created_by: str = Field(..., description="创建人用户名（教师）", max_length=50)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    closed_at: Optional[datetime] = Field(default=None, description="结束时间")


class GroupTaskDimension(SQLModel, table=True):
    """小组任务评分维度表"""
    __tablename__ = "group_task_dimensions"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(..., foreign_key="group_tasks.id", description="任务ID", index=True)
    name: str = Field(..., description="维度名称", max_length=100)
    sort_order: int = Field(default=0, description="排序")


class EvaluationAssignment(SQLModel, table=True):
    """互评分配表"""
    __tablename__ = "evaluation_assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(..., foreign_key="group_tasks.id", description="任务ID", index=True)
    evaluator_group_id: int = Field(..., foreign_key="groups.id", description="评分小组ID", index=True)
    target_group_id: int = Field(..., foreign_key="groups.id", description="被评分小组ID", index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class GroupEvaluationScore(SQLModel, table=True):
    """小组评分结果表"""
    __tablename__ = "group_evaluation_scores"
    __table_args__ = (
        sa.UniqueConstraint("task_id", "target_group_id", "evaluator_type", "evaluator_id", "dimension_id", name="uix_evaluation_score"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    semester: Optional[str] = Field(
        default_factory=get_current_term,
        description="学期标识（如 2026-2027-1）",
        max_length=20,
        index=True
    )
    task_id: int = Field(..., foreign_key="group_tasks.id", description="任务ID", index=True)
    target_group_id: int = Field(..., foreign_key="groups.id", description="被评分小组ID", index=True)
    evaluator_type: str = Field(..., description="评分方类型: teacher|student", max_length=20)
    evaluator_id: str = Field(..., description="评分方标识（教师用户名或学生学号）", max_length=50)
    dimension_id: int = Field(..., foreign_key="group_task_dimensions.id", description="维度ID", index=True)
    score: int = Field(..., ge=0, le=100, description="分数（0-100）")
    created_at: datetime = Field(default_factory=get_now, description="打分时间")


class GroupDissolutionRequest(SQLModel, table=True):
    """解散小组申请"""
    __tablename__ = "group_dissolution_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., foreign_key="groups.id", description="小组ID", index=True)
    reason: str = Field(..., description="解散原因")
    status: str = Field(default="pending", description="状态: pending|approved|rejected", max_length=20)
    created_at: datetime = Field(default_factory=get_now, description="申请时间")
    resolved_at: Optional[datetime] = Field(default=None, description="处理时间")
    resolved_by: Optional[str] = Field(default=None, description="处理人用户名", max_length=50)


class ClassGroupSettings(SQLModel, table=True):
    """班级小组设置表（复合主键 (class_id, semester_id)，class_name 为冗余快照）"""
    __tablename__ = "class_group_settings"

    class_id: int = Field(..., foreign_key="classes.id", primary_key=True, description="班级ID")
    semester_id: int = Field(..., foreign_key="semesters.id", primary_key=True, description="学期ID")
    class_name: str = Field(default="", description="班级名称（冗余快照）", max_length=100)
    max_members_per_group: int = Field(default=5, description="每组上限人数")
    updated_at: datetime = Field(default_factory=get_now, description="最后修改时间")


class GroupScoreLog(SQLModel, table=True):
    """小组分数变更日志表"""
    __tablename__ = "group_score_logs"
    __table_args__ = (
        Index('idx_group_score_logs_group_created_at', 'group_id', desc('created_at')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(..., description="小组ID", index=True)
    subject_id: Optional[int] = Field(default=None, description="科目ID")
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20)
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True,
        description="学期ID（FK，双写过渡期可空）",
    )
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
