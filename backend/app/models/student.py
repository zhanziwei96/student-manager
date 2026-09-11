"""
学生模型 - SQLModel 版本
与现有 students 表结构兼容
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from app.core.timezone import get_now


class StudentBase(SQLModel):
    """学生基础属性"""
    student_id: str = Field(..., description="学号", primary_key=True)
    name: str = Field(..., description="姓名")
    class_id: Optional[int] = Field(
        default=None, foreign_key="classes.id", index=True,
        description="当前班级（冗余缓存，真源见 student_class_semesters）",
    )
    cohort_year: Optional[str] = Field(
        default=None, index=True, max_length=10,
        description="届（身份属性=入学年，不随转班更新）",
    )
    status: str = Field(
        default="active", max_length=20,
        description="学籍状态: active|suspended|withdrawn|graduated",
    )
    is_account_enabled: bool = Field(default=True, description="账户是否启用")


class Student(StudentBase, table=True):
    """学生表模型"""
    __tablename__ = "students"

    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")
    password_hash: Optional[str] = Field(default=None, description="密码哈希 (bcrypt)")
    login_fail_count: int = Field(default=0, description="登录失败次数")
    locked_until: Optional[datetime] = Field(default=None, description="锁定截止时间")
    version: int = Field(default=1, description="乐观锁版本号")
    



class StudentCreate(StudentBase):
    """创建学生请求"""
    pass


class StudentUpdate(SQLModel):
    """更新学生请求"""
    name: Optional[str] = None


class StudentResponse(StudentBase):
    """学生响应"""
    # 响应字段（非 ORM 列）：班级展示名由 API 层按 class_id 运行时解析注入
    class_name: Optional[str] = Field(default=None, description="班级展示名（由 class_id 解析，未分班为'未分班'）")
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
