"""
学生模型 - SQLModel 版本
与现有 students 表结构兼容
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class StudentBase(SQLModel):
    """学生基础属性"""
    student_id: str = Field(..., description="学号", primary_key=True)
    name: str = Field(..., description="姓名")
    class_name: str = Field(default="未分班", description="班级")
    score: float = Field(default=70.0, description="分数")
    is_active: bool = Field(default=True, description="是否激活")


class Student(StudentBase, table=True):
    """学生表模型"""
    __tablename__ = "students"
    
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")
    password_hash: Optional[str] = Field(default=None, description="密码哈希")
    salt: Optional[str] = Field(default=None, description="密码盐值")


class StudentCreate(StudentBase):
    """创建学生请求"""
    pass


class StudentUpdate(SQLModel):
    """更新学生请求"""
    name: Optional[str] = None
    class_name: Optional[str] = None
    score: Optional[float] = None


class StudentResponse(StudentBase):
    """学生响应"""
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
