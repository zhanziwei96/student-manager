"""
课程会话模型 - 单次上课实例 + 课表调整记录
"""
from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Index, text, UniqueConstraint
from app.core.timezone import get_now
from app.core.term import get_current_term


class CourseSessionBase(SQLModel):
    """课程会话基础模型"""
    schedule_id: Optional[int] = Field(
        default=None,
        foreign_key="course_schedules.id",
        description="关联的课表ID"
    )
    session_code: str = Field(..., description="课堂唯一代码", max_length=16)
    course_name: Optional[str] = Field(default=None, description="课程名称", max_length=100)
    class_name: str = Field(..., description="班级名称", max_length=100)
    class_id: Optional[int] = Field(
        default=None, foreign_key="classes.id", index=True,
        description="班级ID（FK，双写过渡期可空）",
    )
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True,
        description="学期ID（FK，双写过渡期可空）",
    )
    classroom: Optional[str] = Field(default=None, description="教室", max_length=50)
    teacher_id: int = Field(..., description="教师ID")
    teacher_name: Optional[str] = Field(default=None, description="教师姓名", max_length=50)
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    week_number: Optional[int] = Field(default=None, description="教学周次")
    status: str = Field(default="active", description="课堂状态: scheduled|active|ended|cancelled", max_length=20)
    source_type: str = Field(default="manual", description="来源类型: scheduled|manual|makeup", max_length=20)


class CourseSession(CourseSessionBase, table=True):
    """课程会话数据库模型"""
    __tablename__ = "course_sessions"
    __table_args__ = (
        # 同一班级同一学期在同一时间只能有一个活跃课堂（第二学期：加 semester 维度）
        Index(
            'uix_active_class_semester',
            'class_name',
            'semester',
            unique=True,
            sqlite_where=text('status="active"'),
            postgresql_where=text("status='active'")
        ),
        # 性能优化索引
        Index('ix_sessions_schedule_week', 'schedule_id', 'week_number'),
        Index('ix_sessions_teacher_id', 'teacher_id'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    semester: Optional[str] = Field(
        default_factory=get_current_term,
        description="学期标识（如 2026-2027-1）",
        max_length=20,
        index=True
    )
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")


class CourseSessionResponse(CourseSessionBase):
    """课程会话响应模型"""
    id: int
    updated_at: str


class ScheduleAdjustmentBase(SQLModel):
    """课表调整基础模型"""
    schedule_id: int = Field(..., foreign_key="course_schedules.id", description="关联课表ID")
    week_number: int = Field(..., description="第几周")
    type: str = Field(..., description="调整类型: cancel|modify|makeup", max_length=20)
    new_date: Optional[date] = Field(default=None, description="新日期")
    new_start_time: Optional[str] = Field(default=None, description="新开始时间", max_length=10)
    new_end_time: Optional[str] = Field(default=None, description="新结束时间", max_length=10)
    new_classroom: Optional[str] = Field(default=None, description="新教室", max_length=50)
    generated_session_id: Optional[int] = Field(
        default=None,
        foreign_key="course_sessions.id",
        description="补课生成的课堂实例ID"
    )
    reason: Optional[str] = Field(default=None, description="调整原因", max_length=200)
    created_by: int = Field(..., description="操作人ID")


class ScheduleAdjustment(ScheduleAdjustmentBase, table=True):
    """课表调整记录数据库模型"""
    __tablename__ = "schedule_adjustments"
    __table_args__ = (
        # 同一课表同一周次只能有一条调整记录
        UniqueConstraint('schedule_id', 'week_number', name='uix_schedule_week'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    semester: Optional[str] = Field(
        default_factory=get_current_term,
        description="学期标识（如 2026-2027-1）",
        max_length=20,
        index=True
    )
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True,
        description="学期ID（FK，双写过渡期可空）",
    )
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class ScheduleAdjustmentResponse(ScheduleAdjustmentBase):
    """课表调整响应模型"""
    id: int
    created_at: str
