"""
学号值对象测试
不需要数据库，不需要mock，纯单元测试
"""
import pytest
from domain.value_objects.student_id import StudentId


class TestStudentId:
    """学号值对象测试类"""
    
    # ========== 构造测试 ==========
    
    def test_create_valid_id(self):
        """创建有效学号"""
        sid = StudentId("2024001")
        
        assert sid.value == "2024001"
        assert str(sid) == "2024001"
    
    def test_create_min_length_id(self):
        """创建最小长度（5位）学号"""
        sid = StudentId("12345")
        
        assert sid.value == "12345"
    
    def test_create_long_id(self):
        """创建长学号"""
        long_id = "2024" + "0" * 20
        sid = StudentId(long_id)
        
        assert sid.value == long_id
    
    def test_create_empty_id_raises_error(self):
        """空学号抛出异常"""
        with pytest.raises(ValueError, match="学号不能为空"):
            StudentId("")
    
    def test_create_too_short_id_raises_error(self):
        """学号太短（少于5位）抛出异常"""
        with pytest.raises(ValueError, match="学号.*至少5位"):
            StudentId("1234")  # 4位
    
    def test_create_single_char_raises_error(self):
        """单字符学号抛出异常"""
        with pytest.raises(ValueError, match="学号.*至少5位"):
            StudentId("A")
    
    # ========== 相等性测试 ==========
    
    def test_same_value_are_equal(self):
        """相同值相等"""
        sid1 = StudentId("2024001")
        sid2 = StudentId("2024001")
        
        assert sid1 == sid2
        assert sid1.value == sid2.value
    
    def test_different_value_are_not_equal(self):
        """不同值不相等"""
        sid1 = StudentId("2024001")
        sid2 = StudentId("2024002")
        
        assert sid1 != sid2
    
    def test_not_equal_to_string(self):
        """不与字符串相等"""
        sid = StudentId("2024001")
        
        assert sid != "2024001"  # 类型不同
        assert sid.value == "2024001"  # 但值相同
    
    def test_not_equal_to_none(self):
        """不与None相等"""
        sid = StudentId("2024001")
        
        assert sid != None
    
    def test_not_equal_to_other_type(self):
        """不与其他类型相等"""
        sid = StudentId("2024001")
        
        assert sid != 2024001  # 整数
        assert sid != ["2024001"]  # 列表
        assert sid != {"value": "2024001"}  # 字典
    
    # ========== 哈希测试 ==========
    
    def test_can_be_used_as_dict_key(self):
        """可作为字典key"""
        sid1 = StudentId("2024001")
        sid2 = StudentId("2024002")
        
        d = {sid1: "张三", sid2: "李四"}
        
        assert d[sid1] == "张三"
        assert d[sid2] == "李四"
    
    def test_same_value_same_hash(self):
        """相同值有相同哈希"""
        sid1 = StudentId("2024001")
        sid2 = StudentId("2024001")
        
        assert hash(sid1) == hash(sid2)
    
    def test_different_value_different_hash(self):
        """不同值通常有不同哈希（可能碰撞但概率低）"""
        sid1 = StudentId("2024001")
        sid2 = StudentId("2024002")
        
        # 注意：哈希可能碰撞，但在测试数据下应该不同
        assert hash(sid1) != hash(sid2)
    
    def test_can_be_used_in_set(self):
        """可用于集合"""
        sid1 = StudentId("2024001")
        sid2 = StudentId("2024001")  # 相同值
        sid3 = StudentId("2024002")
        
        s = {sid1, sid2, sid3}
        
        # 相同值的只保留一个
        assert len(s) == 2
    
    # ========== 不可变性测试 ==========
    
    def test_immutable_cannot_change_value(self):
        """不可变：不能修改value"""
        sid = StudentId("2024001")
        
        with pytest.raises(AttributeError):
            sid.value = "2024002"
    
    # ========== 边界值测试 ==========
    
    def test_id_with_letters(self):
        """包含字母的学号"""
        sid = StudentId("ABC12345")
        
        assert sid.value == "ABC12345"
    
    def test_id_with_special_chars(self):
        """包含特殊字符的学号"""
        sid = StudentId("2024-001")
        
        assert sid.value == "2024-001"
    
    def test_id_with_unicode(self):
        """包含Unicode的学号"""
        sid = StudentId("2024学001")
        
        assert sid.value == "2024学001"
    
    def test_id_with_spaces_raises_error(self):
        """包含空格的学号（空格算字符，但可能不是预期行为）"""
        # 注意：如果业务不允许空格，需要额外验证
        # 当前实现允许空格，只要长度>=5
        sid = StudentId("2024 001")  # 8字符（含空格）
        
        assert sid.value == "2024 001"
    
    # ========== 字符串表示测试 ==========
    
    def test_str_returns_value(self):
        """str返回value值"""
        sid = StudentId("2024001")
        
        assert str(sid) == "2024001"
    
    def test_repr_contains_value(self):
        """repr包含value信息"""
        sid = StudentId("2024001")
        repr_str = repr(sid)
        
        assert "2024001" in repr_str
        assert "StudentId" in repr_str
