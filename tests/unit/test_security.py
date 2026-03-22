"""
安全工具单元测试 - bcrypt 版本
"""
import pytest
from app.core.security import generate_password_hash, verify_password_hash, needs_password_upgrade


class TestPasswordHash:
    """测试密码哈希功能 (bcrypt)"""
    
    def test_generate_password_hash(self):
        """测试生成密码哈希 - bcrypt 格式"""
        password = "password123"
        password_hash, salt = generate_password_hash(password)
        
        assert password_hash is not None
        assert salt is not None
        # bcrypt 自动处理盐值，返回空字符串保持兼容
        assert salt == ""
        # bcrypt 哈希以 $2 开头
        assert password_hash.startswith('$2')
        assert password_hash != password  # 哈希后不应等于原密码
    
    def test_verify_password_hash_success(self):
        """测试密码验证成功"""
        password = "password123"
        password_hash, salt = generate_password_hash(password)
        
        # bcrypt 模式下 salt 参数被忽略
        result = verify_password_hash(password, password_hash, salt)
        assert result is True
        
        # 即使传入 None 也能验证（bcrypt 不需要外部 salt）
        result = verify_password_hash(password, password_hash, None)
        assert result is True
    
    def test_verify_password_hash_failure(self):
        """测试密码验证失败"""
        password = "password123"
        wrong_password = "wrongpassword"
        password_hash, salt = generate_password_hash(password)
        
        result = verify_password_hash(wrong_password, password_hash, salt)
        assert result is False
    
    def test_verify_password_hash_different_hashes(self):
        """测试相同密码生成不同哈希（bcrypt 自动盐值）"""
        password = "password123"
        hash1, salt1 = generate_password_hash(password)
        hash2, salt2 = generate_password_hash(password)
        
        # 相同密码但不同调用应生成不同哈希（自动随机盐值）
        assert hash1 != hash2
        # bcrypt 模式下 salt 返回空字符串
        assert salt1 == ""
        assert salt2 == ""
        
        # 但都能验证成功
        assert verify_password_hash(password, hash1, salt1) is True
        assert verify_password_hash(password, hash2, salt2) is True
    
    def test_verify_password_hash_with_none(self):
        """测试验证时传入 None"""
        result = verify_password_hash("password", None, None)
        assert result is False
        
        # 空哈希但传入 salt（bcrypt 模式下 salt 被忽略）
        result = verify_password_hash("password", "", None)
        assert result is False
    
    def test_needs_password_upgrade(self):
        """测试密码升级检测"""
        # bcrypt 哈希不需要升级
        bcrypt_hash = "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert needs_password_upgrade(bcrypt_hash) is False
        
        # SHA256 哈希需要升级（不以 $2 开头）
        sha256_hash = "a1b2c3d4e5f6..."
        assert needs_password_upgrade(sha256_hash) is True
        
        # None 不需要升级
        assert needs_password_upgrade(None) is False
        
        # 空字符串不需要升级
        assert needs_password_upgrade("") is False
