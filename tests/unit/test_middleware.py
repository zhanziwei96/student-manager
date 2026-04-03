"""
审计日志中间件单元测试
"""
import pytest
from unittest.mock import Mock, MagicMock
from fastapi import Request
from app.core.middleware import AuditLogMiddleware


class TestAuditLogMiddleware:
    """测试审计日志中间件"""
    
    def test_should_audit_match_post_login(self):
        """测试匹配 POST /api/login"""
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/login"
        
        assert middleware._should_audit(mock_request) is True
    
    def test_should_audit_match_put_score(self):
        """测试匹配 PUT /api/students/123/score"""
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "PUT"
        mock_request.url.path = "/api/v1/students/123/score"
        
        assert middleware._should_audit(mock_request) is True
    
    def test_should_audit_match_delete_student(self):
        """测试匹配 DELETE /api/students/123"""
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "DELETE"
        mock_request.url.path = "/api/v1/students/123"
        
        assert middleware._should_audit(mock_request) is True
    
    def test_should_audit_not_match_health(self):
        """测试不匹配 /api/health"""
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v1/health"
        
        assert middleware._should_audit(mock_request) is False
    
    def test_should_audit_not_match_docs(self):
        """测试不匹配 /docs"""
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/docs"
        
        assert middleware._should_audit(mock_request) is False
    
    def test_should_audit_not_match_get_students(self):
        """测试不匹配 GET /api/students"""
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v1/students"
        
        assert middleware._should_audit(mock_request) is False
    
    def test_get_action_name_post(self):
        """测试获取 POST 操作名称"""
        middleware = AuditLogMiddleware(Mock())
        
        assert middleware._get_action_name("POST", "/api/v1/students") == "创建"
        assert middleware._get_action_name("POST", "/api/v1/login") == "登录"
    
    def test_get_action_name_put(self):
        """测试获取 PUT 操作名称"""
        middleware = AuditLogMiddleware(Mock())
        
        assert middleware._get_action_name("PUT", "/api/v1/students/123") == "更新"
        assert middleware._get_action_name("PUT", "/api/v1/students/123/score") == "修改分数"
        assert middleware._get_action_name("PUT", "/api/v1/students/123/reset-password") == "重置密码"
    
    def test_get_action_name_delete(self):
        """测试获取 DELETE 操作名称"""
        middleware = AuditLogMiddleware(Mock())
        
        assert middleware._get_action_name("DELETE", "/api/v1/students/123") == "删除"
    
    def test_get_resource_name_students(self):
        """测试获取学生资源名称"""
        middleware = AuditLogMiddleware(Mock())
        
        assert middleware._get_resource_name("/api/v1/students") == "学生"
        assert middleware._get_resource_name("/api/v1/students/123") == "学生"
        assert middleware._get_resource_name("/api/v1/students/123/score") == "学生"
    
    def test_get_resource_name_users(self):
        """测试获取用户资源名称"""
        middleware = AuditLogMiddleware(Mock())

        assert middleware._get_resource_name("/api/v1/users") == "用户"
        assert middleware._get_resource_name("/api/v1/users/123") == "用户"
    
    def test_get_resource_name_login(self):
        """测试获取登录资源名称"""
        middleware = AuditLogMiddleware(Mock())
        
        assert middleware._get_resource_name("/api/v1/login") == "系统"
    
    def test_extract_resource_id_with_id(self):
        """测试从路径中提取数字 ID"""
        middleware = AuditLogMiddleware(Mock())

        assert middleware._extract_resource_id("/api/v1/students/123") == "123"
        assert middleware._extract_resource_id("/api/v1/students/456/score") == "456"
        assert middleware._extract_resource_id("/api/v1/users/789") == "789"
    
    def test_extract_resource_id_no_id(self):
        """测试从路径中提取不到 ID"""
        middleware = AuditLogMiddleware(Mock())
        
        assert middleware._extract_resource_id("/api/v1/students") is None
        assert middleware._extract_resource_id("/api/v1/login") is None
    
    def test_extract_resource_id_non_numeric(self):
        """测试非数字 ID"""
        middleware = AuditLogMiddleware(Mock())
        
        # 非数字 ID 应该返回 None
        assert middleware._extract_resource_id("/api/v1/students/abc") is None


class TestAuditLogMiddlewareIntegration:
    """测试审计日志中间件集成"""
    
    @pytest.mark.asyncio
    async def test_dispatch_skips_non_audit_routes(self):
        """测试跳过非审计路由"""
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/v1/health"
        mock_request.client = Mock(host="127.0.0.1")
        mock_request.headers = {}
        
        mock_response = Mock()
        
        # 使用 async 函数
        async def mock_call_next(request):
            return mock_response
        
        response = await middleware.dispatch(mock_request, mock_call_next)
        
        assert response == mock_response


class TestAuditLogAsyncSave:
    """测试审计日志异步保存（性能优化）"""
    
    @pytest.mark.asyncio
    async def test_save_audit_log_creates_async_task(self):
        """测试保存审计日志创建异步任务 - 性能优化验证"""
        import asyncio
        from unittest.mock import patch
        from app.core.middleware import _save_audit_log_async
        
        middleware = AuditLogMiddleware(Mock())
        
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/login"
        mock_request.client = Mock(host="127.0.0.1")
        mock_request.headers = {}
        mock_request.state = Mock()
        mock_request.state.user = None
        
        mock_response = Mock()
        mock_response.status_code = 200
        
        audit_data = {
            "user_id": "1",
            "user_name": "admin",
            "role": "admin",
            "method": "POST",
            "path": "/api/v1/login",
            "ip_address": "127.0.0.1",
            "user_agent": None,
        }
        
        # 验证创建后台任务，不阻塞响应
        with patch("app.core.middleware.asyncio.create_task") as mock_create_task:
            await middleware._save_audit_log(mock_request, audit_data, mock_response)
            
            # 验证 create_task 被调用（异步写入）
            mock_create_task.assert_called_once()
            
            # 验证传入的是异步函数
            call_args = mock_create_task.call_args[0][0]
            import inspect
            assert inspect.iscoroutine(call_args)

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
