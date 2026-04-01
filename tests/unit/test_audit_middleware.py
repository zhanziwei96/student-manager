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
            "path": "/api/students",
        }

        # Mock Session 和 engine
        with patch('app.core.middleware.Session') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__ = Mock(return_value=mock_session)
            mock_session_class.return_value.__exit__ = Mock(return_value=False)

            with patch('app.core.middleware.AuditLog') as mock_audit_log:
                _save_audit_log_sync(audit_data)

                # 验证创建了 AuditLog 记录
                mock_audit_log.assert_called_once_with(**audit_data)
                # 验证提交了事务
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_done_callback_captures_exception(self):
        """测试任务完成回调捕获异常"""
        from app.core.middleware import _save_audit_log_async

        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # 创建一个会失败的任务
            async def failing_task():
                raise ValueError("测试错误")

            task = asyncio.create_task(failing_task())

            # 添加回调
            def _on_task_done(t: asyncio.Task) -> None:
                try:
                    t.result()
                except Exception as e:
                    mock_logger.error(f"任务执行失败: {e}")

            task.add_done_callback(_on_task_done)

            # 等待任务完成
            await asyncio.sleep(0.1)

            # 验证异常被捕获并记录
            mock_logger.error.assert_called_once()
            assert "测试错误" in mock_logger.error.call_args[0][0]


class TestAuditMiddlewareIntegration:
    """审计日志中间件集成测试"""

    def test_should_audit_excluded_paths(self):
        """测试排除路径不记录审计"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        # 创建模拟请求
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/health"

        assert middleware._should_audit(mock_request) is False

    def test_should_audit_audit_routes(self):
        """测试审计路由匹配"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        # 测试登录路径
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/login"

        assert middleware._should_audit(mock_request) is True

    def test_should_audit_with_path_params(self):
        """测试带路径参数的路由匹配"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        # 测试带ID的路径
        mock_request = Mock()
        mock_request.method = "PUT"
        mock_request.url.path = "/api/students/123/score"

        assert middleware._should_audit(mock_request) is True

    def test_get_action_name(self):
        """测试获取操作名称"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        assert middleware._get_action_name("POST", "/api/login") == "登录"
        assert middleware._get_action_name("POST", "/api/students") == "创建"
        assert middleware._get_action_name("PUT", "/api/students/123/score") == "修改分数"
        assert middleware._get_action_name("PUT", "/api/students/123/reset-password") == "重置密码"
        assert middleware._get_action_name("DELETE", "/api/students/123") == "删除"

    def test_extract_resource_id(self):
        """测试提取资源ID"""
        from app.core.middleware import AuditLogMiddleware

        middleware = AuditLogMiddleware(Mock())

        assert middleware._extract_resource_id("/api/students/123") == "123"
        assert middleware._extract_resource_id("/api/students/123/score") == "123"
        assert middleware._extract_resource_id("/api/students") is None
        assert middleware._extract_resource_id("/api/login") is None
