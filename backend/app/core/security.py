"""
安全相关工具 - 使用 bcrypt 替代 SHA256
SEC-003: 密码盐值冗余存储修复
"""
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.core.timezone import get_now


# ========== SEC-003: 新的简化接口 ==========

def hash_password(password: str) -> str:
    """生成密码哈希（bcrypt，自动处理盐值）
    
    SEC-003: 简化接口，bcrypt 自动处理盐值，无需单独存储
    
    Args:
        password: 明文密码
        
    Returns:
        str: bcrypt 哈希字符串（包含内置盐值）
        
    Note:
        bcrypt 有 72 字节长度限制，超长密码会被截断
    """
    # bcrypt 有 72 字节长度限制
    password_bytes = password.encode('utf-8')[:72]
    
    # bcrypt 自动生成随机盐并包含在哈希中
    return bcrypt.hashpw(
        password_bytes, 
        bcrypt.gensalt(rounds=12)  # 12轮是平衡安全性和性能的推荐值
    ).decode('utf-8')


def verify_password(password: str, password_hash: Optional[str]) -> bool:
    """验证密码（支持 bcrypt）
    
    SEC-003: 简化接口，bcrypt 哈希已包含盐值
    
    Args:
        password: 明文密码
        password_hash: 存储的密码哈希
        
    Returns:
        bool: 是否匹配
    """
    if not password_hash:
        return False
    
    # 只支持 bcrypt 哈希（以 $2a$, $2b$, $2y$ 开头）
    if password_hash.startswith('$2'):
        password_bytes = password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, password_hash.encode('utf-8'))
    
    # 旧版 SHA256 不再支持（需要重新设置密码）
    return False


# ========== 向后兼容接口（已弃用） ==========

def generate_password_hash(password: str) -> Tuple[str, str]:
    """生成密码哈希和盐值（已弃用）
    
    SEC-003 DEPRECATED: 使用 hash_password() 替代
    
    保留此函数仅用于向后兼容，salt 始终返回空字符串
    """
    password_hash = hash_password(password)
    return password_hash, ""  # salt 返回空字符串以保持兼容


def verify_password_hash(password: str, password_hash: Optional[str], salt: Optional[str] = None) -> bool:
    """验证密码（已弃用）
    
    SEC-003 DEPRECATED: 使用 verify_password() 替代
    
    Args:
        salt: 已弃用参数，bcrypt 哈希已包含盐值
    """
    # 忽略 salt 参数，bcrypt 哈希已包含盐值
    return verify_password(password, password_hash)


def needs_password_upgrade(password_hash: Optional[str]) -> bool:
    """检查密码是否需要升级到 bcrypt
    
    用于识别仍在使用旧版 SHA256 的账号
    """
    if not password_hash:
        return False
    return not password_hash.startswith('$2')


# ========== 登录安全相关 ==========

MAX_LOGIN_FAILURES = 10
LOCKOUT_DURATION_MINUTES = 30


def is_account_locked(locked_until: Optional[datetime]) -> bool:
    """检查账号是否处于锁定状态"""
    if not locked_until:
        return False
    return locked_until > get_now()


def calculate_lockout_time(fail_count: int) -> Optional[datetime]:
    """计算账号锁定截止时间"""
    if fail_count >= MAX_LOGIN_FAILURES:
        return get_now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    return None
