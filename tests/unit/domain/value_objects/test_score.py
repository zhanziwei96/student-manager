"""
分数值对象测试
不需要数据库，不需要mock，纯单元测试
"""
import pytest
from domain.value_objects.score import Score
from infrastructure.config import ScoreConfig


class TestScore:
    """分数值对象测试类"""
    
    # ========== 构造测试 ==========
    
    def test_create_valid_score(self):
        """创建有效分数"""
        score = Score(85.5)
        assert score.value == 85.5
    
    def test_create_zero_score(self):
        """创建0分"""
        score = Score(0)
        assert score.value == 0
    
    def test_create_max_score(self):
        """创建满分"""
        score = Score(100)
        assert score.value == 100
    
    def test_score_cannot_be_negative(self):
        """分数不能为负数"""
        with pytest.raises(ValueError, match="分数不能为负数"):
            Score(-1)
    
    def test_score_cannot_exceed_max(self):
        """分数不能超过最大值"""
        with pytest.raises(ValueError, match="分数不能超过"):
            Score(101)
    
    # ========== 加法测试 ==========
    
    def test_add_score(self):
        """正常加分"""
        score = Score(80)
        new_score = score.add(10)
        
        assert float(new_score) == 90
        assert float(score) == 80  # 原值不变（不可变）
    
    def test_add_score_capped_at_max(self):
        """加分上限截断"""
        score = Score(98)
        new_score = score.add(5)
        
        assert float(new_score) == 100  # 被截断到100
    
    def test_add_zero(self):
        """加0分"""
        score = Score(80)
        new_score = score.add(0)
        
        assert float(new_score) == 80
    
    # ========== 减法测试 ==========
    
    def test_subtract_score(self):
        """正常扣分"""
        score = Score(80)
        new_score = score.subtract(10)
        
        assert float(new_score) == 70
    
    def test_subtract_score_capped_at_min(self):
        """扣分下限截断"""
        score = Score(5)
        new_score = score.subtract(10)
        
        assert float(new_score) == 0  # 被截断到0
    
    # ========== 边界测试 ==========
    
    def test_boundary_min(self):
        """最小值边界"""
        score = Score(0)
        new_score = score.subtract(1)
        assert float(new_score) == 0
    
    def test_boundary_max(self):
        """最大值边界"""
        score = Score(100)
        new_score = score.add(1)
        assert float(new_score) == 100
    
    # ========== 浮点数精度测试 ==========
    
    def test_float_precision(self):
        """浮点数精度处理"""
        score = Score(70.5)
        new_score = score.add(0.5)
        
        assert float(new_score) == 71.0
    
    # ========== 字符串表示测试 ==========
    
    def test_str_representation(self):
        """字符串表示"""
        score = Score(85.5)
        assert str(score) == "85.50"
    
    def test_float_conversion(self):
        """转float"""
        score = Score(85.5)
        assert float(score) == 85.5
