"""
学生分数边界值测试
REVIEW-P1: 补充分数边界值测试场景

测试场景:
- 负数分数变动
- 超大值分数变动  
- 分数上限/下限边界
- 零值变动
"""
import pytest
from sqlmodel import Session
from app.crud import create_student, update_student_score
from app.models import Student
from app.core.config import get_settings


class TestStudentScoreBoundary:
    """测试学生分数边界值处理"""
    
    def test_score_negative_delta(self, session: Session):
        """测试负数分数变动（扣分）"""
        student = create_student(session, "SB001", "张三", "软件1班", score=80.0)
        
        updated = update_student_score(
            session, "SB001", delta=-10.0, reason="迟到", operator="老师"
        )
        
        assert updated is not None
        assert updated.score == 70.0
    
    def test_score_negative_delta_exceed_min(self, session: Session):
        """测试负分数变动超过下限（应截断到最小值）"""
        settings = get_settings()
        min_score = settings.score.min_score
        
        # 创建分数为最小值 + 10 的学生
        student = create_student(session, "SB002", "张三", "软件1班", score=min_score + 10)
        
        # 尝试减去 50 分（超过下限）
        updated = update_student_score(
            session, "SB002", delta=-50.0, reason="严重违纪", operator="老师"
        )
        
        # 分数应被截断到最小值
        assert updated is not None
        assert updated.score == min_score
    
    def test_score_large_positive_delta(self, session: Session):
        """测试超大正分数变动（应截断到最大值）"""
        settings = get_settings()
        max_score = settings.score.max_score
        
        student = create_student(session, "SB003", "张三", "软件1班", score=80.0)
        
        # 尝试增加超大分数
        updated = update_student_score(
            session, "SB003", delta=999999.0, reason="特殊奖励", operator="老师"
        )
        
        # 分数应被截断到最大值
        assert updated is not None
        assert updated.score == max_score
    
    def test_score_large_negative_delta(self, session: Session):
        """测试超大负分数变动（应截断到最小值）"""
        settings = get_settings()
        min_score = settings.score.min_score
        
        student = create_student(session, "SB004", "张三", "软件1班", score=80.0)
        
        # 尝试减去超大分数
        updated = update_student_score(
            session, "SB004", delta=-999999.0, reason="严重违规", operator="老师"
        )
        
        # 分数应被截断到最小值
        assert updated is not None
        assert updated.score == min_score
    
    def test_score_zero_delta(self, session: Session):
        """测试零值分数变动"""
        student = create_student(session, "SB005", "张三", "软件1班", score=80.0)
        
        updated = update_student_score(
            session, "SB005", delta=0.0, reason="无变动", operator="老师"
        )
        
        assert updated is not None
        assert updated.score == 80.0  # 分数不变
    
    def test_score_boundary_max_limit(self, session: Session):
        """测试分数上限边界"""
        settings = get_settings()
        max_score = settings.score.max_score
        
        # 创建分数接近上限的学生
        student = create_student(session, "SB006", "张三", "软件1班", score=max_score - 5)
        
        # 增加 10 分（超过上限）
        updated = update_student_score(
            session, "SB006", delta=10.0, reason="加分", operator="老师"
        )
        
        # 分数应被截断到上限
        assert updated is not None
        assert updated.score == max_score
    
    def test_score_boundary_min_limit(self, session: Session):
        """测试分数下限边界"""
        settings = get_settings()
        min_score = settings.score.min_score
        
        # 创建分数接近下限的学生
        student = create_student(session, "SB007", "张三", "软件1班", score=min_score + 5)
        
        # 减去 10 分（低于下限）
        updated = update_student_score(
            session, "SB007", delta=-10.0, reason="扣分", operator="老师"
        )
        
        # 分数应被截断到下限
        assert updated is not None
        assert updated.score == min_score
    
    def test_score_float_precision(self, session: Session):
        """测试浮点数精度处理"""
        student = create_student(session, "SB008", "张三", "软件1班", score=80.5)
        
        updated = update_student_score(
            session, "SB008", delta=0.33, reason="精确加分", operator="老师"
        )
        
        assert updated is not None
        # 允许浮点数精度误差
        assert abs(updated.score - 80.83) < 0.01
    
    def test_score_at_maximum_no_change(self, session: Session):
        """测试分数已达上限时的变动"""
        settings = get_settings()
        max_score = settings.score.max_score
        
        # 创建分数已达上限的学生
        student = create_student(session, "SB009", "张三", "软件1班", score=max_score)
        
        # 尝试加分
        updated = update_student_score(
            session, "SB009", delta=10.0, reason="加分", operator="老师"
        )
        
        # 分数应保持在上限
        assert updated is not None
        assert updated.score == max_score
    
    def test_score_at_minimum_no_change(self, session: Session):
        """测试分数已达下限时的变动"""
        settings = get_settings()
        min_score = settings.score.min_score
        
        # 创建分数已达下限的学生
        student = create_student(session, "SB010", "张三", "软件1班", score=min_score)
        
        # 尝试减分
        updated = update_student_score(
            session, "SB010", delta=-10.0, reason="扣分", operator="老师"
        )
        
        # 分数应保持在下限
        assert updated is not None
        assert updated.score == min_score
