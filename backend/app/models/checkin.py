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
    student_name: Optional[str] = Field(default=None, description="学生姓名（展示快照）")
    class_id: Optional[int] = Field(
        default=None, foreign_key="classes.id", index=True,
        description="班级ID（FK；历史签到可空）",
    )
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True,
        description="学期ID（FK）",
    )
    checkin_type: str = Field(default=CheckinTypeConst.SELF, description="签到类型")
    checkin_time: datetime = Field(default_factory=get_now, description="签到时间")
    device_id: Optional[str] = Field(default=None, description="设备指纹ID", index=True)
    device_info: Optional[str] = Field(default=None, description="设备信息JSON")
    qr_signature: str | None = Field(default=None, description="二维码签名")
    device_bound: bool = Field(default=True, description="是否绑定设备")
