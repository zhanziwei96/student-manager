"""
审计日志实体
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class AuditLog:
    """
    审计日志实体
    
    Attributes:
        id: 日志ID
        user_id: 操作用户ID
        user_name: 用户姓名
        role: 用户角色
        action: 操作类型 (read/create/update/delete/login/logout)
        resource: 访问的资源 (students/checkin/score等)
        resource_id: 资源标识
        method: HTTP方法
        params: 请求参数 (JSON字符串)
        ip_address: 客户端IP
        user_agent: 浏览器标识
        status_code: 响应状态码
        response_msg: 响应消息
        created_at: 创建时间
    """
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    role: Optional[str] = None
    action: str = ""
    resource: str = ""
    resource_id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    response_msg: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'role': self.role,
            'action': self.action,
            'resource': self.resource,
            'resource_id': self.resource_id,
            'method': self.method,
            'params': self.params,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status_code': self.status_code,
            'response_msg': self.response_msg,
            'created_at': self.created_at
        }
