"""
课表模型 - 用于管理课程安排
"""
from typing import Optional
from datetime import time
from sqlmodel import SQLModel, Field


class CourseScheduleBase(SQLModel):
    """课表基础模型"""
    course_name: str = Field(..., description="课程名称", max_length=100)
    class_name: str = Field(..., description="班级名称", max_length=100)
    teacher_id: Optional[int] = Field(default=None, description="教师ID")
    teacher_name: Optional[str] = Field(default=None, description="教师姓名", max_length=50)
    day_of_week: int = Field(..., description="星期几 (1-7)", ge=1, le=7)
    start_time: str = Field(..., description="开始时间 (HH:MM)")
    end_time: str = Field(..., description="结束时间 (HH:MM)")
    classroom: Optional[str] = Field(default=None, description="教室", max_length=50)
    week_start: int = Field(default=1, description="开始周次", ge=1)
    week_end: int = Field(default=20, description="结束周次", ge=1)


class CourseSchedule(CourseScheduleBase, table=True):
    """课表数据库模型"""
    __tablename__ = "course_schedules"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[str] = Field(default=None, description="创建时间")
    updated_at: Optional[str] = Field(default=None, description="更新时间")


class CourseScheduleResponse(CourseScheduleBase):
    """课表响应模型"""
    id: int
    created_at: Optional[str] = None


class CourseScheduleImport(SQLModel):
    """课表导入数据模型"""
    course_name: str
    class_name: str
    teacher_name: str
    day_of_week: int
    start_time: str
    end_time: str
    classroom: Optional[str] = None
    week_start: int = 1
    week_end: int = 20
