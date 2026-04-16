"""
二维码签名工具模块
使用 HMAC-SHA256 对二维码内容进行签名和验证
"""
import hmac
import hashlib
import time

from app.core.config import get_settings


QR_VALIDITY_SECONDS = 10


def generate_qr_signature(session_code: str, timestamp: int) -> str:
    """生成二维码签名

    Args:
        session_code: 签到会话代码
        timestamp: 时间戳（秒）

    Returns:
        str: HMAC-SHA256 十六进制签名
    """
    message = f"{session_code}|{timestamp}"
    secret_key = get_settings().security.secret_key.encode("utf-8")
    signature = hmac.new(secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()
    return signature


def verify_qr_signature(session_code: str, timestamp: int, signature: str) -> bool:
    """验证二维码签名和时效性

    Args:
        session_code: 签到会话代码
        timestamp: 时间戳（秒）
        signature: 待验证的签名

    Returns:
        bool: 签名有效且未过期返回 True，否则返回 False
    """
    expected = generate_qr_signature(session_code, timestamp)
    if not hmac.compare_digest(expected, signature):
        return False
    if int(time.time()) - timestamp > QR_VALIDITY_SECONDS:
        return False
    return True


def generate_qr_payload(session_code: str) -> dict:
    """生成完整二维码内容字典

    Args:
        session_code: 签到会话代码

    Returns:
        dict: 包含 session_code、timestamp、signature 的字典
    """
    timestamp = int(time.time())
    signature = generate_qr_signature(session_code, timestamp)
    return {
        "session_code": session_code,
        "timestamp": timestamp,
        "signature": signature,
    }
