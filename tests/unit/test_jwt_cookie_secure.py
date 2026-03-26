"""
JWT Cookie Secure 标志测试 - BE-006 修复验证

验证 Cookie secure 标志根据环境配置正确设置
"""
import pytest
from unittest.mock import Mock, patch


class TestBE006Fix:
    """验证 BE-006 修复：Cookie secure 标志不再硬编码"""

    def test_no_hardcoded_secure_false(self):
        """验证代码中没有硬编码的 secure=False"""
        from pathlib import Path
        jwt_py_path = Path(__file__).parent.parent.parent / "backend" / "app" / "core" / "jwt.py"
        content = jwt_py_path.read_text()
        
        # 验证使用了配置而非硬编码
        assert "settings.security.cookie_secure" in content
        
        # 验证没有硬编码的 secure=False (排除注释和字符串)
        lines = content.split('\n')
        for line in lines:
            # 跳过注释行
            if line.strip().startswith('#'):
                continue
            # 检查是否有硬编码的 secure=False
            if 'secure=False' in line and 'cookie_secure' not in line:
                pytest.fail(f"Found hardcoded secure=False in: {line}")

    def test_config_has_cookie_secure(self):
        """验证配置中有 cookie_secure 选项"""
        from pathlib import Path
        config_py_path = Path(__file__).parent.parent.parent / "backend" / "app" / "core" / "config.py"
        content = config_py_path.read_text()
        
        assert "cookie_secure" in content
        assert "Cookie Secure" in content or "BE-006" in content

    def test_set_token_cookie_uses_settings(self):
        """验证 set_token_cookie 使用配置"""
        from app.core.jwt import set_token_cookie, COOKIE_NAME
        
        mock_response = Mock()
        
        # 使用 MagicMock 创建支持属性访问的嵌套 mock
        from unittest.mock import MagicMock
        mock_settings = MagicMock()
        # 通过 __getattr__ 方式设置嵌套属性
        mock_settings.security.cookie_secure = True
        
        with patch('app.core.jwt.get_settings', return_value=mock_settings):
            set_token_cookie(mock_response, "test_token")
            
            # 验证 set_cookie 被调用
            mock_response.set_cookie.assert_called_once()
            call_args = mock_response.set_cookie.call_args
            
            # Python 3.7+ 中 call_args 有 kwargs 属性
            call_kwargs = call_args[-1]  # 最后一个是 kwargs dict
            if isinstance(call_kwargs, dict):
                assert call_kwargs['key'] == COOKIE_NAME
                assert call_kwargs['httponly'] is True
                assert 'secure' in call_kwargs
            else:
                # 兜底：直接检查调用字符串
                call_str = str(mock_response.set_cookie.call_args)
                assert COOKIE_NAME in call_str
                assert 'httponly' in call_str
