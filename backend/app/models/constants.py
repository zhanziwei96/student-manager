"""
系统常量定义
"""
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# ==================== 版本信息 ====================
VERSION: str = "2.0.0"


# ==================== 环境类型 ====================
class EnvConst:
    """环境类型常量"""
    DEVELOPMENT: str = "development"
    TESTING: str = "testing"
    PRODUCTION: str = "production"


# ==================== 用户角色 ====================
# 使用 Literal 提供类型提示
UserRole = Literal["admin", "teacher", "student"]


class UserRoleConst:
    """用户角色常量"""
    ADMIN: str = "admin"
    TEACHER: str = "teacher"
    STUDENT: str = "student"
    
    ALL = [ADMIN, TEACHER, STUDENT]
    
    @classmethod
    def is_valid(cls, role: str) -> bool:
        """验证角色是否合法"""
        return role in cls.ALL
    
    @classmethod
    def all(cls):
        """获取所有合法角色"""
        return cls.ALL


# ==================== 用户状态 ====================
UserStatus = Literal["active", "inactive", "locked"]


class UserStatusConst:
    """用户状态常量"""
    ACTIVE: str = "active"
    INACTIVE: str = "inactive"
    LOCKED: str = "locked"


# ==================== Session Key 常量 ====================
class SessionKeyConst:
    """Session 存储键名常量"""
    USER_ID: str = "user_id"
    USERNAME: str = "username"
    ROLE: str = "role"
    IS_ADMIN: str = "is_admin"


# ==================== API 响应键名 ====================
class ApiResponseConst:
    """API 响应 JSON 键名常量"""
    SUCCESS: str = "success"
    DATA: str = "data"
    MESSAGE: str = "message"


# ==================== API 响应模型 ====================
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """通用 API 响应模型 - P1 修复：标准化响应结构"""
    success: bool = Field(..., description="请求是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")


class ApiSuccessResponse(BaseModel):
    """成功响应模型（无数据）"""
    success: bool = True
    message: Optional[str] = None


class ApiListResponse(BaseModel, Generic[T]):
    """列表数据响应模型"""
    success: bool = True
    data: list[T] = Field(default_factory=list, description="列表数据")


class ApiErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="详细错误信息")


# ==================== 路由前缀 ====================
class RoutePrefixConst:
    """API 路由前缀常量"""
    API: str = "/api"
    ADMIN: str = "/api/admin"


# ==================== 业务消息常量 ====================
class MessageConst:
    """API 响应消息常量"""
    # 登录相关
    LOGIN_SUCCESS: str = "登录成功"
    LOGOUT_SUCCESS: str = "登出成功"
    PASSWORD_CHANGED: str = "密码修改成功"
    OLD_PASSWORD_WRONG: str = "旧密码错误"
    
    # 用户相关
    USER_CREATED: str = "用户创建成功"
    USER_UPDATED: str = "用户更新成功"
    USER_DELETED: str = "用户删除成功"
    PASSWORD_RESET: str = "密码重置成功"
    
    # 学生相关
    STUDENT_CREATED: str = "学生添加成功"
    STUDENT_SCORE_UPDATED: str = "分数更新成功"
    STUDENT_DELETED: str = "学生删除成功"
    IMPORT_PENDING: str = "导入功能待实现"
    
    # 签到相关
    CLASS_STARTED: str = "上课开始"
    CLASS_ENDED: str = "上课结束"
    CHECKIN_SUCCESS: str = "签到成功"


# ==================== 签到类型 ====================
CheckinType = Literal["self", "manual"]


class CheckinTypeConst:
    """签到类型常量"""
    SELF: str = "self"
    MANUAL: str = "manual"


# ==================== 分数变动类型 ====================
ScoreChangeType = Literal["bonus", "penalty", "adjust"]


class ScoreChangeTypeConst:
    """分数变动类型常量"""
    BONUS: str = "bonus"
    PENALTY: str = "penalty"
    ADJUST: str = "adjust"


# ==================== 系统状态 ====================
class SystemStatusConst:
    """系统状态常量"""
    HEALTHY: str = "healthy"
