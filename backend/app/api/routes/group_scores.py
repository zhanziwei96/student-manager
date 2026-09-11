"""
小组分数 API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.config import HttpStatus
from app.api.deps import require_admin_or_teacher, verify_teacher_class_access
from app.crud.group_score import update_group_score, get_group_score_logs
from app.models import Group
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse

router = APIRouter(tags=["group-scores"])


class UpdateGroupScoreRequest(BaseModel):
    score_change: float = Field(..., description="分数变化值")
    reason: str = Field(..., min_length=1, max_length=200, description="原因")


@router.put("/groups/{group_id}/score", response_model=ApiSuccessResponse)
def update_score(
    group_id: int,
    data: UpdateGroupScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """更新小组分数（admin 或负责该班的教师）"""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")

    verify_teacher_class_access(user, group.class_id, session)

    username = user.get("username", "")
    result = update_group_score(session, group_id, data.score_change, data.reason, username)
    if not result:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "分数已更新"
    }


@router.get("/groups/{group_id}/score-logs", response_model=ApiResponse[List[dict]])
def get_score_logs(
    group_id: int,
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取小组分数日志"""
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")

    verify_teacher_class_access(user, group.class_id, session)

    logs = get_group_score_logs(session, group_id, limit=limit, offset=offset)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "old_score": log.old_score,
                "new_score": log.new_score,
                "delta": log.delta,
                "reason": log.reason,
                "operator": log.operator,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }


