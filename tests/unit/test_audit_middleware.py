"""
测试审计日志中间件 - SEC-006: 任务队列管理
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request
from starlette.datastructures import Headers


class TestAuditMiddleware:
    """测试审计日志中间件"""

    def test_semaphore_limits_concurrent_tasks(self):
        """测试信号量限制并发任务数"""
        from app.core.middleware import MAX_CONCURRENT_AUDIT_TASKS, _audit_task_semaphore

        # 验证信号量初始值
        assert _audit_task_semaphore._value == MAX_CONCURRENT_AUDIT_TASKS
        assert MAX_CONCURRENT_AUDIT_TASKS == 50

    @pytest.mark.asyncio
    async def test_save_audit_log_async_with_timeout(self):
        """测试审计日志写入超时处理"""
        from app.core.middleware import _save_audit_log_async

        audit_data = {
            "action": "test",
            "resource": "student",
            "user_id": 1,
        }

        # Mock run_in_executor 使其超时
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_future = asyncio.Future()
            mock_future.set_exception(asyncio.TimeoutError())
            mock_loop.return_value.run_in_executor = Mock(return_value=mock_future)

            # 不应该抛出异常
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                await _save_audit_log_async(audit_data)

                # 验证记录了超时警告
                mock_logger.warning.assert_called_once()
                assert "超时" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_save_audit_log_async_exception_handling(self):
        """测试审计日志异常处理"""
        from app.core.middleware import _save_audit_log_async

        audit_data = {"action": "test"}

        # Mock run_in_executor 使其抛出异常
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_future = asyncio.Future()
            mock_future.set_exception(Exception("数据库错误"))
            mock_loop.return_value.run_in_executor = Mock(return_value=mock_future)

            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                # 不应该抛出异常
                await _save_audit_log_async(audit_data)

                # 验证记录了错误
                mock_logger.error.assert_called_once()
                assert "失败" in mock_logger.error.call_args[0][0]

    def test_save_audit_log_sync(self):
        """测试同步保存审计日志"""
        from app.core.middleware import _save_audit_log_sync

        audit_data = {
            "action": "创建",
            "resource": "学生",
            "user_id": 1,
            "method": "POST",
            "path": "/api/v1/students",
        }

        # Mock Session 和 AuditLog - 这些是在函数内部导入的
        with patch('app.core.db.engine'):
            with patch('sqlmodel.Session') as mock_session_class:
                mock_session = MagicMock()
                mock_session_class.return_value.__enter__ = Mock(return_value=mock_session)
                mock_session_class.return_value.__exit__ = Mock(return_value=False)

                with patch('app.models.AuditLog') as mock_audit_log:
                    _save_audit_log_sync(audit_data)

                    # 验证创建了 AuditLog 记录
                    mock_audit_log.assert_called_once_with(**audit_data)
                    # 验证提交了事务
                    mock_session.commit.assert_called_once()


class TestAuditMiddlewareIntegration:
    """测试审计日志中间件集成"""

    @pytest.mark.asyncio
    async def test_should_audit_audit_routes(self):
        """测试应该审计的路由 - 使用实际中间件实例"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        # 创建模拟请求
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/login"

        # 验证应该审计
        assert middleware._should_audit(mock_request) is True

    @pytest.mark.asyncio
    async def test_should_audit_with_path_params(self):
        """测试带路径参数的路由也应该审计"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        mock_request = Mock()
        mock_request.method = "PUT"
        mock_request.url.path = "/api/v1/students/123/score"

        assert middleware._should_audit(mock_request) is True

    @pytest.mark.asyncio
    async def test_should_not_audit_health_check(self):
        """测试健康检查不应该审计"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v1/health"

        assert middleware._should_audit(mock_request) is False

    @pytest.mark.asyncio
    async def test_should_not_audit_docs(self):
        """测试API文档不应该审计"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/docs"

        assert middleware._should_audit(mock_request) is False


class TestAuditLogAsyncSave:
    """测试审计日志异步保存（性能优化）"""

    @pytest.mark.asyncio
    async def test_async_save_handles_exception_silently(self):
        """测试异步保存异常被静默处理 - 不影响主业务"""
        from app.core.middleware import _save_audit_log_async

        # 传入无效数据，应该捕获异常不抛出
        audit_data = {
            "invalid_field": "test",  # 无效字段
        }

        # 不应抛出异常
        await _save_audit_log_async(audit_data)

        # 断言通过即表示异常被正确捕获
        assert True
