"""
学生签到领域事件
"""
from dataclasses import dataclass
from datetime import datetime
from domain.value_objects.student_id import StudentId


@dataclass
class StudentCheckedInEvent:
    """学生签到事件"""
    student_id: StudentId
    student_name: str
    class_name: str
    timestamp: datetime
