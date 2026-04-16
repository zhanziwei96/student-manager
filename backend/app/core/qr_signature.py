"""
动态验证码工具模块
基于 HMAC-SHA256 生成短时验证码
"""
import hmac
import hashlib
import time

from app.core.config import get_settings


CODE_VALIDITY_SECONDS = 30
CODE_REFRESH_SECONDS = 15


def _generate_code(session_code: str, timestamp: int) -> str:
    """生成验证码内部实现"""
    message = f"{session_code}|{timestamp}"
    secret_key = get_settings().security.secret_key.encode("utf-8")
    hash_val = hmac.new(secret_key, message.encode("utf-8"), hashlib.sha256).hexdigest()
    # 取前6位大写字母+数字，去除易混淆字符
    code = hash_val.upper()[:6]
    code = code.replace('0', 'A').replace('O', 'B').replace('I', 'C').replace('L', 'D')
    return code


def generate_verification_code(session_code: str) -> dict:
    """生成动态验证码

    Args:
        session_code: 签到会话代码

    Returns:
        dict: 包含 code、expires_in 的字典
    """
    timestamp = int(time.time()) // CODE_REFRESH_SECONDS * CODE_REFRESH_SECONDS
    code = _generate_code(session_code, timestamp)
    expires_in = CODE_REFRESH_SECONDS - (int(time.time()) - timestamp)
    return {
        "code": code,
        "expires_in": expires_in,
    }


def verify_verification_code(session_code: str, code: str) -> bool:
    """验证动态验证码

    检查当前时间窗口及前后一个窗口，容错时间差

    Args:
        session_code: 签到会话代码
        code: 待验证的验证码

    Returns:
        bool: 验证码有效返回 True，否则返回 False
    """
    normalized = code.upper().strip()
    now = int(time.time())
    for offset in (-CODE_REFRESH_SECONDS, 0, CODE_REFRESH_SECONDS):
        ts = (now + offset) // CODE_REFRESH_SECONDS * CODE_REFRESH_SECONDS
        expected = _generate_code(session_code, ts)
        if hmac.compare_digest(expected, normalized):
            return True
    return False
