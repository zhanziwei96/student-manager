"""
学生仓储接口
领域层只定义接口，实现由基础设施层提供
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.student import Student
from domain.value_objects.student_id import StudentId


class StudentRepository(ABC):
    """学生仓储接口"""
    
    @abstractmethod
    def find_by_id(self, student_id: StudentId) -> Optional[Student]:
        """根据学号查找学生"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Student]:
        """查找所有学生"""
        pass
    
    @abstractmethod
    def find_by_class(self, class_name: str) -> List[Student]:
        """根据班级查找学生"""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> List[Student]:
        """根据姓名查找学生（模糊匹配）"""
        pass
    
    @abstractmethod
    def save(self, student: Student) -> None:
        """保存学生（新增或更新）"""
        pass
    
    @abstractmethod
    def delete(self, student_id: StudentId) -> None:
        """删除学生"""
        pass
    
    @abstractmethod
    def exists(self, student_id: StudentId) -> bool:
        """检查学生是否存在"""
        pass
    
    # 学生账号相关（数据持久化，业务逻辑在领域层）
    @abstractmethod
    def save_password(self, student_id: str, password_hash: str, salt: str) -> None:
        """保存学生密码（纯数据操作）
        
        Args:
            student_id: 学号
            password_hash: 密码哈希值
            salt: 盐值
        """
        pass
    
    @abstractmethod
    def find_password(self, student_id: str) -> Optional[tuple]:
        """查找学生密码信息
        
        Args:
            student_id: 学号
            
        Returns:
            (password_hash, salt) 元组，或 None
        """
        pass
