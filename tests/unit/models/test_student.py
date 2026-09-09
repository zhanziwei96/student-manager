"""
学生模型单元测试
"""
import pytest
from app.models import Student, StudentCreate, StudentUpdate
from app.core.security import hash_password


class TestStudentModel:
    """测试学生模型"""
    
    def test_student_creation(self):
        """测试创建学生"""
        student = Student(
            student_id="2024001",
            name="张三",
            class_name="软件1班"
        )
        
        assert student.student_id == "2024001"
        assert student.name == "张三"
        assert student.class_name == "软件1班"
        assert student.status == "active"
        assert student.is_account_enabled is True
    
    def test_student_default_values(self):
        """测试学生默认值"""
        student = Student(
            student_id="2024002",
            name="李四"
        )
        
        assert student.class_name == "未分班"
        assert student.status == "active"
        assert student.is_account_enabled is True
    
    def test_student_with_password(self):
        """测试带密码的学生 - SEC-003: 移除 salt"""
        password_hash = hash_password("2024003")
        
        student = Student(
            student_id="2024003",
            name="王五",
            password_hash=password_hash
        )
        
        assert student.password_hash is not None


class TestStudentSchemas:
    """测试学生 Schema"""
    
    def test_student_create(self):
        """测试创建学生请求"""
        data = StudentCreate(
            student_id="2024004",
            name="赵六",
            class_name="软件2班"
        )
        
        assert data.student_id == "2024004"
        assert data.class_name == "软件2班"
    
    def test_student_update(self):
        """测试更新学生请求"""
        data = StudentUpdate(name="新名字")
        
        assert data.name == "新名字"
        assert data.class_name is None
