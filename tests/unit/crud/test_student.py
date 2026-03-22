"""
学生 CRUD 单元测试
"""
import pytest
from sqlmodel import Session
from app.crud import (
    get_student, get_students, get_students_by_class,
    create_student, update_student_score, delete_student, get_all_classes
)
from app.models import Student, ScoreLog


class TestStudentCRUD:
    """测试学生 CRUD 操作"""
    
    def test_create_student(self, session: Session):
        """测试创建学生"""
        student = create_student(
            session,
            student_id="S001",
            name="张三",
            class_name="软件1班",
            score=85.0
        )
        
        assert student.student_id == "S001"
        assert student.name == "张三"
        assert student.class_name == "软件1班"
        assert student.score == 85.0
    
    def test_get_student(self, session: Session):
        """测试获取学生"""
        # 先创建学生
        create_student(session, "S002", "李四", "软件1班")
        
        # 查询学生
        student = get_student(session, "S002")
        assert student is not None
        assert student.name == "李四"
    
    def test_get_student_not_found(self, session: Session):
        """测试获取不存在的学生"""
        student = get_student(session, "NOT_EXIST")
        assert student is None
    
    def test_get_students(self, session: Session):
        """测试获取所有学生"""
        create_student(session, "S003", "王五", "软件1班")
        create_student(session, "S004", "赵六", "软件2班")
        
        students = get_students(session)
        assert len(students) == 2
    
    def test_get_students_by_class(self, session: Session):
        """测试按班级获取学生"""
        create_student(session, "S005", "张三", "软件1班")
        create_student(session, "S006", "李四", "软件2班")
        create_student(session, "S007", "王五", "软件1班")
        
        students = get_students_by_class(session, "软件1班")
        assert len(students) == 2
        assert all(s.class_name == "软件1班" for s in students)
    
    def test_update_student_score(self, session: Session):
        """测试更新学生分数"""
        student = create_student(session, "S008", "张三", "软件1班", 80.0)
        
        updated = update_student_score(
            session, "S008", delta=5.0, reason="回答问题", operator="老师"
        )
        
        assert updated is not None
        assert updated.score == 85.0
        
        # 验证分数日志
        from sqlmodel import select
        logs = session.exec(select(ScoreLog).where(ScoreLog.student_id == "S008")).all()
        assert len(logs) == 1
        assert logs[0].delta == 5.0
        assert logs[0].reason == "回答问题"
    
    def test_update_student_score_negative(self, session: Session):
        """测试扣分"""
        student = create_student(session, "S009", "张三", "软件1班", 80.0)
        
        updated = update_student_score(
            session, "S009", delta=-5.0, reason="迟到", operator="老师"
        )
        
        assert updated.score == 75.0
    
    def test_delete_student(self, session: Session):
        """测试删除学生"""
        create_student(session, "S010", "张三", "软件1班")
        
        success = delete_student(session, "S010")
        assert success is True
        
        # 确认已删除
        student = get_student(session, "S010")
        assert student is None
    
    def test_delete_student_not_found(self, session: Session):
        """测试删除不存在的学生"""
        success = delete_student(session, "NOT_EXIST")
        assert success is False
    
    def test_get_all_classes(self, session: Session):
        """测试获取所有班级"""
        create_student(session, "S011", "张三", "软件1班")
        create_student(session, "S012", "李四", "软件2班")
        create_student(session, "S013", "王五", "软件1班")
        
        classes = get_all_classes(session)
        assert "软件1班" in classes
        assert "软件2班" in classes
