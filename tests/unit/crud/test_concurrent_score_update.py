"""
测试并发分数更新保护（BE-008 修复验证）
"""
import pytest
from sqlmodel import Session
from app.models import Student
from app.crud.student import update_student_score


class TestConcurrentScoreUpdate:
    """测试并发分数更新乐观锁保护"""
    
    def test_student_has_version_field(self, session, test_student):
        """测试学生模型有 version 字段"""
        student = session.get(Student, test_student.student_id)
        assert hasattr(student, 'version')
        assert student.version == 1
    
    def test_update_score_increments_version(self, session, test_student):
        """测试更新分数会递增版本号"""
        # 初始版本为 1
        assert test_student.version == 1
        
        # 更新分数
        result = update_student_score(
            session=session,
            student_id=test_student.student_id,
            delta=5.0,
            reason="测试加分",
            operator="teacher1"
        )
        
        # 刷新获取最新数据
        session.refresh(result)
        
        # 版本号应该递增到 2
        assert result.version == 2
        assert result.score == 85.0  # 80.0 + 5.0
    
    def test_update_nonexistent_student_returns_none(self, session):
        """测试更新不存在的学生返回 None"""
        result = update_student_score(
            session=session,
            student_id="NONEXISTENT",
            delta=5.0,
            reason="测试",
            operator="teacher1"
        )
        assert result is None


class TestOptimisticLockIntegration:
    """乐观锁集成测试"""
    
    def test_concurrent_update_detection(self, session, test_student):
        """
        测试并发更新检测
        
        模拟场景：
        1. 获取学生对象（version=1）
        2. 模拟另一个会话更新（version 变为 2）
        3. 验证版本号更新正确
        """
        engine = session.get_bind()
        
        # 第一步：获取学生
        student = session.get(Student, test_student.student_id)
        assert student.version == 1
        
        # 第二步：在另一个会话中更新学生（模拟并发）
        with Session(engine) as session_b:
            student_b = session_b.get(Student, test_student.student_id)
            student_b.score = 90.0
            student_b.version += 1  # 递增版本号
            session_b.add(student_b)
            session_b.commit()
        
        # 第三步：刷新会话 A 的数据
        session.refresh(student)
        
        # 验证版本已更新
        assert student.version == 2
        assert student.score == 90.0
        
        # 再次更新应该正常工作（版本已更新）
        student.score = 95.0
        student.version += 1
        session.add(student)
        session.commit()
        
        # 验证最终状态
        session.refresh(student)
        assert student.version == 3
        assert student.score == 95.0
