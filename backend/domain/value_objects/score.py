"""
分数值对象
不可变，有业务规则验证
"""
from dataclasses import dataclass
from infrastructure.config import ScoreConfig


@dataclass(frozen=True)
class Score:
    """分数值对象"""
    value: float
    
    def __post_init__(self):
        if self.value < ScoreConfig.MIN_SCORE:
            raise ValueError(f"分数不能为负数")
        if self.value > ScoreConfig.MAX_SCORE:
            raise ValueError(f"分数不能超过 {ScoreConfig.MAX_SCORE}")
    
    def add(self, delta: float) -> "Score":
        """增加分数，返回新的值对象"""
        return Score(min(ScoreConfig.MAX_SCORE, self.value + delta))
    
    def subtract(self, delta: float) -> "Score":
        """减少分数，返回新的值对象"""
        return Score(max(ScoreConfig.MIN_SCORE, self.value - delta))
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.2f}"
