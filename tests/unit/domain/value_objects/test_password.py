"""
密码值对象测试
不需要数据库，不需要mock，纯单元测试
"""
import pytest
from domain.value_objects.password import Password


class TestPassword:
    """密码值对象测试类"""
    
    # ========== 构造测试 ==========
    
    def test_create_from_plain_success(self):
        """成功从明文创建密码"""
        password = Password.create_from_plain("secure123")
        
        assert password.hash_value is not None
        assert password.salt is not None
        assert len(password.salt) == 32  # 16字节hex编码 = 32字符
        assert len(password.hash_value) == 64  # SHA256 hex = 64字符
    
    def test_password_min_length_6(self):
        """密码最小长度6位"""
        with pytest.raises(ValueError, match="密码长度至少6位"):
            Password.create_from_plain("12345")  # 5位
    
    def test_password_empty(self):
        """空密码抛出异常"""
        with pytest.raises(ValueError, match="密码长度至少6位"):
            Password.create_from_plain("")
    
    def test_password_exactly_6_chars(self):
        """刚好6位密码可以创建"""
        password = Password.create_from_plain("123456")
        assert password is not None
    
    # ========== 哈希特性测试 ==========
    
    def test_same_password_different_hash(self):
        """相同明文产生不同哈希（salt不同）"""
        pwd1 = Password.create_from_plain("samepassword")
        pwd2 = Password.create_from_plain("samepassword")
        
        # salt 应该不同
        assert pwd1.salt != pwd2.salt
        # hash 应该不同
        assert pwd1.hash_value != pwd2.hash_value
    
    def test_hash_is_not_plaintext(self):
        """哈希值不是明文"""
        plain = "mypassword123"
        password = Password.create_from_plain(plain)
        
        # 哈希值不应该包含明文
        assert plain not in password.hash_value
        assert password.hash_value != plain
    
    def test_hash_deterministic_with_same_salt(self):
        """相同salt产生相同哈希"""
        plain = "testpass"
        salt = "abcdef1234567890"
        
        hash1 = Password._hash_password(plain, salt)
        hash2 = Password._hash_password(plain, salt)
        
        assert hash1 == hash2
    
    # ========== 验证测试 ==========
    
    def test_verify_correct_password(self):
        """验证正确密码返回True"""
        password = Password.create_from_plain("correct123")
        
        assert password.verify("correct123") is True
    
    def test_verify_wrong_password(self):
        """验证错误密码返回False"""
        password = Password.create_from_plain("correct123")
        
        assert password.verify("wrong123") is False
    
    def test_verify_case_sensitive(self):
        """密码验证大小写敏感"""
        password = Password.create_from_plain("SecurePass")
        
        assert password.verify("securepass") is False  # 小写不匹配
        assert password.verify("SecurePass") is True   # 完全匹配
    
    def test_verify_empty_password(self):
        """验证空密码返回False"""
        password = Password.create_from_plain("somepass")
        
        assert password.verify("") is False
    
    # ========== 安全性测试 ==========
    
    def test_str_representation_hides_password(self):
        """字符串表示隐藏密码"""
        password = Password.create_from_plain("secret123")
        
        assert str(password) == "[PROTECTED]"
        assert "secret" not in str(password)
    
    def test_no_plaintext_in_repr(self):
        """repr中也不应该包含明文"""
        password = Password.create_from_plain("secret123")
        repr_str = repr(password)
        
        assert "secret" not in repr_str
        assert "[PROTECTED]" in repr_str or "hash_value" in repr_str
    
    # ========== 边界测试 ==========
    
    def test_very_long_password(self):
        """超长密码"""
        long_pass = "a" * 1000
        password = Password.create_from_plain(long_pass)
        
        assert password.verify(long_pass) is True
        assert password.verify(long_pass[:-1]) is False
    
    def test_password_with_special_chars(self):
        """包含特殊字符的密码"""
        special_pass = "p@ssw0rd!#$%^&*()"
        password = Password.create_from_plain(special_pass)
        
        assert password.verify(special_pass) is True
    
    def test_password_with_unicode(self):
        """包含Unicode的密码"""
        unicode_pass = "密码123abc"
        password = Password.create_from_plain(unicode_pass)
        
        assert password.verify(unicode_pass) is True
    
    def test_password_with_spaces(self):
        """包含空格的密码"""
        space_pass = "pass word 123"
        password = Password.create_from_plain(space_pass)
        
        assert password.verify(space_pass) is True
        assert password.verify("password123") is False  # 去掉空格不匹配
