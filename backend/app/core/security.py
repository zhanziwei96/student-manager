"""
安全相关工具 - 使用 bcrypt 替代 SHA256
"""
import bcrypt
from datetime import datetime, timedelta
from typing import Optional


def generate_password_hash(password: str) -> tuple[str, str]:
    """生成密码哈希和盐值（使用 bcrypt）
    
    bcrypt 自动处理盐值，返回格式兼容旧接口
    
    注意：bcrypt 有 72 字节长度限制，超长密码会被截断处理
    
    Returns:
        (password_hash, salt) - salt 返回空字符串以保持兼容
    """
    # bcrypt 有 72 字节长度限制
    password_bytes = password.encode('utf-8')[:72]
    
    # bcrypt 自动生成随机盐并包含在哈希中
    password_hash = bcrypt.hashpw(
        password_bytes, 
        bcrypt.gensalt(rounds=12)  # 12轮是平衡安全性和性能的推荐值
    ).decode('utf-8')
    
    # 保持接口兼容：返回 (hash, salt)
    # bcrypt 的哈希已包含盐值，所以 salt 返回空
    return password_hash, ""


def verify_password_hash(password: str, password_hash: Optional[str], salt: Optional[str]) -> bool:
    """验证密码（支持 bcrypt 和旧版 SHA256 迁移）
    
    Args:
        password: 明文密码
        password_hash: 存储的密码哈希
        salt: 盐值（bcrypt 模式下忽略）
        
    Returns:
        是否匹配
    """
    if not password_hash:
        return False
    
    # 检测哈希类型
    if password_hash.startswith('$2'):
        # bcrypt 哈希（以 $2a$, $2b$, $2y$ 开头）
        # bcrypt 有 72 字节长度限制
        password_bytes = password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, password_hash.encode('utf-8'))
    else:
        # 旧版 SHA256 - 为了兼容现有用户，保留验证逻辑
        # 建议：用户下次登录时自动迁移到 bcrypt
        import hashlib
        if not salt:
            return False
        computed_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return computed_hash == password_hash


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
    return locked_until > datetime.now()


def calculate_lockout_time(fail_count: int) -> Optional[datetime]:
    """计算账号锁定截止时间"""
    if fail_count >= MAX_LOGIN_FAILURES:
        return datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    return None
