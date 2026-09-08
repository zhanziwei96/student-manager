"""
学生-班级-学期桥接表 — 记录学生每个学期的行政班归属
（方案 docs/SEMESTER_COHORT_REFACTOR_PLAN.md 2.2 桥接表）
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint

from app.core.timezone import get_now


class StudentClassSemesterBase(SQLModel):
    """归属关系基础属性"""
    student_id: str = Field(..., foreign_key="students.student_id", description="学号", index=True)
    class_id: int = Field(..., foreign_key="classes.id", description="行政班ID", index=True)
    semester_id: int = Field(..., foreign_key="semesters.id", description="学期ID", index=True)


class StudentClassSemester(StudentClassSemesterBase, table=True):
    """学生-班级-学期归属表模型 — 每学期每个学生一条记录"""
    __tablename__ = "student_class_semesters"
    __table_args__ = (
        UniqueConstraint('student_id', 'semester_id', name='uix_student_class_semester'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class StudentClassSemesterResponse(StudentClassSemesterBase):
    """归属关系响应"""
    id: int
