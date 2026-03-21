"""
审计日志应用服务
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from domain.entities.audit_log import AuditLog
from domain.repositories.audit_log_repository import AuditLogRepository
from infrastructure.config import PaginationConfig


class AuditLogAppService:
    """审计日志应用服务"""
    
    def __init__(self, audit_log_repo: AuditLogRepository):
        self._repo = audit_log_repo
    
    def create_log(
        self,
        action: str,
        resource: str,
        user_id: Optional[int] = None,
        user_name: Optional[str] = None,
        role: Optional[str] = None,
        resource_id: Optional[str] = None,
        method: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: Optional[int] = None,
        response_msg: Optional[str] = None
    ) -> AuditLog:
        """
        创建审计日志
        
        Args:
            action: 操作类型 (read/create/update/delete/login/logout)
            resource: 资源名称
            user_id: 用户ID
            user_name: 用户名
            role: 角色
            resource_id: 资源标识
            method: HTTP方法
            params: 请求参数（会被转为JSON）
            ip_address: IP地址
            user_agent: 浏览器标识
            status_code: 状态码
            response_msg: 响应消息
        """
        import json
        
        # 过滤敏感参数
        filtered_params = self._filter_sensitive_params(params) if params else None
        params_str = json.dumps(filtered_params, ensure_ascii=False) if filtered_params else None
        
        log = AuditLog(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action=action,
            resource=resource,
            resource_id=resource_id,
            method=method,
            params=params_str,
            ip_address=ip_address,
            user_agent=user_agent,
            status_code=status_code,
            response_msg=response_msg
        )
        
        return self._repo.save(log)
    
    def get_logs(
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
        days: Optional[int] = None,
        limit: int = PaginationConfig.MAX_AUDIT_LOGS,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        查询审计日志
        
        Args:
            days: 最近N天（如果设置，会覆盖start_time和end_time）
        """
        # 如果指定了days，自动计算时间范围
        if days and not (start_time or end_time):
            end_time = datetime.now().isoformat()
            start_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        return self._repo.find_by_filters(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action=action,
            resource=resource,
            method=method,
            status_code=status_code,
            ip_address=ip_address,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
    
    def get_log_count(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        days: Optional[int] = None
    ) -> int:
        """获取日志数量"""
        start_time = None
        end_time = None
        
        if days:
            end_time = datetime.now().isoformat()
            start_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        return self._repo.count_by_filters(
            user_id=user_id,
            action=action,
            resource=resource,
            start_time=start_time,
            end_time=end_time
        )
    
    def get_statistics(
        self,
        days: int = 7,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取审计统计"""
        return self._repo.get_statistics(days=days, user_id=user_id)
    
    def get_recent_activity(
        self,
        user_id: int,
        limit: int = PaginationConfig.MY_LOGS_PAGE_SIZE
    ) -> List[AuditLog]:
        """获取用户近期活动"""
        return self._repo.find_by_filters(
            user_id=user_id,
            limit=limit
        )
    
    def _filter_sensitive_params(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """过滤敏感参数"""
        sensitive_fields = [
            'password', 'old_password', 'new_password', 
            'secret', 'token', 'authorization', 'cookie'
        ]
        
        filtered = {}
        for key, value in params.items():
            if key.lower() in sensitive_fields:
                filtered[key] = '***'
            else:
                filtered[key] = value
        
        return filtered
