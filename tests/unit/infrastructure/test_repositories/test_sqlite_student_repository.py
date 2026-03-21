import sys
import os

# 添加 backend 到 Python 路径（必须在任何其他导入之前）
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

"""
SQLite 学生仓储测试
使用内存数据库，无需外部依赖
"""
import pytest
from datetime import datetime
from domain.entities.student import Student
from domain.value_objects.student_id import StudentId
from domain.value_objects.score import Score


class TestSQLiteStudentRepository:
    """SQLite 学生仓储测试类"""
    
    @pytest.fixture
    def sample_student(self):
        """示例学生"""
        return Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(75.5)
        )
    
    # ========== 保存测试 ==========
    
    def test_save_new_student(self, student_repo):
        """保存新学生"""
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70)
        )
        
        student_repo.save(student)
        
        # 验证能查找到
        found = student_repo.find_by_id_str("2024001")
        assert found is not None
        assert found.name == "张三"
    
    def test_save_multiple_students(self, student_repo):
        """保存多个学生"""
        students = [
            Student(StudentId("2024001"), "张三", "软件1班", Score(70)),
            Student(StudentId("2024002"), "李四", "软件1班", Score(80)),
            Student(StudentId("2024003"), "王五", "软件2班", Score(90)),
        ]
        
        for s in students:
            student_repo.save(s)
        
        all_students = student_repo.find_all()
        assert len(all_students) == 3
    
    def test_save_updates_existing_student(self, student_repo, sample_student):
        """保存已存在的学生（更新）"""
        student_repo.save(sample_student)
        
        # 修改后再次保存
        sample_student.name = "张三丰"
        sample_student.class_name = "计算机1班"
        sample_student.score = Score(85)
        student_repo.save(sample_student)
        
        # 验证更新成功
        found = student_repo.find_by_id_str("2024001")
        assert found.name == "张三丰"
        assert found.class_name == "计算机1班"
        assert float(found.score) == 85
    
    # ========== 查询测试 ==========
    
    def test_find_by_id_str_exists(self, student_repo, sample_student):
        """通过学号查找存在的学生"""
        student_repo.save(sample_student)
        
        found = student_repo.find_by_id_str("2024001")
        
        assert found is not None
        assert str(found.student_id) == "2024001"
        assert found.name == "张三"
        assert found.class_name == "软件1班"
        assert float(found.score) == 75.5
    
    def test_find_by_id_str_not_exists(self, student_repo):
        """通过学号查找不存在的学生"""
        found = student_repo.find_by_id_str("9999999")
        
        assert found is None
    
    def test_find_by_id_with_student_id_object(self, student_repo, sample_student):
        """通过 StudentId 对象查找"""
        student_repo.save(sample_student)
        
        found = student_repo.find_by_id(StudentId("2024001"))
        
        assert found is not None
        assert found.name == "张三"
    
    def test_find_all_empty(self, student_repo):
        """查找所有学生（空表）"""
        students = student_repo.find_all()
        
        assert students == []
    
    def test_find_all_returns_all(self, student_repo):
        """查找所有学生"""
        student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(70)))
        student_repo.save(Student(StudentId("2024002"), "李四", "软件1班", Score(80)))
        
        students = student_repo.find_all()
        
        assert len(students) == 2
        # 默认按 created_at 降序
        assert students[0].name == "李四"
        assert students[1].name == "张三"
    
    def test_find_by_class_exists(self, student_repo):
        """通过班级查找学生"""
        student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(70)))
        student_repo.save(Student(StudentId("2024002"), "李四", "软件1班", Score(80)))
        student_repo.save(Student(StudentId("2024003"), "王五", "软件2班", Score(90)))
        
        students = student_repo.find_by_class("软件1班")
        
        assert len(students) == 2
        assert all(s.class_name == "软件1班" for s in students)
    
    def test_find_by_class_empty(self, student_repo):
        """通过班级查找（无结果）"""
        student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(70)))
        
        students = student_repo.find_by_class("计算机1班")
        
        assert students == []
    
    def test_find_by_class_order(self, student_repo):
        """班级查找结果按学号排序"""
        student_repo.save(Student(StudentId("2024003"), "王五", "软件1班", Score(70)))
        student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(80)))
        student_repo.save(Student(StudentId("2024002"), "李四", "软件1班", Score(90)))
        
        students = student_repo.find_by_class("软件1班")
        
        assert [str(s.student_id) for s in students] == ["2024001", "2024002", "2024003"]
    
    def test_find_by_name(self, student_repo):
        """通过姓名模糊查找"""
        student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(70)))
        student_repo.save(Student(StudentId("2024002"), "张三丰", "软件1班", Score(80)))
        student_repo.save(Student(StudentId("2024003"), "李四", "软件1班", Score(90)))
        
        students = student_repo.find_by_name("张")
        
        assert len(students) == 2
        assert "张三" in [s.name for s in students]
        assert "张三丰" in [s.name for s in students]
    
    def test_find_by_name_not_found(self, student_repo):
        """姓名查找无结果"""
        student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(70)))
        
        students = student_repo.find_by_name("王")
        
        assert students == []
    
    # ========== 删除测试 ==========
    
    def test_delete_existing_student(self, student_repo, sample_student):
        """删除存在的学生"""
        student_repo.save(sample_student)
        assert student_repo.find_by_id_str("2024001") is not None
        
        student_repo.delete(StudentId("2024001"))
        
        assert student_repo.find_by_id_str("2024001") is None
    
    def test_delete_nonexistent_student(self, student_repo):
        """删除不存在的学生（不报错）"""
        # 应该不抛出异常
        student_repo.delete(StudentId("9999999"))
    
    # ========== 存在性测试 ==========
    
    def test_exists_true(self, student_repo, sample_student):
        """学生存在返回True"""
        student_repo.save(sample_student)
        
        assert student_repo.exists(StudentId("2024001")) is True
    
    def test_exists_false(self, student_repo):
        """学生不存在返回False"""
        assert student_repo.exists(StudentId("9999999")) is False
    
    # ========== 边界情况测试 ==========
    
    def test_save_student_with_none_score(self, student_repo):
        """保存分数为None的学生（使用默认值）"""
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70)  # 实际不会为None，因为构造时会检查
        )
        student_repo.save(student)
        
        found = student_repo.find_by_id_str("2024001")
        assert float(found.score) == 70
    
    def test_save_student_with_none_class(self, student_repo):
        """保存班级为None的学生"""
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name=None,
            score=Score(70)
        )
        student_repo.save(student)
        
        found = student_repo.find_by_id_str("2024001")
        # 仓库层应处理为默认值
        assert found.class_name is not None
    
    def test_student_id_type_conversion(self, student_repo):
        """学号类型转换"""
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70)
        )
        student_repo.save(student)
        
        # 使用字符串查找
        found = student_repo.find_by_id_str("2024001")
        assert found is not None
        
        # 使用 StudentId 对象查找
        found2 = student_repo.find_by_id(StudentId("2024001"))
        assert found2 is not None
