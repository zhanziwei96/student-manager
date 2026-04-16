"""
设备绑定模型
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import SQLModel, Field, UniqueConstraint


class DeviceBind(SQLModel, table=True):
    __tablename__ = "device_binds"
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="course_sessions.id", index=True)
    student_id: str = Field(index=True)
    device_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Shanghai")))
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="unique_session_student_bind"),)


class DeviceBindCreate(SQLModel):
    session_id: int
    student_id: str
    device_id: str
