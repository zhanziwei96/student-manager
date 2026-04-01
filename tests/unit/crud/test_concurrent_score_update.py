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

    def test_concurrent_update_raises_409(self, session, test_student):
        """
        测试并发更新冲突时抛出 409 错误

        模拟真实并发场景：
        1. 会话 A 获取学生（version=1）
        2. 会话 B 并发更新同一学生（version 变为 2）
        3. 会话 A 尝试更新（基于旧的 version=1）
        4. 应该抛出 409 冲突错误
        """
        from fastapi import HTTPException
        engine = session.get_bind()

        # 第一步：在会话 A 中获取学生并计算新分数
        # 但先不提交，模拟用户正在编辑的状态
        student_id = test_student.student_id
        initial_version = test_student.version
        assert initial_version == 1

        # 第二步：在另一个会话中更新同一学生（模拟并发）
        with Session(engine) as session_b:
            # 使用 update_student_score 正确更新
            result_b = update_student_score(
                session=session_b,
                student_id=student_id,
                delta=5.0,
                reason="并发更新",
                operator="teacher_b"
            )
            # 验证会话B更新成功
            assert result_b.version == 2
            assert result_b.score == 85.0  # 80 + 5

        # 第三步：在原始会话中尝试更新（基于旧的 version）
        # 这会失败，因为 version 已经从 1 变为 2
        with pytest.raises(HTTPException) as exc_info:
            update_student_score(
                session=session,
                student_id=student_id,
                delta=10.0,
                reason="应该失败的更新",
                operator="teacher_a"
            )

        # 验证错误信息
        assert exc_info.value.status_code == 409
        assert "已被其他用户修改" in exc_info.value.detail

        # 第四步：验证数据未被会话A的更新覆盖
        session_c = Session(engine)
        final_student = session_c.get(Student, student_id)
        assert final_student.version == 2  # 版本号应该是2（来自会话B的更新）
        assert final_student.score == 85.0  # 分数应该是85（来自会话B的更新），不是90
