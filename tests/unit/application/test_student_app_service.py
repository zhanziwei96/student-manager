"""
学生应用服务单元测试
使用 Mock Repository 验证用例编排逻辑
"""
import pytest
from datetime import datetime

from domain.entities.student import Student
from domain.entities.score_log import ScoreLog
from domain.value_objects.student_id import StudentId
from domain.value_objects.score import Score
from application.dto.student_dto import CreateStudentDTO, UpdateScoreDTO


class TestStudentAppService:
    """学生应用服务测试类"""
    
    def test_create_student_success(self, student_app_service, mock_student_repo):
        """测试成功创建学生"""
        # Arrange
        dto = CreateStudentDTO(
            student_id="2024001",
            name="张三",
            class_name="软件1班"
        )
        
        # Act
        result = student_app_service.create_student(dto)
        
        # Assert
        assert result is not None
        assert result.student_id == "2024001"
        assert result.name == "张三"
        assert result.class_name == "软件1班"
        assert result.score == 70.0  # 默认分数
        
        # 验证仓储中保存了实体
        saved = mock_student_repo.find_by_id_str("2024001")
        assert saved is not None
        assert saved.name == "张三"
    
    def test_create_student_duplicate_id(self, student_app_service, mock_student_repo):
        """测试创建重复学号学生失败"""
        # Arrange - 先创建一个学生
        dto = CreateStudentDTO(student_id="2024001", name="张三", class_name="软件1班")
        student_app_service.create_student(dto)
        
        # Act & Assert - 再次创建相同学号应抛出异常
        with pytest.raises(ValueError) as exc_info:
            student_app_service.create_student(dto)
        assert "已存在" in str(exc_info.value)
    
    def test_create_student_default_class(self, student_app_service, mock_student_repo):
        """测试创建学生时默认班级"""
        # Arrange
        dto = CreateStudentDTO(student_id="2024001", name="张三")  # 不指定班级
        
        # Act
        result = student_app_service.create_student(dto)
        
        # Assert
        assert result.class_name == "未分班"
    
    def test_get_student_by_id_exists(self, student_app_service, mock_student_repo):
        """测试获取存在的学生"""
        # Arrange
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(80.0)
        )
        mock_student_repo.save(student)
        
        # Act
        result = student_app_service.get_student_by_id("2024001")
        
        # Assert
        assert result is not None
        assert result.student_id == "2024001"
        assert result.name == "张三"
        assert result.score == 80.0
    
    def test_get_student_by_id_not_exists(self, student_app_service):
        """测试获取不存在的学生"""
        # Act
        result = student_app_service.get_student_by_id("9999999")
        
        # Assert
        assert result is None
    
    def test_get_all_students(self, student_app_service, mock_student_repo):
        """测试获取所有学生"""
        # Arrange
        mock_student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(70)))
        mock_student_repo.save(Student(StudentId("2024002"), "李四", "软件1班", Score(80)))
        
        # Act
        results = student_app_service.get_all_students()
        
        # Assert
        assert len(results) == 2
        student_ids = [r.student_id for r in results]
        assert "2024001" in student_ids
        assert "2024002" in student_ids
    
    def test_get_students_by_class(self, student_app_service, mock_student_repo):
        """测试按班级获取学生"""
        # Arrange
        mock_student_repo.save(Student(StudentId("2024001"), "张三", "软件1班", Score(70)))
        mock_student_repo.save(Student(StudentId("2024002"), "李四", "软件1班", Score(80)))
        mock_student_repo.save(Student(StudentId("2024003"), "王五", "软件2班", Score(90)))
        
        # Act
        results = student_app_service.get_students_by_class("软件1班")
        
        # Assert
        assert len(results) == 2
        assert all(r.class_name == "软件1班" for r in results)
    
    def test_update_score_success(self, student_app_service, mock_student_repo):
        """测试成功更新分数"""
        # Arrange
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70.0)
        )
        mock_student_repo.save(student)
        
        dto = UpdateScoreDTO(
            student_id="2024001",
            delta=10.0,
            reason="课堂表现优秀",
            operator="王老师"
        )
        
        # Act
        result = student_app_service.update_score(dto)
        
        # Assert
        assert result.score == 80.0
        
        # 验证仓储中的实体已更新
        saved = mock_student_repo.find_by_id_str("2024001")
        assert float(saved.score) == 80.0
    
    def test_update_score_student_not_exists(self, student_app_service):
        """测试更新不存在学生的分数"""
        # Arrange
        dto = UpdateScoreDTO(
            student_id="9999999",
            delta=10.0,
            reason="课堂表现优秀",
            operator="王老师"
        )
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            student_app_service.update_score(dto)
        assert "不存在" in str(exc_info.value)
    
    def test_update_score_creates_log(self, student_app_service, mock_student_repo, mock_score_log_repo):
        """测试更新分数时创建审计日志"""
        # Arrange
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70.0)
        )
        mock_student_repo.save(student)
        
        dto = UpdateScoreDTO(
            student_id="2024001",
            delta=10.0,
            reason="课堂表现优秀",
            operator="王老师"
        )
        
        # Act
        student_app_service.update_score(dto)
        
        # Assert - 验证日志已创建
        logs = mock_score_log_repo.find_by_student("2024001")
        assert len(logs) == 1
        assert logs[0].delta == 10.0
        assert logs[0].reason == "课堂表现优秀"
        assert logs[0].operator_name == "王老师"
    
    def test_update_score_without_log_repo(self, mock_student_repo):
        """测试没有日志仓储时也能正常更新分数"""
        # Arrange - 不传入 score_log_repo
        from application.services.student_app_service import StudentAppService
        service = StudentAppService(mock_student_repo, None)
        
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(70.0)
        )
        mock_student_repo.save(student)
        
        dto = UpdateScoreDTO(
            student_id="2024001",
            delta=10.0,
            reason="课堂表现优秀",
            operator="王老师"
        )
        
        # Act - 不应抛出异常
        result = service.update_score(dto)
        
        # Assert
        assert result.score == 80.0
    
    def test_delete_student(self, student_app_service, mock_student_repo):
        """测试删除学生"""
        # Arrange
        student = Student(StudentId("2024001"), "张三", "软件1班", Score(70))
        mock_student_repo.save(student)
        assert mock_student_repo.find_by_id_str("2024001") is not None
        
        # Act
        student_app_service.delete_student("2024001")
        
        # Assert
        assert mock_student_repo.find_by_id_str("2024001") is None
    
    def test_update_score_negative_delta(self, student_app_service, mock_student_repo):
        """测试扣分操作"""
        # Arrange
        student = Student(
            student_id=StudentId("2024001"),
            name="张三",
            class_name="软件1班",
            score=Score(80.0)
        )
        mock_student_repo.save(student)
        
        dto = UpdateScoreDTO(
            student_id="2024001",
            delta=-5.0,
            reason="迟到",
            operator="李老师"
        )
        
        # Act
        result = student_app_service.update_score(dto)
        
        # Assert
        assert result.score == 75.0
