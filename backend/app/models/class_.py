"""
班级模型 — 届+专业下的一个班
（方案 docs/SEMESTER_COHORT_REFACTOR_PLAN.md 2.2）
"""
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint


class ClassBase(SQLModel):
    """班级基础属性"""
    name: str = Field(..., description="班级名（如 1班）", max_length=100)
    major: str = Field(default="", description="专业", max_length=50)
    cohort_year: str = Field(..., description="所属届（入学年份）", max_length=10)


class Class_(ClassBase, table=True):
    """班级表模型（模型类名 Class_ 规避关键字）"""
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint('name', 'major', 'cohort_year', name='uix_class_name_major_cohort'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    # display_name（如 2026届1班）由响应层拼接 cohort_year + name，不做 PG 生成列


class ClassCreate(SQLModel):
    """创建班级请求"""
    name: str
    major: str = ""
    cohort_year: str


class ClassUpdate(SQLModel):
    """更新班级请求（全部 Optional）"""
    name: Optional[str] = None
    major: Optional[str] = None
    cohort_year: Optional[str] = None


class ClassResponse(ClassBase):
    """班级响应"""
    id: int
    display_name: str = ""  # 响应层拼接 "2026届1班"
