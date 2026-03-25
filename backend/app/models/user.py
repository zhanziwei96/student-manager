"""
用户模型 - SQLModel 版本
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field
from pydantic import field_validator
import json

from app.models.constants import UserRole, UserRoleConst


class UserBase(SQLModel):
    """用户基础属性"""
    username: str = Field(..., description="用户名")
    name: str = Field(..., description="姓名")
    role: str = Field(default=UserRoleConst.TEACHER, description="角色")
    assigned_classes: str = Field(default="[]", description="负责班级列表（JSON字符串）")
    is_active: bool = Field(default=True, description="是否激活")
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """验证角色值是否合法"""
        if not UserRoleConst.is_valid(v):
            raise ValueError(f"无效的角色: {v}, 必须是 {UserRoleConst.all()}")
        return v.lower()
    
    def get_assigned_classes(self) -> List[str]:
        """获取班级列表（从JSON解析）"""
        try:
            return json.loads(self.assigned_classes) if self.assigned_classes else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_assigned_classes(self, classes: List[str]) -> None:
        """设置班级列表（转为JSON）"""
        self.assigned_classes = json.dumps(classes, ensure_ascii=False) if classes else "[]"


class User(UserBase, table=True):
    """用户表模型"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str = Field(..., description="密码哈希 (bcrypt)")
    # SEC-003 DEPRECATED: bcrypt 已内置盐值，此字段不再使用，保留仅用于兼容旧数据
    salt: Optional[str] = Field(default=None, description="[DEPRECATED] 密码盐值 - bcrypt已内置，此字段将在未来版本移除")
    login_fail_count: int = Field(default=0, description="登录失败次数")
    locked_until: Optional[datetime] = Field(default=None, description="锁定截止时间")
    last_login_ip: Optional[str] = Field(default=None, description="最后登录IP")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    version: int = Field(default=1, description="乐观锁版本号")
    
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == UserRoleConst.ADMIN
    
    def is_teacher(self) -> bool:
        """检查是否为教师"""
        return self.role == UserRoleConst.TEACHER


class UserCreate(SQLModel):
    """创建用户请求"""
    username: str
    password: str
    name: str
    role: UserRole = UserRoleConst.TEACHER
    assigned_classes: List[str] = []


class UserUpdate(SQLModel):
    """更新用户请求"""
    name: Optional[str] = None
    role: Optional[UserRole] = None
    assigned_classes: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserResponse(SQLModel):
    """用户响应"""
    id: int
    username: str
    name: str
    role: UserRole
    assigned_classes: List[str]
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
