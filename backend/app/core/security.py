"""
安全相关工具
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional


def generate_password_hash(password: str) -> tuple[str, str]:
    """生成密码哈希和盐值
    
    Returns:
        (password_hash, salt)
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    return password_hash, salt


def verify_password_hash(password: str, password_hash: Optional[str], salt: Optional[str]) -> bool:
    """验证密码
    
    Args:
        password: 明文密码
        password_hash: 存储的密码哈希
        salt: 盐值
        
    Returns:
        是否匹配
    """
    if not password_hash or not salt:
        return False
    computed_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    return computed_hash == password_hash
