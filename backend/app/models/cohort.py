"""
届模型 — 一届学生，入学年份相同
（方案 docs/SEMESTER_COHORT_REFACTOR_PLAN.md 2.2）
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class CohortBase(SQLModel):
    """届基础属性"""
    year: str = Field(..., description="届（入学年份，如 2026）", primary_key=True, max_length=10)
    label: str = Field(default="", description="显示名（如 2026届）", max_length=50)
    status: str = Field(default="active", description="状态: active|graduated", max_length=20)


class Cohort(CohortBase, table=True):
    """届表模型"""
    __tablename__ = "cohorts"

    entry_semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", description="入学学期"
    )


class CohortCreate(SQLModel):
    """创建届请求"""
    year: str
    label: str = ""
    entry_semester_id: Optional[int] = None


class CohortUpdate(SQLModel):
    """更新届请求（全部 Optional）"""
    label: Optional[str] = None
    entry_semester_id: Optional[int] = None
    status: Optional[str] = None


class CohortResponse(CohortBase):
    """届响应"""
    entry_semester_id: Optional[int] = None
