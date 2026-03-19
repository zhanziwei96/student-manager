"""
分数变更领域事件
"""
from dataclasses import dataclass
from datetime import datetime
from domain.value_objects.student_id import StudentId


@dataclass
class ScoreChangedEvent:
    """分数变更事件"""
    student_id: StudentId
    student_name: str
    old_score: float
    new_score: float
    delta: float
    reason: str
    operator: str
    timestamp: datetime
