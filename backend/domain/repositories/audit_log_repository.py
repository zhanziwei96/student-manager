"""
审计日志仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from domain.entities.audit_log import AuditLog
# Domain 层硬编码默认值（不依赖 Infrastructure 层）
DEFAULT_MAX_AUDIT_LOGS = 100


class AuditLogRepository(ABC):
    """审计日志仓储接口"""
    
    @abstractmethod
    def save(self, log: AuditLog) -> AuditLog:
        """保存审计日志"""
        pass
    
    @abstractmethod
    def find_by_id(self, log_id: int) -> Optional[AuditLog]:
        """根据ID查找日志"""
        pass
    
    @abstractmethod
    def find_by_filters(
        self,
        user_id: Optional[int] = None,
        user_name: Optional[str] = None,
        role: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        ip_address: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = DEFAULT_MAX_AUDIT_LOGS,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        条件查询日志
        
        Args:
            user_id: 用户ID
            user_name: 用户名（模糊匹配）
            role: 角色
            action: 操作类型
            resource: 资源
            method: HTTP方法
            status_code: 状态码
            ip_address: IP地址（模糊匹配）
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制数量
            offset: 偏移量
        """
        pass
    
    @abstractmethod
    def get_statistics(
        self,
        days: int = 7,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取审计统计
        
        Args:
            days: 统计天数
            user_id: 指定用户（None则统计全部）
            
        Returns:
            统计信息字典
        """
        pass
    
    @abstractmethod
    def count_by_filters(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> int:
        """根据条件统计日志数量"""
        pass
