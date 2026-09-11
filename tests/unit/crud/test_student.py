"""
学生 CRUD 单元测试
"""
import pytest
from sqlmodel import Session
from app.crud import (
    get_student, get_students, get_students_by_class, get_students_by_classes,
    create_student, delete_student, get_all_classes,
    reset_student_password,
)
from app.models import Student


class TestStudentCRUD:
    """测试学生 CRUD 操作"""
    
    def test_create_student(self, session: Session, seed_refs):
        """测试创建学生"""
        student = create_student(
            session,
            student_id="S001",
            name="张三",
            class_id=seed_refs["一班"]
        )

        assert student.student_id == "S001"
        assert student.name == "张三"
        assert student.class_id == seed_refs["一班"]

    def test_get_student(self, session: Session, seed_refs):
        """测试获取学生"""
        # 先创建学生
        create_student(session, "S002", "李四", seed_refs["一班"])
        
        # 查询学生
        student = get_student(session, "S002")
        assert student is not None
        assert student.name == "李四"
    
    def test_get_student_not_found(self, session: Session):
        """测试获取不存在的学生"""
        student = get_student(session, "NOT_EXIST")
        assert student is None
    
    def test_get_students(self, session: Session, seed_refs):
        """测试获取所有学生"""
        create_student(session, "S003", "王五", seed_refs["一班"])
        create_student(session, "S004", "赵六", seed_refs["二班"])

        students = get_students(session)
        assert len(students) == 2

    def test_get_students_by_class(self, session: Session, seed_refs):
        """测试按班级获取学生"""
        create_student(session, "S005", "张三", seed_refs["一班"])
        create_student(session, "S006", "李四", seed_refs["二班"])
        create_student(session, "S007", "王五", seed_refs["一班"])

        students = get_students_by_class(session, seed_refs["一班"])
        assert len(students) == 2
        assert all(s.class_id == seed_refs["一班"] for s in students)

    def test_delete_student(self, session: Session, seed_refs):
        """测试删除学生"""
        create_student(session, "S010", "张三", seed_refs["一班"])
        
        success = delete_student(session, "S010")
        assert success is True
        
        # 确认已删除
        student = get_student(session, "S010")
        assert student is None
    
    def test_delete_student_not_found(self, session: Session):
        """测试删除不存在的学生"""
        success = delete_student(session, "NOT_EXIST")
        assert success is False
    
    def test_get_all_classes(self, session: Session, seed_refs):
        """测试获取所有班级"""
        create_student(session, "S011", "张三", seed_refs["一班"])
        create_student(session, "S012", "李四", seed_refs["二班"])
        create_student(session, "S013", "王五", seed_refs["一班"])

        classes = get_all_classes(session)
        assert "一班" in classes
        assert "二班" in classes

    def test_reset_student_password(self, session: Session, seed_refs):
        """测试重置学生密码 - SEC-003: 简化密码哈希接口"""
        student = create_student(session, "S014", "张三", seed_refs["一班"])
        
        # 重置密码
        updated = reset_student_password(
            session, "S014", 
            password_hash="new_hash"
        )
        
        assert updated is not None
        assert updated.password_hash == "new_hash"
    
    def test_reset_student_password_not_found(self, session: Session):
        """测试重置不存在学生的密码 - SEC-003: 简化密码哈希接口"""
        result = reset_student_password(
            session, "NOT_EXIST",
            password_hash="new_hash"
        )
        
        assert result is None
    
class TestStudentPagination:
    """学生列表分页（limit/offset）与总数统计"""

    def test_get_students_with_limit_offset(self, session: Session, seed_refs):
        """limit/offset 分页返回正确切片"""
        for i in range(1, 8):
            create_student(session, f"P{i:03d}", f"学生{i}", seed_refs["一班"])

        page1 = get_students(session, limit=3, offset=0)
        page2 = get_students(session, limit=3, offset=3)
        page3 = get_students(session, limit=3, offset=6)

        assert [s.student_id for s in page1] == ["P001", "P002", "P003"]
        assert [s.student_id for s in page2] == ["P004", "P005", "P006"]
        assert [s.student_id for s in page3] == ["P007"]

    def test_get_students_without_limit_returns_all(self, session: Session, seed_refs):
        """不传 limit 时返回全部（向后兼容）"""
        for i in range(1, 6):
            create_student(session, f"P{i:03d}", f"学生{i}", seed_refs["一班"])

        students = get_students(session)
        assert len(students) == 5

    def test_get_students_pagination_with_class_filter(self, session: Session, seed_refs):
        """分页与班级筛选同时生效"""
        for i in range(1, 6):
            create_student(session, f"P{i:03d}", f"学生{i}", seed_refs["一班"])
        for i in range(6, 9):
            create_student(session, f"P{i:03d}", f"学生{i}", seed_refs["二班"])

        students = get_students(session, class_id=seed_refs["二班"], limit=2, offset=1)
        assert [s.student_id for s in students] == ["P007", "P008"]

    def test_get_students_by_class_with_limit_offset(self, session: Session, seed_refs):
        """get_students_by_class 支持分页"""
        for i in range(1, 6):
            create_student(session, f"P{i:03d}", f"学生{i}", seed_refs["一班"])

        students = get_students_by_class(session, seed_refs["一班"], limit=2, offset=2)
        assert [s.student_id for s in students] == ["P003", "P004"]

    def test_get_students_by_classes_with_limit_offset(self, session: Session, seed_refs):
        """get_students_by_classes 支持分页（教师多班级场景）"""
        create_student(session, "P001", "学生1", seed_refs["一班"])
        create_student(session, "P002", "学生2", seed_refs["二班"])
        create_student(session, "P003", "学生3", seed_refs["一班"])
        create_student(session, "P004", "学生4", seed_refs["三班"])

        students = get_students_by_classes(
            session, [seed_refs["一班"], seed_refs["二班"]], limit=2, offset=1
        )
        assert [s.student_id for s in students] == ["P002", "P003"]

    def test_count_students_filtered(self, session: Session, seed_refs):
        """count_students_filtered 按条件统计总数"""
        from app.crud import count_students_filtered

        for i in range(1, 4):
            create_student(session, f"P{i:03d}", f"学生{i}", seed_refs["一班"])
        for i in range(4, 7):
            create_student(session, f"P{i:03d}", f"学生{i}", seed_refs["二班"])

        assert count_students_filtered(session) == 6
        assert count_students_filtered(session, class_id=seed_refs["一班"]) == 3
        assert count_students_filtered(
            session, class_ids=[seed_refs["一班"], seed_refs["二班"]]
        ) == 6
        assert count_students_filtered(session, class_ids=[]) == 0

    def test_count_students_filtered_excludes_disabled(self, session: Session, seed_refs):
        """count_students_filtered 默认排除已禁用学生"""
        from app.crud import count_students_filtered

        student = create_student(session, "P001", "学生1", seed_refs["一班"])
        create_student(session, "P002", "学生2", seed_refs["一班"])
        student.is_account_enabled = False
        session.add(student)
        session.commit()

        assert count_students_filtered(session) == 1
        assert count_students_filtered(session, include_disabled=True) == 2
