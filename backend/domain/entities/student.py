"""
学生实体
有唯一标识（学号），有生命周期
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from domain.value_objects.student_id import StudentId
from domain.value_objects.score import Score
from domain.events.score_changed import ScoreChangedEvent
from domain.events.student_checked_in import StudentCheckedInEvent


@dataclass
class Student:
    """学生实体"""
    student_id: StudentId
    name: str
    class_name: str
    score: Score
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None  # 数据库技术ID
    
    # 领域事件列表
    _events: List = field(default_factory=list, repr=False)
    
    @property
    def events(self) -> List:
        """获取领域事件"""
        return self._events
    
    def clear_events(self) -> None:
        """清空领域事件"""
        self._events.clear()
    
    def change_score(self, delta: float, reason: str, operator: str) -> None:
        """
        修改分数 - 领域逻辑
        
        Args:
            delta: 分数变化值（可为负）
            reason: 变更原因
            operator: 操作人
        """
        old_score = self.score
        
        if delta > 0:
            self.score = self.score.add(delta)
        else:
            self.score = self.score.subtract(abs(delta))
        
        # 记录领域事件
        self._events.append(ScoreChangedEvent(
            student_id=self.student_id,
            student_name=self.name,
            old_score=float(old_score),
            new_score=float(self.score),
            delta=delta,
            reason=reason,
            operator=operator,
            timestamp=datetime.now()
        ))
    
    def checkin(self) -> None:
        """签到 - 领域逻辑"""
        self._events.append(StudentCheckedInEvent(
            student_id=self.student_id,
            student_name=self.name,
            class_name=self.class_name,
            timestamp=datetime.now()
        ))
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'student_id': str(self.student_id),
            'name': self.name,
            'class_name': self.class_name,
            'score': float(self.score),
            'created_at': self.created_at.isoformat()
        }
