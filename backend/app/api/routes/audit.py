"""
审计日志 API — 敏感操作记录查询（ADM-13）
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import require_admin
from app.core.db import get_session
from app.crud.audit import get_audit_logs
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["audit"])


@router.get("/audit-logs", response_model=ApiResponse[list])
def list_audit_logs(
    semester_id: Optional[int] = Query(None, description="按学期过滤（缺省全部）"),
    limit: int = Query(100, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """审计日志列表（仅管理员，支持按学期过滤）"""
    logs = get_audit_logs(session, limit=limit, offset=offset, semester_id=semester_id)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user_name,
            "role": log.role,
            "action": log.action,
            "resource": log.resource,
            "method": log.method,
            "status_code": log.status_code,
            "semester_id": log.semester_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]}
