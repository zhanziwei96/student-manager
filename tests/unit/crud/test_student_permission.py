"""
学生权限查询测试 - BE-003 修复验证

测试 CRUD 层的权限控制逻辑是否正确实现
"""
import pytest
from app.crud.student import get_students_by_permission, get_classes_by_permission


class TestGetStudentsByPermission:
    """测试 get_students_by_permission 函数"""

    def test_admin_can_view_all_students(self, session):
        """管理员可以查看所有学生"""
        from app.models import Student
        
        # 创建测试学生
        student1 = Student(student_id="S001", name="学生1", class_name="班级A", score=80)
        student2 = Student(student_id="S002", name="学生2", class_name="班级B", score=85)
        session.add_all([student1, student2])
        session.commit()
        
        # 管理员用户
        user = {"is_admin": True, "sub": "1"}
        
        students, error = get_students_by_permission(session, user)
        
        assert error is None
        assert len(students) == 2
        assert {s.student_id for s in students} == {"S001", "S002"}

    def test_admin_can_view_students_by_class(self, session):
        """管理员可以按班级查看学生"""
        from app.models import Student
        
        student1 = Student(student_id="S001", name="学生1", class_name="班级A", score=80)
        student2 = Student(student_id="S002", name="学生2", class_name="班级B", score=85)
        session.add_all([student1, student2])
        session.commit()
        
        user = {"is_admin": True, "sub": "1"}
        
        students, error = get_students_by_permission(session, user, class_name="班级A")
        
        assert error is None
        assert len(students) == 1
        assert students[0].student_id == "S001"

    def test_invalid_user_id(self, session):
        """无效的用户ID返回错误"""
        user = {"is_admin": False, "sub": None}
        
        students, error = get_students_by_permission(session, user)
        
        assert error == "无效的用户信息"
        assert students is None


class TestGetClassesByPermission:
    """测试 get_classes_by_permission 函数"""

    def test_admin_can_view_all_classes(self, session):
        """管理员可以查看所有班级"""
        from app.models import Student
        
        student1 = Student(student_id="S001", name="学生1", class_name="班级A", score=80)
        student2 = Student(student_id="S002", name="学生2", class_name="班级B", score=85)
        session.add_all([student1, student2])
        session.commit()
        
        user = {"is_admin": True, "sub": "1"}
        
        classes, error = get_classes_by_permission(session, user)
        
        assert error is None
        assert set(classes) == {"班级A", "班级B"}


class TestBE003Fix:
    """验证 BE-003 修复：业务逻辑从 API 层移至 CRUD 层"""

    def test_business_logic_in_crud_layer(self):
        """验证业务逻辑已移至 CRUD 层"""
        import inspect
        from app.crud import student as student_module
        
        # 验证 CRUD 层有权限控制函数
        assert hasattr(student_module, 'get_students_by_permission')
        assert hasattr(student_module, 'get_classes_by_permission')
        
        # 验证函数签名正确
        sig = inspect.signature(get_students_by_permission)
        params = list(sig.parameters.keys())
        assert 'session' in params
        assert 'user' in params
        assert 'class_name' in params

    def test_api_layer_simplified(self):
        """验证 API 层已简化"""
        # 读取 students.py 内容
        from pathlib import Path
        students_py_path = Path(__file__).parent.parent.parent.parent / "backend" / "app" / "api" / "routes" / "students.py"
        content = students_py_path.read_text()
        
        # 验证使用了新的 CRUD 函数
        assert "get_students_by_permission" in content
        assert "get_classes_by_permission" in content
        
        # 验证不再有复杂的权限判断逻辑
        assert "assigned_classes = user_obj.get_assigned_classes()" not in content
