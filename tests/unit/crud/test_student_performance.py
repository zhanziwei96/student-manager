"""
学生 CRUD 性能优化测试

测试性能优化相关函数，特别是IN查询优化。
"""
import pytest
from sqlmodel import Session
from app.crud.student import (
    create_student, get_students_by_class, get_students_by_classes
)


class TestStudentQueryPerformance:
    """测试学生查询性能优化"""
    
    def test_get_students_by_classes_single(self, session: Session):
        """测试获取单个班级学生"""
        # 创建测试数据
        create_student(session, "S001", "张三", "软件1班")
        create_student(session, "S002", "李四", "软件1班")
        create_student(session, "S003", "王五", "软件2班")
        
        # 使用IN查询获取单个班级
        students = get_students_by_classes(session, ["软件1班"])
        
        assert len(students) == 2
        student_ids = {s.student_id for s in students}
        assert "S001" in student_ids
        assert "S002" in student_ids
    
    def test_get_students_by_classes_multiple(self, session: Session):
        """测试获取多个班级学生 - IN查询优化"""
        # 创建测试数据
        create_student(session, "S004", "张三", "软件1班")
        create_student(session, "S005", "李四", "软件2班")
        create_student(session, "S006", "王五", "软件3班")
        create_student(session, "S007", "赵六", "软件1班")
        
        # 使用IN查询一次性获取多个班级学生
        students = get_students_by_classes(session, ["软件1班", "软件2班"])
        
        assert len(students) == 3
        student_ids = {s.student_id for s in students}
        assert "S004" in student_ids
        assert "S005" in student_ids
        assert "S007" in student_ids
        assert "S006" not in student_ids  # 软件3班不应包含
    
    def test_get_students_by_classes_empty_list(self, session: Session):
        """测试空班级列表返回空结果"""
        students = get_students_by_classes(session, [])
        assert students == []
    
    def test_get_students_by_classes_not_exist(self, session: Session):
        """测试获取不存在的班级学生"""
        students = get_students_by_classes(session, ["不存在班级"])
        assert students == []
    
    def test_get_students_by_classes_vs_loop(self, session: Session):
        """对比IN查询和循环查询结果一致性"""
        # 创建测试数据
        create_student(session, "S008", "张三", "软件1班")
        create_student(session, "S009", "李四", "软件2班")
        create_student(session, "S010", "王五", "软件1班")
        
        # 循环查询结果
        loop_result = []
        for cls in ["软件1班", "软件2班"]:
            loop_result.extend(get_students_by_class(session, cls))
        
        # IN查询结果
        in_result = get_students_by_classes(session, ["软件1班", "软件2班"])
        
        # 结果应该一致（数量相同，学生ID相同）
        assert len(in_result) == len(loop_result)
        loop_ids = {s.student_id for s in loop_result}
        in_ids = {s.student_id for s in in_result}
        assert loop_ids == in_ids
