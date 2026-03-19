"""
学生数据传输对象（DTO）
用于接口层和应用层之间的数据传输
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateStudentDTO:
    """创建学生DTO"""
    student_id: str
    name: str
    class_name: Optional[str] = None


@dataclass
class UpdateScoreDTO:
    """更新分数DTO"""
    student_id: str
    delta: float
    reason: str
    operator: str


@dataclass
class StudentResponseDTO:
    """学生响应DTO"""
    student_id: str
    name: str
    class_name: str
    score: float
