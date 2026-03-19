"""
密码值对象
封装密码验证规则
"""
import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class Password:
    """密码值对象 - 存储哈希值"""
    hash_value: str
    salt: str
    
    @classmethod
    def create_from_plain(cls, plain_password: str) -> "Password":
        """从明文密码创建"""
        if len(plain_password) < 6:
            raise ValueError("密码长度至少6位")
        
        salt = secrets.token_hex(16)
        hash_value = cls._hash_password(plain_password, salt)
        return cls(hash_value=hash_value, salt=salt)
    
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """PBKDF2 密码哈希"""
        return hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode(), 
            salt.encode(), 
            100000
        ).hex()
    
    def verify(self, plain_password: str) -> bool:
        """验证明文密码"""
        return self._hash_password(plain_password, self.salt) == self.hash_value
    
    def __str__(self) -> str:
        return "[PROTECTED]"
