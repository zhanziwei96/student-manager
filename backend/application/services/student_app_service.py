"""
学生应用服务
协调学生相关的用例
"""
import logging
from typing import List, Optional
from domain.entities.student import Student
from domain.entities.score_log import ScoreLog
from domain.value_objects.student_id import StudentId
from domain.value_objects.score import Score
from domain.value_objects.password import Password
from domain.repositories.student_repository import StudentRepository
from application.dto.student_dto import (
    CreateStudentDTO, 
    UpdateScoreDTO, 
    StudentResponseDTO
)
from infrastructure.config import ScoreConfig


class StudentAppService:
    """学生应用服务"""
    
    def __init__(self, student_repo: StudentRepository, score_log_repo=None):
        self.student_repo = student_repo
        self.score_log_repo = score_log_repo  # 可选的日志仓储
    
    def create_student(self, dto: CreateStudentDTO) -> StudentResponseDTO:
        """
        创建学生用例
        
        Args:
            dto: 创建学生DTO
            
        Returns:
            创建的学生响应DTO
            
        Raises:
            ValueError: 学号已存在
        """
        student_id = StudentId(dto.student_id)
        
        # 检查学号是否已存在
        if self.student_repo.exists(student_id):
            raise ValueError(f"学号 {dto.student_id} 已存在")
        
        # 创建领域实体
        student = Student(
            student_id=student_id,
            name=dto.name,
            class_name=dto.class_name or "未分班",
            score=Score(ScoreConfig.DEFAULT_SCORE)  # 使用配置默认值
        )
        
        # 保存
        self.student_repo.save(student)
        
        # 设置初始密码（使用领域层Password值对象）
        password = Password.create(str(student_id))
        self.student_repo.save_password(str(student_id), password.hash, password.salt)
        
        # 返回DTO
        return self._to_response_dto(student)
    
    def update_score(self, dto: UpdateScoreDTO) -> StudentResponseDTO:
        """
        更新学生分数用例
        
        Args:
            dto: 更新分数DTO
            
        Returns:
            更新后的学生响应DTO
        """
        student_id = StudentId(dto.student_id)
        
        # 查找实体
        student = self.student_repo.find_by_id(student_id)
        if not student:
            raise ValueError(f"学生 {dto.student_id} 不存在")
        
        # 调用领域逻辑
        student.change_score(dto.delta, dto.reason, dto.operator)
        
        # 保存修改
        self.student_repo.save(student)
        
        # 记录审计日志
        if self.score_log_repo:
            log = ScoreLog(
                student_id=str(student.student_id),
                student_name=student.name,
                class_name=student.class_name,
                delta=dto.delta,
                reason=dto.reason,
                operator_name=dto.operator or "系统"
            )
            self.score_log_repo.save(log)
        
        # 处理领域事件
        events = student.events
        logger = logging.getLogger(__name__)
        for event in events:
            logger.info(f"[Event] Score changed: {event}")
        student.clear_events()
        
        return self._to_response_dto(student)
    
    def get_student_by_id(self, student_id: str) -> Optional[StudentResponseDTO]:
        """根据学号获取学生"""
        student = self.student_repo.find_by_id(StudentId(student_id))
        if student:
            return self._to_response_dto(student)
        return None
    
    def get_all_students(self) -> List[StudentResponseDTO]:
        """获取所有学生"""
        students = self.student_repo.find_all()
        return [self._to_response_dto(s) for s in students]
    
    def get_students_by_class(self, class_name: str) -> List[StudentResponseDTO]:
        """根据班级获取学生"""
        students = self.student_repo.find_by_class(class_name)
        return [self._to_response_dto(s) for s in students]
    
    def delete_student(self, student_id: str) -> None:
        """删除学生"""
        self.student_repo.delete(StudentId(student_id))
    
    def reset_student_password(self, student_id: str, new_password: str) -> bool:
        """重置学生密码
        
        Args:
            student_id: 学号
            new_password: 新密码（明文）
            
        Returns:
            是否成功
        """
        # 检查学生是否存在
        if not self.student_repo.exists(StudentId(student_id)):
            return False
        
        # 使用领域层Password值对象创建新密码
        password = Password.create(new_password)
        
        # 持久化（仓储只负责数据存取）
        self.student_repo.save_password(student_id, password.hash, password.salt)
        
        return True
    
    def verify_student_password(self, student_id: str, password: str) -> bool:
        """验证学生密码
        
        Args:
            student_id: 学号
            password: 明文密码
            
        Returns:
            是否匹配
        """
        # 从仓储获取密码信息（纯数据）
        password_info = self.student_repo.find_password(student_id)
        if not password_info:
            return False
        
        # 使用领域层Password值对象验证
        stored_hash, salt = password_info
        password_obj = Password.from_hash(stored_hash, salt)
        return password_obj.verify(password)
    
    def _to_response_dto(self, student: Student) -> StudentResponseDTO:
        """将领域实体转换为响应DTO"""
        return StudentResponseDTO(
            student_id=str(student.student_id),
            name=student.name,
            class_name=student.class_name,
            score=float(student.score)
        )
