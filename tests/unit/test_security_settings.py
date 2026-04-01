"""
测试安全配置校验 - SEC-004: JWT密钥强度校验
"""
import os
import pytest
from pydantic import ValidationError


class TestSecuritySettings:
    """测试安全配置校验"""

    def test_production_with_default_key_raises_error(self, monkeypatch):
        """生产环境使用默认密钥应报错"""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "dev-secret-key-change-in-production")

        from app.core.config import SecuritySettings

        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings()

        assert "必须使用自定义密钥" in str(exc_info.value)

    def test_production_with_short_key_raises_error(self, monkeypatch):
        """生产环境使用短密钥应报错"""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "short-key")

        from app.core.config import SecuritySettings

        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings()

        assert "长度必须至少32字符" in str(exc_info.value)

    def test_production_with_strong_key_succeeds(self, monkeypatch):
        """生产环境使用强密钥应通过"""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 32 + "-very-strong-secret-key-2024")

        from app.core.config import SecuritySettings

        settings = SecuritySettings()
        assert settings.secret_key == "a" * 32 + "-very-strong-secret-key-2024"

    def test_development_with_default_key_succeeds(self, monkeypatch):
        """开发环境使用默认密钥应通过"""
        monkeypatch.setenv("ENV", "development")

        from app.core.config import SecuritySettings

        settings = SecuritySettings()
        assert settings.secret_key == "dev-secret-key-change-in-production"

    def test_testing_with_default_key_succeeds(self, monkeypatch):
        """测试环境使用默认密钥应通过"""
        monkeypatch.setenv("ENV", "testing")

        from app.core.config import SecuritySettings

        settings = SecuritySettings()
        assert settings.secret_key == "dev-secret-key-change-in-production"

    def test_production_32_char_key_boundary(self, monkeypatch):
        """测试32字符边界值"""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 32)

        from app.core.config import SecuritySettings

        # 正好32字符应该通过
        settings = SecuritySettings()
        assert len(settings.secret_key) == 32

    def test_production_31_char_key_fails(self, monkeypatch):
        """31字符密钥应该失败"""
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 31)

        from app.core.config import SecuritySettings

        with pytest.raises(ValidationError) as exc_info:
            SecuritySettings()

        assert "长度必须至少32字符" in str(exc_info.value)
