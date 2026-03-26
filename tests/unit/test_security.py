"""
安全工具单元测试 - bcrypt 版本
"""
import pytest
from app.core.security import (
    generate_password_hash, verify_password_hash, needs_password_upgrade,
    hash_password, verify_password  # SEC-003: 新接口
)


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
    
    # ========== SEC-003: 新接口测试 (hash_password / verify_password) ==========
    
    def test_hash_password(self):
        """测试 hash_password 新接口"""
        password = "new_password_456"
        password_hash = hash_password(password)
        
        assert password_hash is not None
        assert isinstance(password_hash, str)
        # bcrypt 哈希以 $2 开头
        assert password_hash.startswith('$2')
        # 哈希后不应等于原密码
        assert password_hash != password
    
    def test_verify_password_success(self):
        """测试 verify_password 新接口 - 验证成功"""
        password = "test_password"
        password_hash = hash_password(password)
        
        # 正确密码验证成功
        assert verify_password(password, password_hash) is True
    
    def test_verify_password_failure(self):
        """测试 verify_password 新接口 - 验证失败"""
        password = "test_password"
        wrong_password = "wrong_password"
        password_hash = hash_password(password)
        
        # 错误密码验证失败
        assert verify_password(wrong_password, password_hash) is False
    
    def test_verify_password_edge_cases(self):
        """测试 verify_password 边界情况"""
        password = "test_password"
        password_hash = hash_password(password)
        
        # 空密码应失败（bcrypt 对空密码的处理）
        # 注意：空密码哈希后仍是一个有效哈希
        empty_hash = hash_password("")
        assert verify_password("", empty_hash) is True  # 空密码可以验证空密码的哈希
        assert verify_password("", password_hash) is False  # 空密码不能验证非空密码的哈希
        
        # None 哈希应失败（不崩溃）
        assert verify_password(password, None) is False
        
        # 空字符串哈希应失败
        assert verify_password(password, "") is False
        
        # None 密码 - verify_password 不处理 None，这是预期的
        # 实际调用时应确保传入字符串
    
    def test_hash_and_verify_roundtrip(self):
        """测试 hash -> verify 完整流程"""
        passwords = [
            "simple",
            "Complex123!@#",
            "a" * 50,  # 较长密码（bcrypt 截断到 72 字节，50字节安全）
            "中文密码测试",
            "   spaces   ",
            "",
        ]
        
        for password in passwords:
            password_hash = hash_password(password)
            # 验证自己生成的哈希
            assert verify_password(password, password_hash) is True
            # 验证错误密码失败（使用完全不同的密码避免截断后相同）
            assert verify_password("wrong_password_123", password_hash) is False
    
    def test_bcrypt_72_byte_truncation(self):
        """测试 bcrypt 72 字节截断特性"""
        # bcrypt 只使用前 72 字节，超出的部分被忽略
        long_password_1 = "a" * 71 + "x"
        long_password_2 = "a" * 71 + "y"  # 第72字节不同
        long_password_3 = "a" * 71 + "x" + "_extra"  # 超出72字节但前72字节与1相同
        
        hash_1 = hash_password(long_password_1)
        
        # 验证：72字节内不同则验证失败
        assert verify_password(long_password_2, hash_1) is False
        
        # 验证：72字节相同则验证成功（超出部分被忽略）
        assert verify_password(long_password_3, hash_1) is True
    
    def test_new_and_old_interface_equivalent(self):
        """测试新旧接口等价性"""
        password = "test_equivalent"
        
        # 新接口
        new_hash = hash_password(password)
        new_result = verify_password(password, new_hash)
        
        # 旧接口
        old_hash, _ = generate_password_hash(password)
        old_result = verify_password_hash(password, old_hash, "")
        
        # 验证结果应相同
        assert new_result is True
        assert old_result is True
        
        # 注意：bcrypt 每次使用随机盐，所以哈希值不同
        # 但都能验证成功
        assert new_hash != old_hash  # 不同的随机盐
        assert verify_password(password, old_hash) is True  # 新接口验证旧哈希
        assert verify_password_hash(password, new_hash, "") is True  # 旧接口验证新哈希
    
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
