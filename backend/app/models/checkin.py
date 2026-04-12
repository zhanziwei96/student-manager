"""
签到相关模型 - SQLModel 版本
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint
from sqlalchemy import Index, desc
from app.models.constants import CheckinTypeConst
from app.core.timezone import get_now


class CheckinRecord(SQLModel, table=True):
    """签到记录表"""
    __tablename__ = "checkin_records"
    __table_args__ = (
        # 同一学生在同一课堂只能签到一次
        UniqueConstraint('session_id', 'student_id', name='idx_unique_session_student'),
        Index('idx_checkin_records_checkin_time', desc('checkin_time')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(
        default=None,
        foreign_key="course_sessions.id",
        description="课堂会话ID",
        index=True
    )
    student_id: str = Field(..., description="学号", index=True)
    student_name: Optional[str] = Field(default=None, description="学生姓名")
    class_name: Optional[str] = Field(default=None, description="班级", index=True)
    checkin_type: str = Field(default=CheckinTypeConst.SELF, description="签到类型")
    checkin_time: datetime = Field(default_factory=get_now, description="签到时间")
    device_id: Optional[str] = Field(default=None, description="设备指纹ID", index=True)
    device_info: Optional[str] = Field(default=None, description="设备信息JSON")


class ScoreLog(SQLModel, table=True):
    """分数变更日志表"""
    __tablename__ = "score_logs"
    __table_args__ = (
        Index('idx_score_logs_student_created_at', 'student_id', desc('created_at')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号")
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
