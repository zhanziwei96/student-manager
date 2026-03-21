"""
SQLite审计日志仓储实现
"""
import sqlite3
import json
from typing import List, Optional, Dict, Any

from domain.entities.audit_log import AuditLog
from domain.repositories.audit_log_repository import AuditLogRepository
from infrastructure.persistence.database import Database
from infrastructure.config import PaginationConfig


class SQLiteAuditLogRepository(AuditLogRepository):
    """SQLite审计日志仓储实现"""
    
    def __init__(self, db: Database):
        self._db = db
    
    def _row_to_entity(self, row: sqlite3.Row) -> AuditLog:
        """将数据库行转换为实体"""
        return AuditLog(
            id=row['id'],
            user_id=row['user_id'],
            user_name=row['user_name'],
            role=row['role'],
            action=row['action'],
            resource=row['resource'],
            resource_id=row['resource_id'],
            method=row['method'],
            params=row['params'],
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            status_code=row['status_code'],
            response_msg=row['response_msg'],
            created_at=row['created_at']
        )
    
    def save(self, log: AuditLog) -> AuditLog:
        """保存审计日志"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                """INSERT INTO audit_logs
                    (user_id, user_name, role, action, resource, resource_id,
                     method, params, ip_address, user_agent, status_code, response_msg)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    log.user_id, log.user_name, log.role, log.action, log.resource,
                    log.resource_id, log.method, log.params, log.ip_address,
                    log.user_agent, log.status_code, log.response_msg
                )
            )
            log.id = cursor.lastrowid
            return log
    
    def find_by_id(self, log_id: int) -> Optional[AuditLog]:
        """根据ID查找日志"""
        with self._db.connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_logs WHERE id = ?",
                (log_id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
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
        limit: int = PaginationConfig.MAX_AUDIT_LOGS,
        offset: int = 0
    ) -> List[AuditLog]:
        """条件查询日志"""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if user_name:
            query += " AND user_name LIKE ?"
            params.append(f"%{user_name}%")
        
        if role:
            query += " AND role = ?"
            params.append(role)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if resource:
            query += " AND resource LIKE ?"
            params.append(f"%{resource}%")
        
        if method:
            query += " AND method = ?"
            params.append(method)
        
        if status_code is not None:
            query += " AND status_code = ?"
            params.append(status_code)
        
        if ip_address:
            query += " AND ip_address LIKE ?"
            params.append(f"%{ip_address}%")
        
        if start_time:
            query += " AND created_at >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND created_at <= ?"
            params.append(end_time)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._db.connection() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def count_by_filters(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> int:
        """根据条件统计日志数量"""
        query = "SELECT COUNT(*) as count FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if resource:
            query += " AND resource LIKE ?"
            params.append(f"%{resource}%")
        
        if start_time:
            query += " AND created_at >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND created_at <= ?"
            params.append(end_time)
        
        with self._db.connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def get_statistics(
        self,
        days: int = 7,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取审计统计"""
        with self._db.connection() as conn:
            # 基础查询条件
            where_clause = f"created_at >= datetime('now', '-{days} days')"
            params = []
            
            if user_id:
                where_clause += " AND user_id = ?"
                params.append(user_id)
            
            # 操作类型统计
            cursor = conn.execute(f'''
                SELECT action, COUNT(*) as count 
                FROM audit_logs 
                WHERE {where_clause}
                GROUP BY action
            ''', params)
            action_stats = {row['action']: row['count'] for row in cursor.fetchall()}
            
            # 资源访问统计
            cursor = conn.execute(f'''
                SELECT resource, COUNT(*) as count 
                FROM audit_logs 
                WHERE {where_clause}
                GROUP BY resource
            ''', params)
            resource_stats = {row['resource']: row['count'] for row in cursor.fetchall()}
            
            # 状态码统计
            cursor = conn.execute(f'''
                SELECT status_code, COUNT(*) as count 
                FROM audit_logs 
                WHERE {where_clause}
                GROUP BY status_code
            ''', params)
            status_stats = {row['status_code']: row['count'] for row in cursor.fetchall()}
            
            # 活跃用户统计
            cursor = conn.execute(f'''
                SELECT user_name, COUNT(*) as count 
                FROM audit_logs 
                WHERE {where_clause} AND user_id IS NOT NULL
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            ''', params)
            top_users = [{'user_name': row['user_name'], 'count': row['count']} 
                        for row in cursor.fetchall()]
            
            # 总记录数
            cursor = conn.execute(f'''
                SELECT COUNT(*) as count FROM audit_logs WHERE {where_clause}
            ''', params)
            total_count = cursor.fetchone()['count']
            
            return {
                'period_days': days,
                'total_count': total_count,
                'action_stats': action_stats,
                'resource_stats': resource_stats,
                'status_stats': status_stats,
                'top_active_users': top_users
            }
