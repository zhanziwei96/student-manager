"""
用户仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.user import User


class UserRepository(ABC):
    """用户仓储接口"""
    
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """根据ID查找用户"""
        pass
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找用户"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[User]:
        """查找所有用户"""
        pass
    
    @abstractmethod
    def find_by_class(self, class_name: str) -> List[User]:
        """查找绑定指定班级的用户"""
        pass
    
    @abstractmethod
    def save(self, user: User) -> None:
        """保存用户"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> None:
        """删除用户"""
        pass
    
    @abstractmethod
    def exists(self, username: str) -> bool:
        """检查用户名是否已存在"""
        pass
