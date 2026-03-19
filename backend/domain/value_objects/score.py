"""
分数值对象
不可变，有业务规则验证
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Score:
    """分数值对象 - 范围 0-100"""
    value: float
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("分数不能为负数")
        if self.value > 100:
            raise ValueError("分数不能超过100")
    
    def add(self, delta: float) -> "Score":
        """增加分数，返回新的值对象"""
        return Score(min(100, self.value + delta))
    
    def subtract(self, delta: float) -> "Score":
        """减少分数，返回新的值对象"""
        return Score(max(0, self.value - delta))
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.2f}"
