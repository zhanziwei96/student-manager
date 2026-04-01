"""
签到相关 API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from app.core.db import get_session
from app.core.config import HttpStatus
from app.crud import (
    get_class_session, start_class, end_class,
    get_today_checkins, create_checkin, has_checked_in_today
)
from app.api.deps import require_login
from app.core.jwt import get_current_user
from app.models.constants import (
    ApiResponseConst, MessageConst, RoutePrefixConst,
    ApiResponse, ApiSuccessResponse
)
from app.models.checkin import ClassSession

router = APIRouter(tags=["checkin"])


class CheckinRequest(BaseModel):
    student_id: str = Field(..., description="学号")
    student_name: str = Field(..., description="姓名")
    lat: Optional[float] = Field(default=None, description="签到纬度")
    lng: Optional[float] = Field(default=None, description="签到经度")
    device_id: Optional[str] = Field(default=None, description="设备指纹ID")
    device_info: Optional[str] = Field(default=None, description="设备信息JSON")


class StartClassRequest(BaseModel):
    class_name: str = Field(..., description="班级名称")
    course_name: Optional[str] = Field(default=None, description="课程名称")
    location_lat: Optional[float] = Field(default=None, description="签到中心纬度")
    location_lng: Optional[float] = Field(default=None, description="签到中心经度")
    location_name: Optional[str] = Field(default=None, description="位置名称")
    checkin_radius: Optional[int] = Field(default=100, description="签到半径（米）")


class ClassSessionData(BaseModel):
    """课堂会话数据"""
    active: bool
    course_name: Optional[str] = None
    class_name: Optional[str] = None
    start_time: Optional[datetime] = None


class CheckinData(BaseModel):
    """签到数据"""
    id: int
    student_id: str
    student_name: str
    class_name: str
    checkin_time: datetime
    checkin_type: str
    session_id: int
    lat: Optional[float] = None
    lng: Optional[float] = None
    distance: Optional[float] = None


class CheckinStatsData(BaseModel):
    """签到统计数据"""
    active: bool
    course_name: Optional[str] = None
    class_name: Optional[str] = None
    total: int
    checked_in: int
    not_checked_in: int
    rate: float


class ActiveSessionData(BaseModel):
    """活跃课堂数据"""
    course_name: Optional[str] = None
    class_name: Optional[str] = None
    teacher_id: int
    teacher_name: Optional[str] = None
    start_time: Optional[datetime] = None


class StudentSessionData(BaseModel):
    """学生端课堂数据"""
    id: Optional[int] = None
    session_code: Optional[str] = None
    active: bool = True
    course_name: Optional[str] = None
    class_name: Optional[str] = None
    teacher_name: Optional[str] = None
    start_time: Optional[datetime] = None


# 响应模型定义
class ClassSessionResponse(ApiResponse[ClassSessionData]):
    """课堂会话响应"""
    pass


class StartClassResponse(ApiResponse[dict]):
    """开始课堂响应"""
    pass


class CheckinResponse(ApiResponse[CheckinData]):
    """签到响应"""
    pass


class CheckinListResponse(ApiResponse[list[CheckinData]]):
    """签到列表响应"""
    pass


class CheckinStatsResponse(ApiResponse[CheckinStatsData]):
    """签到统计响应"""
    pass


class ActiveSessionsResponse(ApiResponse[list[ActiveSessionData]]):
    """活跃课堂列表响应"""
    pass


class StudentSessionResponse(ApiResponse[StudentSessionData]):
    """学生端课堂响应"""
    pass


@router.get("/class-session", response_model=ClassSessionResponse)
def get_current_session(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取当前用户的上课状态"""
    teacher_id = int(user.get("sub", 0))
    class_session = get_class_session(session, teacher_id)
    if class_session:
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'active': class_session.active,
                'course_name': class_session.course_name,
                'class_name': class_session.class_name,
                'start_time': class_session.start_time
            }
        }
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {'active': False}
    }


@router.post("/class-session/start", response_model=StartClassResponse)
async def begin_class(
    request: Request,
    data: StartClassRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """开始上课（检查班级冲突）"""
    # 用户认证已通过 Depends(get_current_user) 完成
    
    # 检查该班级是否已有活跃课堂
    from app.crud.checkin import get_class_session_by_class_name
    existing_session = get_class_session_by_class_name(session, data.class_name)
    if existing_session and existing_session.active:
        teacher_name = existing_session.teacher_name or "其他教师"
        raise HTTPException(
            status_code=HttpStatus.CONFLICT,
            detail=f'该班级正在被 {teacher_name} 老师上课，无法开始新课堂'
        )
    
    # 检查当前教师是否有其他活跃课堂
    teacher_id = int(user.get("sub", 0))
    current_session = get_class_session(session, teacher_id)
    if current_session and current_session.active and current_session.class_name != data.class_name:
        raise HTTPException(
            status_code=HttpStatus.CONFLICT,
            detail=f'您正在 {current_session.class_name} 上课，请先结束当前课堂'
        )
    
    # 开始新课堂
    teacher_name = user.get("name", "")
    class_session = start_class(
        session=session,
        class_name=data.class_name,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        course_name=data.course_name,
        location_lat=data.location_lat,
        location_lng=data.location_lng,
        location_name=data.location_name,
        checkin_radius=data.checkin_radius
    )
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_STARTED,
        ApiResponseConst.DATA: class_session.model_dump()
    }


@router.post("/class-session/end", response_model=ApiSuccessResponse)
async def finish_class(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """结束上课"""
    # 用户认证已通过 Depends(get_current_user) 完成
    
    teacher_id = int(user.get("sub", 0))
    end_class(session, teacher_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_ENDED
    }


@router.post("/checkin", response_model=CheckinResponse)
def do_checkin(
    request: Request,
    data: CheckinRequest,
    db_session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """学生签到（带GPS地理围栏验证）"""
    import math
    from app.crud.checkin import get_class_session_by_class_name, has_checked_in_session, is_device_checked_in_session
    
    # 验证学生
    from app.crud import get_student
    student = get_student(db_session, data.student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    
    # 检查学生所在班级是否有活跃课堂
    class_session = get_class_session_by_class_name(db_session, student.class_name)
    if not class_session or not class_session.active:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='当前未在上课')
    
    # 检查是否在当前课堂已签到
    if has_checked_in_session(db_session, data.student_id, class_session.id):
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='您已在本课堂签到')
    
    # 验证GPS定位（如果课堂设置了位置）
    if class_session.location_lat is not None and class_session.location_lng is not None:
        # 检查是否提供了GPS位置
        if data.lat is None or data.lng is None:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='请先开启GPS定位')
        
        # 计算与签到中心的距离（Haversine公式）
        R = 6371000  # 地球半径（米）
        lat1 = math.radians(class_session.location_lat)
        lat2 = math.radians(data.lat)
        delta_lat = math.radians(data.lat - class_session.location_lat)
        delta_lng = math.radians(data.lng - class_session.location_lng)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        # 检查是否在允许范围内
        if distance > class_session.checkin_radius:
            raise HTTPException(
                status_code=HttpStatus.FORBIDDEN, 
                detail=f'您不在签到范围内，距离签到点约{distance:.0f}米，允许范围{class_session.checkin_radius}米'
            )
    
    # 验证设备唯一性（如果提供了设备ID）
    if data.device_id:
        if is_device_checked_in_session(db_session, data.device_id, class_session.id):
            raise HTTPException(status_code=HttpStatus.CONFLICT, detail='该设备已签到')
    
    # 创建签到记录
    checkin = create_checkin(
        db_session,
        data.student_id,
        data.student_name or student.name,
        class_session.class_name,
        class_session.id,
        lat=data.lat,
        lng=data.lng,
        distance=distance if class_session.location_lat else None,
        device_id=data.device_id,
        device_info=data.device_info
    )
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CHECKIN_SUCCESS,
        ApiResponseConst.DATA: checkin.model_dump()
    }


@router.get("/checkins/today", response_model=CheckinListResponse)
def get_today_checkin_list(
    request: Request,
    class_name: Optional[str] = Query(None, description="班级名称"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取今日签到列表（只返回当前课堂开始后的签到）"""
    # 根据班级名称获取活跃课堂
    from app.crud.checkin import get_class_session_by_class_name
    class_session = get_class_session_by_class_name(session, class_name) if class_name else None
    
    # 只查询当前课堂开始时间之后的签到（如果课堂活跃）
    if class_session and class_session.active:
        checkins = get_today_checkins(session, class_name, class_session.start_time)
    elif class_name:
        # 指定了班级但没有活跃课堂，返回今日该班级所有签到（用于历史查看）
        checkins = get_today_checkins(session, class_name)
    else:
        # 没有指定班级，返回今日所有签到
        checkins = get_today_checkins(session)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [c.model_dump() for c in checkins]
    }


@router.get("/checkins/stats", response_model=CheckinStatsResponse)
def get_checkin_stats(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取签到统计（当前教师的活跃课堂）"""
    teacher_id = int(user.get("sub", 0))
    class_session = get_class_session(session, teacher_id)
    
    if not class_session or not class_session.active:
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'active': False,
                'total': 0,
                'checked_in': 0,
                'not_checked_in': 0,
                'rate': 0
            }
        }
    
    from app.crud import get_students_by_class
    students = get_students_by_class(session, class_session.class_name)
    # 只统计当前课堂开始后的签到
    checkins = get_today_checkins(session, class_session.class_name, class_session.start_time)
    
    total = len(students)
    checked_in = len(checkins)
    not_checked_in = total - checked_in
    rate = round(checked_in / total * 100, 1) if total > 0 else 0
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'active': True,
            'course_name': class_session.course_name,
            'class_name': class_session.class_name,
            'total': total,
            'checked_in': checked_in,
            'not_checked_in': not_checked_in,
            'rate': rate
        }
    }


@router.get("/class-sessions/active", response_model=ActiveSessionsResponse)
def get_active_class_sessions(
    request: Request,
    session: Session = Depends(get_session)
):
    """获取所有活跃课堂列表"""
    from sqlmodel import select
    query = select(ClassSession).where(ClassSession.active == True)
    active_sessions = session.exec(query).all()
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                'course_name': s.course_name,
                'class_name': s.class_name,
                'teacher_id': s.teacher_id,
                'teacher_name': s.teacher_name,
                'start_time': s.start_time
            }
            for s in active_sessions
        ]
    }


@router.get("/class-sessions/class/{class_name}", response_model=StudentSessionResponse)
async def get_class_session_for_student(
    class_name: str,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取指定班级的活跃课堂状态（学生端使用）"""
    # 用户认证已通过 Depends(get_current_user) 完成
    
    from app.crud.checkin import get_class_session_by_class_name
    class_session = get_class_session_by_class_name(session, class_name)
    
    if class_session and class_session.active:
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'id': class_session.id,
                'session_code': class_session.session_code,
                'active': True,
                'course_name': class_session.course_name,
                'class_name': class_session.class_name,
                'teacher_name': class_session.teacher_name,
                'start_time': class_session.start_time
            }
        }
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {'active': False}
    }
