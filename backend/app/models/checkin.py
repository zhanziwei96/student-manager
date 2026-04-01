"""
签到相关模型 - SQLModel 版本
"""
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from sqlmodel import SQLModel, Field
from app.models.constants import CheckinTypeConst

# 上海时区
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def get_shanghai_now() -> datetime:
    """获取上海时区的当前时间"""
    return datetime.now(SHANGHAI_TZ)


class CheckinRecord(SQLModel, table=True):
    """签到记录表"""
    __tablename__ = "checkin_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, description="课堂会话ID", index=True)
    student_id: str = Field(..., description="学号", index=True)
    student_name: Optional[str] = Field(default=None, description="学生姓名")
    class_name: Optional[str] = Field(default=None, description="班级", index=True)
    checkin_type: str = Field(default=CheckinTypeConst.SELF, description="签到类型")
    checkin_time: datetime = Field(default_factory=get_shanghai_now, description="签到时间")
    
    # 地理位置和设备信息字段
    checkin_lat: Optional[float] = Field(default=None, description="签到时纬度")
    checkin_lng: Optional[float] = Field(default=None, description="签到时经度")
    checkin_distance: Optional[float] = Field(default=None, description="与签到中心的距离（米）")
    device_id: Optional[str] = Field(default=None, description="设备指纹ID", index=True)
    device_info: Optional[str] = Field(default=None, description="设备信息JSON")


class ClassSession(SQLModel, table=True):
    """上课状态表 - 支持多教师同时上课，每次开始新课堂创建新记录"""
    __tablename__ = "class_session"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_code: Optional[str] = Field(default=None, description="课堂唯一代码", index=True)
    course_name: Optional[str] = Field(default=None, description="课程名称")
    class_name: Optional[str] = Field(default=None, description="当前上课班级", index=True)
    teacher_id: Optional[int] = Field(default=None, description="上课教师ID", index=True)
    teacher_name: Optional[str] = Field(default=None, description="上课教师姓名")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    active: bool = Field(default=False, description="是否上课中")
    updated_at: datetime = Field(default_factory=get_shanghai_now, description="更新时间")
    
    # 地理位置字段
    location_lat: Optional[float] = Field(default=None, description="签到中心纬度")
    location_lng: Optional[float] = Field(default=None, description="签到中心经度")
    location_name: Optional[str] = Field(default=None, description="位置名称，如'机房312'")
    checkin_radius: int = Field(default=100, description="允许签到半径（米），默认100米")


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
