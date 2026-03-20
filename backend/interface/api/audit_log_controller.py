"""
审计日志API控制器 - FastAPI版本
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field

from infrastructure.persistence.database import Database
from infrastructure.persistence.repositories.sqlite_audit_log_repository import SQLiteAuditLogRepository
from infrastructure.security.session import require_admin, require_login
from application.services.audit_log_app_service import AuditLogAppService


router = APIRouter(prefix="/api/audit", tags=["audit"])


# ============ Pydantic模型 ============

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    role: Optional[str]
    action: str
    resource: str
    resource_id: Optional[str]
    method: Optional[str]
    params: Optional[str]
    ip_address: Optional[str]
    status_code: Optional[int]
    created_at: str


class AuditStatsResponse(BaseModel):
    period_days: int
    total_count: int
    action_stats: dict
    resource_stats: dict
    status_stats: dict
    top_active_users: List[dict]


class LogListResponse(BaseModel):
    success: bool
    data: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


# ============ 依赖注入 ============

def get_audit_log_service():
    """获取审计日志应用服务"""
    db = Database()
    repo = SQLiteAuditLogRepository(db)
    return AuditLogAppService(repo)


# ============ API端点 ============

@router.get("/logs", response_model=dict)
async def get_audit_logs(
    request: Request,
    user_id: Optional[int] = Query(None, description="用户ID"),
    user_name: Optional[str] = Query(None, description="用户名（模糊匹配）"),
    role: Optional[str] = Query(None, description="角色"),
    action: Optional[str] = Query(None, description="操作类型: read/create/update/delete/login/logout"),
    resource: Optional[str] = Query(None, description="资源名称"),
    method: Optional[str] = Query(None, description="HTTP方法: GET/POST/PUT/DELETE"),
    status_code: Optional[int] = Query(None, description="状态码"),
    ip_address: Optional[str] = Query(None, description="IP地址"),
    days: Optional[int] = Query(None, description="最近N天"),
    limit: int = Query(100, ge=1, le=1000, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    service: AuditLogAppService = Depends(get_audit_log_service)
):
    """
    查询审计日志（管理员权限）
    
    支持多种筛选条件，返回分页结果
    """
    require_admin(request)
    
    try:
        logs = service.get_logs(
            user_id=user_id,
            user_name=user_name,
            role=role,
            action=action,
            resource=resource,
            method=method,
            status_code=status_code,
            ip_address=ip_address,
            days=days,
            limit=limit,
            offset=offset
        )
        
        total = service.get_log_count(
            user_id=user_id,
            action=action,
            resource=resource,
            days=days
        )
        
        return {
            'success': True,
            'data': [log.to_dict() for log in logs],
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/my", response_model=dict)
async def get_my_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    service: AuditLogAppService = Depends(get_audit_log_service)
):
    """
    获取当前用户的操作日志
    """
    user_id = require_login(request)
    
    try:
        logs = service.get_recent_activity(user_id, limit=limit)
        
        return {
            'success': True,
            'data': [log.to_dict() for log in logs]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_audit_stats(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    user_id: Optional[int] = Query(None, description="指定用户ID"),
    service: AuditLogAppService = Depends(get_audit_log_service)
):
    """
    获取审计统计（管理员权限）
    
    返回操作类型分布、资源访问分布、活跃用户排行等统计信息
    """
    require_admin(request)
    
    try:
        stats = service.get_statistics(days=days, user_id=user_id)
        
        return {
            'success': True,
            'data': stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions", response_model=dict)
async def get_action_types(request: Request):
    """
    获取所有操作类型列表
    """
    require_login(request)
    
    return {
        'success': True,
        'data': [
            {'value': 'login', 'label': '登录'},
            {'value': 'logout', 'label': '登出'},
            {'value': 'read', 'label': '查询'},
            {'value': 'create', 'label': '创建'},
            {'value': 'update', 'label': '更新'},
            {'value': 'delete', 'label': '删除'}
        ]
    }


@router.get("/resources", response_model=dict)
async def get_resource_types(request: Request):
    """
    获取所有资源类型列表
    """
    require_login(request)
    
    return {
        'success': True,
        'data': [
            {'value': 'students', 'label': '学生管理'},
            {'value': 'checkin', 'label': '签到系统'},
            {'value': 'score', 'label': '分数管理'},
            {'value': 'users', 'label': '用户管理'},
            {'value': 'class_session', 'label': '课堂会话'}
        ]
    }
