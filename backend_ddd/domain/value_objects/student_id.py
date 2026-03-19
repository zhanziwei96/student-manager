"""
学号值对象
不可变，通过值判断相等
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class StudentId:
    """学生ID/学号值对象"""
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 5:
            raise ValueError("学号不能为空且至少5位")
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, StudentId):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        return hash(self.value)
