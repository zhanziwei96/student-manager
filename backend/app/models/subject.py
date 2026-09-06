"""
科目模型 - 学生科目分数系统
"""
from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlmodel import SQLModel, Field
from sqlalchemy import Index, desc
from app.core.timezone import get_now
from app.core.term import get_current_term


class Subject(SQLModel, table=True):
    """科目表（全局共享，从课表推导）"""
    __tablename__ = "subjects"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., description="科目名称（如'数学'）", max_length=100)
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20, index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")

    __table_args__ = (
        # 同一学期内科目名称唯一
        sa.UniqueConstraint("name", "semester", name="uix_subject_name_semester"),
    )


class StudentSubjectScore(SQLModel, table=True):
    """学生科目分数表（按科目独立管理）"""
    __tablename__ = "student_subject_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号", max_length=50, index=True)
    subject_id: int = Field(..., foreign_key="subjects.id", description="科目ID", index=True)
    teacher_id: int = Field(..., foreign_key="users.id", description="教师ID（该学生这个科目的授课教师）", index=True)
    score: float = Field(default=70.0, description="分数", index=True)
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20, index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")

    __table_args__ = (
        # 同一学生同一科目同一学期同一教师唯一（学期中换老师新建记录）
        sa.UniqueConstraint("student_id", "subject_id", "teacher_id", "semester", name="uix_student_subject_teacher_semester"),
    )


class StudentSubjectScoreLog(SQLModel, table=True):
    """学生科目分数变更日志表"""
    __tablename__ = "student_subject_score_logs"
    __table_args__ = (
        Index('idx_subject_score_logs_student_created_at', 'student_id', desc('created_at')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号")
    subject_id: int = Field(..., description="科目ID")
    teacher_id: int = Field(..., description="教师ID（操作时的授课教师）")
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
