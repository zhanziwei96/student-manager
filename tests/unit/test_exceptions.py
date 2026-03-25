"""
异常处理器单元测试
"""
import pytest
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)


class TestHttpExceptionHandler:
    """测试 HTTP 异常处理器"""
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """测试 HTTPException 处理"""
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": []
        })
        
        exc = HTTPException(status_code=404, detail="资源不存在")
        
        response = await http_exception_handler(request, exc)
        
        assert response.status_code == 404
        data = response.body.decode()
        assert '"success":false' in data.replace(' ', '')
        assert "资源不存在" in data
    
    @pytest.mark.asyncio
    async def test_http_exception_handler_401(self):
        """测试 401 未授权异常"""
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": []
        })
        
        exc = HTTPException(status_code=401, detail="请先登录")
        
        response = await http_exception_handler(request, exc)
        
        assert response.status_code == 401
        data = response.body.decode()
        assert '"success":false' in data.replace(' ', '')


class TestValidationExceptionHandler:
    """测试验证异常处理器"""
    
    @pytest.mark.asyncio
    async def test_validation_error_handler(self):
        """测试请求体验证错误处理"""
        request = Request(scope={
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "headers": []
        })
        
        errors = [
            {"loc": ["body", "username"], "msg": "字段必填", "type": "value_error.missing"}
        ]
        exc = RequestValidationError(errors=errors)
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == 422
        data = response.body.decode()
        assert '"success":false' in data.replace(' ', '')
        assert "username" in data
    
    @pytest.mark.asyncio
    async def test_validation_error_multiple_fields(self):
        """测试多字段验证错误"""
        request = Request(scope={
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "headers": []
        })
        
        errors = [
            {"loc": ["body", "username"], "msg": "字段必填", "type": "value_error.missing"},
            {"loc": ["body", "password"], "msg": "密码太短", "type": "value_error"}
        ]
        exc = RequestValidationError(errors=errors)
        
        response = await validation_exception_handler(request, exc)
        
        assert response.status_code == 422
        data = response.body.decode()
        assert "errors" in data


class TestGenericExceptionHandler:
    """测试通用异常处理器"""
    
    @pytest.mark.asyncio
    async def test_generic_exception_handler(self):
        """测试通用异常处理"""
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": []
        })
        
        exc = Exception("测试异常")
        
        response = await generic_exception_handler(request, exc)
        
        assert response.status_code == 500
        data = response.body.decode()
        assert '"success":false' in data.replace(' ', '')
        # 根据环境可能显示不同消息
        assert "message" in data
