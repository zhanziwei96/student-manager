"""
学生模型单元测试
"""
import pytest
from app.models import Student, StudentCreate, StudentUpdate, StudentResponse
from app.core.security import hash_password


class TestStudentModel:
    """测试学生模型"""

    def test_student_creation(self):
        """测试创建学生"""
        student = Student(
            student_id="2024001",
            name="张三"
        )

        assert student.student_id == "2024001"
        assert student.name == "张三"
        assert student.status == "active"
        assert student.is_account_enabled is True

    def test_student_default_values(self):
        """测试学生默认值"""
        student = Student(
            student_id="2024002",
            name="李四"
        )

        assert student.class_id is None
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
            name="赵六"
        )

        assert data.student_id == "2024004"
        assert data.class_id is None

    def test_student_update(self):
        """测试更新学生请求"""
        data = StudentUpdate(name="新名字")

        assert data.name == "新名字"

    def test_student_response_class_name_field(self):
        """测试响应模型的 class_name 响应字段（默认 None，由 API 层按 class_id 注入）"""
        data = StudentResponse(
            student_id="2024005",
            name="孙七",
            created_at="2024-01-01T00:00:00"
        )

        assert data.class_name is None

        data_with_class = StudentResponse(
            student_id="2024005",
            name="孙七",
            created_at="2024-01-01T00:00:00",
            class_name="2024届软件工程1班"
        )
        assert data_with_class.class_name == "2024届软件工程1班"
