"""
学生权限查询测试 - REVIEW-P1: 权限检查已移至 API 层

原测试验证 CRUD 层权限控制，现已重构为验证 API 层权限控制。
CRUD 层保持纯粹，只负责数据操作。
"""
import pytest


class TestStudentPermissionArchitecture:
    """验证权限架构：CRUD 层纯粹，API 层负责权限"""

    def test_crud_layer_no_permission_logic(self):
        """验证 CRUD 层不再包含权限控制函数"""
        from app.crud import student as student_module
        
        # 验证 CRUD 层已移除权限控制函数（REVIEW-P1）
        assert not hasattr(student_module, 'get_students_by_permission'), \
            "get_students_by_permission 应已移至 API 层"
        assert not hasattr(student_module, 'get_classes_by_permission'), \
            "get_classes_by_permission 应已移至 API 层"

    def test_crud_layer_pure_functions(self):
        """验证 CRUD 层只包含纯粹的数据操作函数"""
        from app.crud import student as student_module
        
        # CRUD 层应有的纯粹函数
        pure_functions = [
            'get_student', 'get_students', 'get_students_by_class',
            'create_student', 'delete_student',
            'get_all_classes', 'reset_student_password', 'count_students'
        ]
        
        for func_name in pure_functions:
            assert hasattr(student_module, func_name), f"CRUD 层应包含 {func_name}"

    def test_api_layer_has_permission_logic(self):
        """验证 API 层包含权限控制逻辑"""
        from pathlib import Path
        
        students_py_path = Path(__file__).parent.parent.parent.parent / "backend" / "app" / "api" / "routes" / "students.py"
        content = students_py_path.read_text()
        
        # 验证 API 层有权限检查逻辑
        assert "is_admin = user.get(\"is_admin\", False)" in content, \
            "API 层应包含管理员权限检查"
        assert "get_teacher_accessible_classes" in content, \
            "API 层应包含授课班级权限检查"
        assert "get_students_by_permission" not in content, \
            "API 层不应再调用已删除的 CRUD 权限函数"
        assert "get_classes_by_permission" not in content, \
            "API 层不应再调用已删除的 CRUD 权限函数"


class TestStudentCRUDPureFunctions:
    """测试 CRUD 层纯粹函数"""

    def test_get_students_no_permission_check(self, session):
        """验证 get_students 不做权限检查"""
        from app.models import Student
        from app.crud import get_students
        
        # 创建测试学生
        student = Student(student_id="S001", name="学生1", class_name="班级A", score=80)
        session.add(student)
        session.commit()
        
        # 直接调用应返回所有学生（无权限过滤）
        students = get_students(session)
        assert len(students) == 1
        assert students[0].student_id == "S001"

    def test_get_students_by_class_no_permission_check(self, session, seed_refs):
        """验证 get_students_by_class 不做权限检查"""
        from app.models import Student
        from app.crud import get_students_by_class

        student1 = Student(student_id="S001", name="学生1",
                           class_name="一班", class_id=seed_refs["一班"])
        student2 = Student(student_id="S002", name="学生2",
                           class_name="二班", class_id=seed_refs["二班"])
        session.add_all([student1, student2])
        session.commit()

        # 直接调用应返回指定班级学生（无权限过滤）
        students = get_students_by_class(session, "一班")
        assert len(students) == 1
        assert students[0].student_id == "S001"

    def test_get_all_classes_no_permission_check(self, session, seed_refs):
        """验证 get_all_classes 不做权限检查"""
        from app.models import Student
        from app.crud import get_all_classes

        student1 = Student(student_id="S001", name="学生1",
                           class_name="一班", class_id=seed_refs["一班"])
        student2 = Student(student_id="S002", name="学生2",
                           class_name="二班", class_id=seed_refs["二班"])
        session.add_all([student1, student2])
        session.commit()

        # 直接调用应返回所有班级（无权限过滤）
        classes = get_all_classes(session)
        assert {"一班", "二班"} <= set(classes)
