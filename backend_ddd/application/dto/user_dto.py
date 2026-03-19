"""
用户数据传输对象
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CreateUserDTO:
    """创建用户DTO"""
    username: str
    password: str
    name: str
    role: str  # 'admin' 或 'teacher'
    assigned_classes: Optional[List[str]] = None


@dataclass
class UpdateUserDTO:
    """更新用户DTO"""
    name: Optional[str] = None
    role: Optional[str] = None
    assigned_classes: Optional[List[str]] = None
    status: Optional[str] = None


@dataclass
class UserResponseDTO:
    """用户响应DTO"""
    id: int
    username: str
    name: str
    role: str
    assigned_classes: List[str]
    status: str
    last_login_at: Optional[str]
