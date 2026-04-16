"""
二维码签名工具单元测试
"""
import time
import pytest
from unittest.mock import patch

from app.core.qr_signature import (
    generate_qr_signature,
    verify_qr_signature,
    generate_qr_payload,
)


class TestQRSignature:
    """二维码签名功能测试"""

    def test_generate_signature(self):
        """测试签名生成"""
        session_code = "CHECKIN_001"
        timestamp = 1234567890
        signature = generate_qr_signature(session_code, timestamp)

        assert signature is not None
        assert isinstance(signature, str)
        assert len(signature) > 0

    def test_verify_valid_signature(self):
        """测试有效签名验证"""
        session_code = "CHECKIN_001"
        timestamp = int(time.time())
        signature = generate_qr_signature(session_code, timestamp)

        result = verify_qr_signature(session_code, timestamp, signature)
        assert result is True

    def test_verify_expired_signature(self):
        """测试过期签名（15秒前）被拒绝"""
        session_code = "CHECKIN_001"
        timestamp = int(time.time()) - 15
        signature = generate_qr_signature(session_code, timestamp)

        result = verify_qr_signature(session_code, timestamp, signature)
        assert result is False

    def test_verify_invalid_signature(self):
        """测试伪造签名被拒绝"""
        session_code = "CHECKIN_001"
        timestamp = int(time.time())
        fake_signature = "a" * 64

        result = verify_qr_signature(session_code, timestamp, fake_signature)
        assert result is False

    def test_generate_qr_payload(self):
        """测试生成完整二维码内容字典"""
        session_code = "CHECKIN_002"
        payload = generate_qr_payload(session_code)

        assert isinstance(payload, dict)
        assert payload["session_code"] == session_code
        assert "timestamp" in payload
        assert "signature" in payload
        assert isinstance(payload["timestamp"], int)
        assert isinstance(payload["signature"], str)
