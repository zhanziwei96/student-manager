"""
安全工具单元测试
"""
import pytest
from app.core.security import generate_password_hash, verify_password_hash


class TestPasswordHash:
    """测试密码哈希功能"""
    
    def test_generate_password_hash(self):
        """测试生成密码哈希"""
        password = "password123"
        password_hash, salt = generate_password_hash(password)
        
        assert password_hash is not None
        assert salt is not None
        assert len(salt) == 32  # 16字节 = 32个十六进制字符
        assert password_hash != password  # 哈希后不应等于原密码
    
    def test_verify_password_hash_success(self):
        """测试密码验证成功"""
        password = "password123"
        password_hash, salt = generate_password_hash(password)
        
        result = verify_password_hash(password, password_hash, salt)
        assert result is True
    
    def test_verify_password_hash_failure(self):
        """测试密码验证失败"""
        password = "password123"
        wrong_password = "wrongpassword"
        password_hash, salt = generate_password_hash(password)
        
        result = verify_password_hash(wrong_password, password_hash, salt)
        assert result is False
    
    def test_verify_password_hash_different_salts(self):
        """测试不同盐值生成不同哈希"""
        password = "password123"
        hash1, salt1 = generate_password_hash(password)
        hash2, salt2 = generate_password_hash(password)
        
        # 相同密码但不同盐值应生成不同哈希
        assert hash1 != hash2
        assert salt1 != salt2
        
        # 但都能验证成功
        assert verify_password_hash(password, hash1, salt1) is True
        assert verify_password_hash(password, hash2, salt2) is True
    
    def test_verify_password_hash_with_none(self):
        """测试验证时传入 None"""
        result = verify_password_hash("password", None, None)
        assert result is False
        
        result = verify_password_hash("password", "hash", None)
        assert result is False
        
        result = verify_password_hash("password", None, "salt")
        assert result is False
