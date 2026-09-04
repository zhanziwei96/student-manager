"""
学期信息 API - 前端周次计算基准来源
"""
from fastapi import APIRouter

from app.core.term import (
    get_current_term,
    get_term_start_date,
    get_term_total_weeks,
    get_current_week_number,
)
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["term"])


@router.get("/term/current", response_model=ApiResponse[dict])
def get_current_term_info():
    """获取当前学期信息（无认证，前端登录前亦需使用）"""
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "term": get_current_term(),
            "start_date": get_term_start_date().isoformat(),
            "current_week": get_current_week_number(),
            "total_weeks": get_term_total_weeks(),
        }
    }
