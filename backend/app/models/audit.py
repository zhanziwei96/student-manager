"""
审计日志模型 - SQLModel 版本
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger
from sqlmodel import SQLModel, Field
from app.core.timezone import get_now


class AuditLog(SQLModel, table=True):
    """审计日志表"""
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, sa_type=BigInteger, description="用户ID", index=True)
    user_name: Optional[str] = Field(default=None, description="用户名")
    role: Optional[str] = Field(default=None, description="角色")
    action: Optional[str] = Field(default=None, description="操作", index=True)
    resource: Optional[str] = Field(default=None, description="资源")
    resource_id: Optional[str] = Field(default=None, description="资源ID")
    method: Optional[str] = Field(default=None, description="HTTP方法")
    params: Optional[str] = Field(default=None, description="请求参数")
    ip_address: Optional[str] = Field(default=None, description="IP地址")
    user_agent: Optional[str] = Field(default=None, description="UserAgent")
    status_code: Optional[int] = Field(default=None, description="状态码")
    response_msg: Optional[str] = Field(default=None, description="响应消息")
    semester_id: Optional[int] = Field(
        default=None, foreign_key="semesters.id", index=True,
        description="学期ID（FK，按学期审计）",
    )
    created_at: datetime = Field(default_factory=get_now, description="创建时间", index=True)


class SecurityAlert(SQLModel, table=True):
    """安全告警表"""
    __tablename__ = "security_alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    alert_type: Optional[str] = Field(default=None, description="告警类型", index=True)
    severity: Optional[str] = Field(default=None, description="严重级别")
    description: Optional[str] = Field(default=None, description="描述")
    related_user_id: Optional[int] = Field(default=None, sa_type=BigInteger, description="相关用户ID")
    related_ip: Optional[str] = Field(default=None, description="相关IP")
    is_resolved: bool = Field(default=False, description="是否已解决", index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
