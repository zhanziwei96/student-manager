"""
系统相关 API
"""
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import get_settings
from app.core.jwt import get_current_user
from app.models.constants import (
    VERSION, SystemStatusConst, ApiResponseConst, RoutePrefixConst
)

router = APIRouter(prefix=RoutePrefixConst.API, tags=["system"])


@router.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": SystemStatusConst.HEALTHY,
        "timestamp": datetime.now().isoformat(),
        "version": VERSION
    }


@router.get("/stats")
def get_stats(
    request: Request, 
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取系统统计（需要登录）"""
    from app.crud import get_students, get_all_classes
    from app.crud.checkin import get_today_checkins
    
    students = get_students(session)
    classes = get_all_classes(session)
    checkins = get_today_checkins(session)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'total_students': len(students),
            'total_classes': len(classes),
            'today_checkins': len(checkins)
        }
    }


@router.get("/dashboard")
def get_dashboard_stats(session: Session = Depends(get_session)):
    """
    获取仪表盘统计数据（公开接口，数据脱敏）
    用于首页数据展示，无需登录
    """
    from app.crud import get_students, get_all_classes
    from app.crud.checkin import get_today_checkins
    
    students = get_students(session)
    classes = get_all_classes(session)
    checkins = get_today_checkins(session)
    
    total_students = len(students)
    checked_in = len(checkins)
    not_checked_in = total_students - checked_in
    checkin_rate = round(checked_in / total_students * 100, 1) if total_students > 0 else 0
    
    # 分数排行榜（脱敏处理：隐藏姓名和学号，只显示分数和排名）
    score_ranking = []
    if students:
        # 按分数排序，取前10
        sorted_students = sorted(students, key=lambda s: s.score, reverse=True)[:10]
        for rank, student in enumerate(sorted_students, 1):
            score_ranking.append({
                'rank': rank,
                'score': student.score,
                # 姓名脱敏：显示第一位和最后一位，中间用 * 代替
                'name_mask': student.name[0] + '*' + student.name[-1] if len(student.name) >= 2 else (student.name if student.name else '*'),
                # 学号脱敏：只显示后4位
                'student_id_mask': '****' + student.student_id[-4:] if len(student.student_id) >= 4 else '****'
            })
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'total_students': total_students,
            'total_classes': len(classes),
            'today_checkins': checked_in,
            'checked_in': checked_in,
            'not_checked_in': not_checked_in,
            'checkin_rate': checkin_rate,
            'score_ranking': score_ranking
        }
    }
