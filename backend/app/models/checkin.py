"""
签到相关模型 - SQLModel 版本
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.models.constants import CheckinTypeConst


class CheckinRecord(SQLModel, table=True):
    """签到记录表"""
    __tablename__ = "checkin_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号", index=True)
    student_name: Optional[str] = Field(default=None, description="学生姓名")
    class_name: Optional[str] = Field(default=None, description="班级", index=True)
    checkin_type: str = Field(default=CheckinTypeConst.SELF, description="签到类型")
    checkin_time: datetime = Field(default_factory=datetime.now, description="签到时间")


class ClassSession(SQLModel, table=True):
    """上课状态表"""
    __tablename__ = "class_session"
    
    id: int = Field(default=1, primary_key=True)
    class_name: Optional[str] = Field(default=None, description="当前上课班级")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    active: bool = Field(default=False, description="是否上课中")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class ScoreLog(SQLModel, table=True):
    """分数变更日志表"""
    __tablename__ = "score_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号", index=True)
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
