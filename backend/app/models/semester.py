"""
学期模型 — 学期实体化，替代 .env TermSettings 配置
（方案 docs/SEMESTER_COHORT_REFACTOR_PLAN.md 2.2）
"""
from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field


class SemesterBase(SQLModel):
    """学期基础属性"""
    label: str = Field(..., description="学期标识（如 2026-2027-1）", max_length=20)
    start_date: date = Field(..., description="开学第一天")
    total_weeks: int = Field(..., description="总周数")
    is_current: bool = Field(default=False, description="当前学期标记", index=True)
    status: str = Field(default="active", description="状态: active|archived", max_length=20)


class Semester(SemesterBase, table=True):
    """学期表模型"""
    __tablename__ = "semesters"

    id: Optional[int] = Field(default=None, primary_key=True)


class SemesterCreate(SQLModel):
    """创建学期请求"""
    label: str
    start_date: date
    total_weeks: int


class SemesterUpdate(SQLModel):
    """更新学期请求（全部 Optional）"""
    start_date: Optional[date] = None
    total_weeks: Optional[int] = None
    is_current: Optional[bool] = None
    status: Optional[str] = None


class SemesterResponse(SemesterBase):
    """学期响应"""
    id: int
