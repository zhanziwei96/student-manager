"""
动态验证码生成工具单元测试
"""
from app.core.qr_signature import (
    generate_verification_code,
    verify_verification_code,
    _generate_code,
)


class TestVerificationCode:
    """动态验证码功能测试"""

    def test_generate_code(self):
        """测试验证码生成"""
        session_code = "CHECKIN_001"
        code = _generate_code(session_code, 1234567890)

        assert code is not None
        assert isinstance(code, str)
        assert len(code) == 6

    def test_generate_verification_code(self):
        """测试生成验证码字典"""
        session_code = "CHECKIN_002"
        payload = generate_verification_code(session_code)

        assert isinstance(payload, dict)
        assert "code" in payload
        assert "expires_in" in payload
        assert len(payload["code"]) == 6
        assert isinstance(payload["expires_in"], int)

    def test_verify_valid_code(self):
        """测试有效验证码验证"""
        session_code = "CHECKIN_001"
        code = generate_verification_code(session_code)["code"]

        result = verify_verification_code(session_code, code)
        assert result is True

    def test_verify_invalid_code(self):
        """测试伪造验证码被拒绝"""
        session_code = "CHECKIN_001"
        fake_code = "BAD000"

        result = verify_verification_code(session_code, fake_code)
        assert result is False

    def test_verify_code_case_insensitive(self):
        """测试验证码大小写不敏感"""
        session_code = "CHECKIN_001"
        code = generate_verification_code(session_code)["code"]

        result = verify_verification_code(session_code, code.lower())
        assert result is True
