"""
用户实体
管理员或老师
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
from domain.value_objects.password import Password


class UserRole(Enum):
    """用户角色"""
    ADMIN = "admin"
    TEACHER = "teacher"


class UserStatus(Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


@dataclass
class User:
    """用户实体"""
    username: str
    name: str
    password: Password
    role: UserRole
    assigned_classes: list = field(default_factory=list)  # 绑定的班级列表
    status: UserStatus = UserStatus.ACTIVE
    login_fail_count: int = 0
    locked_until: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None
    
    def is_admin(self) -> bool:
        """是否是管理员"""
        return self.role == UserRole.ADMIN
    
    def is_active(self) -> bool:
        """是否激活"""
        return self.status == UserStatus.ACTIVE
    
    def is_locked(self) -> bool:
        """是否被锁定"""
        if self.status == UserStatus.LOCKED and self.locked_until:
            if datetime.now() < self.locked_until:
                return True
            # 锁定已过期，自动解锁
            self.unlock()
        return False
    
    def can_access_class(self, class_name: str) -> bool:
        """是否有权限访问指定班级"""
        if self.is_admin():
            return True
        return class_name in self.assigned_classes
    
    def record_login_failure(self) -> None:
        """记录登录失败"""
        self.login_fail_count += 1
        if self.login_fail_count >= 5:
            self.lock()
    
    def lock(self, minutes: int = 15) -> None:
        """锁定账号"""
        self.status = UserStatus.LOCKED
        self.locked_until = datetime.now() + timedelta(minutes=minutes)
    
    def unlock(self) -> None:
        """解锁账号"""
        self.status = UserStatus.ACTIVE
        self.locked_until = None
        self.login_fail_count = 0
    
    def record_login_success(self, ip: str) -> None:
        """记录登录成功"""
        self.login_fail_count = 0
        self.last_login_ip = ip
        self.last_login_at = datetime.now()
    
    def assign_class(self, class_name: str) -> None:
        """绑定班级"""
        if class_name not in self.assigned_classes:
            self.assigned_classes.append(class_name)
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'role': self.role.value,
            'assigned_classes': self.assigned_classes,
            'status': self.status.value,
            'last_login_ip': self.last_login_ip,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat()
        }
        return data
