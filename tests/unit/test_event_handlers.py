"""
事件处理器测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from app.events.handlers import handle_score_updated
from app.core.events import ScoreUpdated


class TestHandleScoreUpdated:
    """测试分数更新事件处理器"""

    def test_handle_score_updated_creates_score_log(self):
        """测试处理器创建 ScoreLog 记录"""
        # 创建事件
        event = ScoreUpdated(
            student_id=1,
            old_score=100,
            new_score=110,
            delta=10,
            reason="测试加分",
            operator="teacher_001",
            occurred_at=datetime.now()
        )
        
        # Mock session 和 engine
        mock_session = MagicMock()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__ = Mock(return_value=mock_session)
        mock_context_manager.__exit__ = Mock(return_value=False)
        
        with patch("app.events.handlers.Session", return_value=mock_context_manager):
            with patch("app.core.db.engine"):
                # 执行处理器
                handle_score_updated(event)
                
                # 验证 ScoreLog 被添加
                assert mock_session.add.called
                added_log = mock_session.add.call_args[0][0]
                assert added_log.student_id == 1
                assert added_log.old_score == 100
                assert added_log.new_score == 110
                assert added_log.delta == 10
                assert added_log.reason == "测试加分"
                assert added_log.operator == "teacher_001"
                
                # 验证提交
                mock_session.commit.assert_called_once()
