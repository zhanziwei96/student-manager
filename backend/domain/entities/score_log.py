"""
分数变更日志实体 - 审计追踪
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ScoreLog:
    """
    分数变更日志
    
    Attributes:
        id: 日志ID
        student_id: 学生学号
        student_name: 学生姓名（冗余）
        class_name: 班级名称
        delta: 分数变动值（正为加分，负为扣分）
        reason: 变更原因
        operator_id: 操作人ID
        operator_name: 操作人姓名
        created_at: 操作时间
    """
    student_id: str
    student_name: str
    class_name: str
    delta: float
    reason: str
    operator_id: Optional[int] = None
    operator_name: str = "系统"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'class_name': self.class_name,
            'delta': self.delta,
            'reason': self.reason,
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'created_at': self.created_at
        }
