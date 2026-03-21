"""
签到记录实体
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from infrastructure.config import ScoreConfig


class CheckinType(Enum):
    """签到类型"""
    SELF = "自主签到"
    TEACHER = "老师代签"
    AUTO = "系统自动"


@dataclass
class Checkin:
    """
    签到记录实体
    
    Attributes:
        id: 数据库ID
        student_id: 学生学号
        student_name: 学生姓名（冗余存储，方便查询）
        class_name: 班级名称
        checkin_type: 签到类型
        checkin_date: 签到日期（YYYY-MM-DD）
        checkin_time: 签到时间
        score_delta: 签到获得/扣除的分数
        created_by: 创建者ID（老师代签时记录）
    """
    student_id: str
    student_name: str
    class_name: str
    checkin_type: CheckinType = CheckinType.SELF
    checkin_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    checkin_time: str = field(default_factory=lambda: datetime.now().strftime('%H:%M:%S'))
    score_delta: float = ScoreConfig.CHECKIN_SCORE_DELTA
    created_by: Optional[int] = None
    id: Optional[int] = None
    
    def is_same_day(self, date_str: str) -> bool:
        """检查是否是同一天签到"""
        return self.checkin_date == date_str
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'class_name': self.class_name,
            'checkin_type': self.checkin_type.value,
            'checkin_date': self.checkin_date,
            'checkin_time': self.checkin_time,
            'score_delta': self.score_delta,
            'created_by': self.created_by
        }
