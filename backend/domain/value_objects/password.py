"""
密码值对象
处理密码哈希和验证（纯领域逻辑，不依赖外部库）
"""
from dataclasses import dataclass
import hashlib
import secrets


@dataclass(frozen=True)
class Password:
    """密码值对象
    
    属性:
        hash: 密码哈希值
        salt: 盐值
    """
    hash: str
    salt: str
    
    @classmethod
    def create(cls, plain_text: str) -> 'Password':
        """创建新密码（生成随机盐值）
        
        Args:
            plain_text: 明文密码
            
        Returns:
            Password值对象
        """
        salt = secrets.token_hex(16)
        hash_value = cls._hash(plain_text, salt)
        return cls(hash=hash_value, salt=salt)
    
    @classmethod
    def from_hash(cls, hash_value: str, salt: str) -> 'Password':
        """从已有哈希和盐值创建
        
        Args:
            hash_value: 密码哈希
            salt: 盐值
            
        Returns:
            Password值对象
        """
        return cls(hash=hash_value, salt=salt)
    
    def verify(self, plain_text: str) -> bool:
        """验证密码
        
        Args:
            plain_text: 明文密码
            
        Returns:
            是否匹配
        """
        return self._hash(plain_text, self.salt) == self.hash
    
    def reset(self, new_plain_text: str) -> 'Password':
        """重置密码
        
        Args:
            new_plain_text: 新明文密码
            
        Returns:
            新的Password值对象
        """
        return self.create(new_plain_text)
    
    @staticmethod
    def _hash(password: str, salt: str) -> str:
        """计算密码哈希（私有方法）
        
        Args:
            password: 明文密码
            salt: 盐值
            
        Returns:
            SHA256哈希值
        """
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
