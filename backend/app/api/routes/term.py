"""
学期信息 API - 前端周次计算基准来源
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.core.term import (
    get_current_term,
    get_current_semester,
    get_current_week_number,
)
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["term"])


@router.get("/term/current", response_model=ApiResponse[dict])
def get_current_term_info(session: Session = Depends(get_session)):
    """获取当前学期信息（无认证，前端登录前亦需使用）"""
    sem = get_current_semester(session)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "term": get_current_term(),
            "start_date": sem.start_date.isoformat() if sem else None,
            "current_week": get_current_week_number(session),
            "total_weeks": sem.total_weeks if sem else None,
        }
    }
