"""
签到相关 API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Body, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.class_cache import get_class_display_name_by_id, get_class_display_names
from app.core.term import get_current_semester_id
from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.rate_limit import check_rate_limit
from app.crud import (
    create_checkin, get_students_by_class
)
from app.crud.checkin import (
    get_checkins_by_session_id, get_all_checkins
)
from app.crud.course_session import (
    get_active_course_session_by_class_id,
    get_teacher_active_course_sessions,
    get_course_session,
)
from app.crud.checkin import DuplicateCheckinError
from app.crud.device_bind import upsert_device_bind
from app.core.jwt import get_current_user
from app.core.qr_signature import verify_verification_code
from app.models.constants import (
    ApiResponseConst, MessageConst,
    ApiResponse, ApiSuccessResponse
)
from app.models import CourseSession
from app.api.deps import verify_teacher_class_access, require_admin_or_teacher

router = APIRouter(tags=["checkin"])


class CheckinRequest(BaseModel):
    student_id: str = Field(..., description="学号")
    student_name: str = Field(..., description="姓名")
    device_id: Optional[str] = Field(default=None, description="设备指纹ID")
    device_info: Optional[str] = Field(default=None, description="设备信息JSON")
    verification_code: Optional[str] = Field(default=None, description="动态验证码")
    session_id: Optional[int] = Field(default=None, description="课堂会话ID（教师手动签到时必填）")


class CheckinData(BaseModel):
    """签到数据"""
    id: int
    student_id: str
    student_name: str
    class_name: str
    checkin_time: datetime
    checkin_type: str
    session_id: int


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
    id: int
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


@router.post("/checkin", response_model=CheckinResponse)
async def do_checkin(
    request: Request,
    data: CheckinRequest,
    db_session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """签到（支持学生扫码和教师手动两种模式）"""
    # 限流检查（基于学号）
    allowed = await check_rate_limit(request, data.student_id, key_prefix="checkin", limiter_attr="checkin_limiter")
    if not allowed:
        raise HTTPException(
            status_code=HttpStatus.TOO_MANY_REQUESTS,
            detail='请求过于频繁，请稍后再试'
        )

    from app.crud import get_student
    student = get_student(db_session, data.student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    user_role = user.get("role", "")
    is_teacher_or_admin = user_role in ("admin", "teacher")

    if data.verification_code:
        # === 学生验证码签到路径 ===
        # 先通过 session_id 查找课堂（学生端已知 session_id）
        from app.crud.course_session import get_course_session_by_session_code
        # 由于验证码本身不携带 session_code，我们需要先找到该学生班级的活跃课堂
        # 实际场景中学生端已经通过 /course-sessions/class/{class_id} 获取了 session_code
        # 这里复用该接口返回的 session_code 来验证
        cs = get_active_course_session_by_class_id(db_session, student.class_id)
        if not cs or cs.status != "active":
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='当前未在上课')

        if not verify_verification_code(cs.session_code, data.verification_code):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='验证码无效或已过期')

        # 验证 JWT 身份：只能为自己签到
        if not is_teacher_or_admin:
            if str(user.get("sub")) != data.student_id:
                raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='只能为自己签到')

        # 验证班级匹配（FK 比较，跨届同名班不混淆）
        if student.class_id != cs.class_id:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='你不是该课堂的学生')

        # 设备绑定检查（在同一事务内完成，防止并发竞态）
        device_bound = False
        if data.device_id:
            upsert_device_bind(db_session, cs.id, data.student_id, data.device_id)
            device_bound = True

        try:
            checkin = create_checkin(
                db_session,
                data.student_id,
                data.student_name or student.name,
                cs.class_id,
                cs.id,
                device_id=data.device_id,
                device_info=data.device_info,
                qr_signature=data.verification_code,
                device_bound=device_bound,
            )
        except DuplicateCheckinError as e:
            raise HTTPException(status_code=HttpStatus.CONFLICT, detail=str(e))

    elif is_teacher_or_admin and data.session_id:
        # === 教师手动签到路径 ===
        cs = get_course_session(db_session, data.session_id)
        if not cs:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='课堂不存在')
        if cs.status != "active":
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='课堂未在进行中')
        # 验证教师是否有权操作该课堂
        if cs.teacher_id != int(user.get("sub", 0)) and user_role != "admin":
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='无权为该课堂签到')
        # 验证学生属于该课堂班级
        if student.class_id != cs.class_id:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='该学生不属于此课堂班级')

        try:
            checkin = create_checkin(
                db_session,
                data.student_id,
                data.student_name or student.name,
                cs.class_id,
                cs.id,
            )
        except DuplicateCheckinError as e:
            raise HTTPException(status_code=HttpStatus.CONFLICT, detail=str(e))

    else:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='缺少验证码或教师权限')

    checkin_data = checkin.model_dump()
    checkin_data["class_name"] = get_class_display_name_by_id(db_session, checkin.class_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CHECKIN_SUCCESS,
        ApiResponseConst.DATA: checkin_data
    }


@router.get("/checkins", response_model=CheckinListResponse)
def get_checkin_list(
    request: Request,
    limit: int = Query(200, ge=1, le=1000, description="返回条数限制"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取签到记录列表（admin 全量；教师限负责班级）"""
    class_ids = None
    if user.get("role") != "admin":
        from app.api.deps import get_teacher_accessible_classes
        # 返回 int 列表 / None（通配）/ []（空集，fail-closed），直接透传
        class_ids = get_teacher_accessible_classes(user, session)

    checkins = get_all_checkins(session, limit=limit, class_ids=class_ids)
    name_map = get_class_display_names(session, (c.class_id for c in checkins))
    data = []
    for c in checkins:
        item = c.model_dump()
        item["class_name"] = name_map.get(c.class_id)
        data.append(item)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: data
    }


@router.get("/checkins/session/{session_id}", response_model=CheckinListResponse)
def get_session_checkin_list(
    request: Request,
    session_id: int,
    db_session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取指定课堂会话的签到列表（admin 或负责该班的教师）"""
    cs = get_course_session(db_session, session_id)
    if not cs:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课堂不存在")
    class_name = get_class_display_name_by_id(db_session, cs.class_id)
    verify_teacher_class_access(user, cs.class_id, db_session)

    checkins = get_checkins_by_session_id(db_session, session_id)
    data = []
    for c in checkins:
        item = c.model_dump()
        item["class_name"] = class_name
        data.append(item)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: data
    }


@router.get("/checkins/stats", response_model=CheckinStatsResponse)
def get_checkin_stats(
    request: Request,
    session_id: Optional[int] = Query(None, description="课堂会话ID"),
    db_session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取签到统计（支持按 session_id 精确统计）"""
    from app.crud.course_session import get_course_session

    if session_id:
        cs = get_course_session(db_session, session_id)
        if not cs:
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
        class_name = get_class_display_name_by_id(db_session, cs.class_id)
        verify_teacher_class_access(user, cs.class_id, db_session)
        students = get_students_by_class(db_session, cs.class_id)
        checkins = get_checkins_by_session_id(db_session, session_id)
        total = len(students)
        checked_in = len(checkins)
        not_checked_in = total - checked_in
        rate = round(checked_in / total * 100, 1) if total > 0 else 0
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'active': cs.status == "active",
                'course_name': cs.course_name,
                'class_name': class_name,
                'total': total,
                'checked_in': checked_in,
                'not_checked_in': not_checked_in,
                'rate': rate
            }
        }

    # 未指定 session_id 时，返回当前教师活跃课堂的统计（兼容旧逻辑）
    teacher_id = int(user.get("sub", 0))
    course_sessions = get_teacher_active_course_sessions(db_session, teacher_id)

    if not course_sessions:
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

    cs = course_sessions[0]
    class_name = get_class_display_name_by_id(db_session, cs.class_id)
    students = get_students_by_class(db_session, cs.class_id)
    checkins = get_checkins_by_session_id(db_session, cs.id)

    total = len(students)
    checked_in = len(checkins)
    not_checked_in = total - checked_in
    rate = round(checked_in / total * 100, 1) if total > 0 else 0

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'active': True,
            'course_name': cs.course_name,
            'class_name': class_name,
            'total': total,
            'checked_in': checked_in,
            'not_checked_in': not_checked_in,
            'rate': rate
        }
    }


@router.get("/course-sessions/active", response_model=ActiveSessionsResponse)
def get_active_course_sessions(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取所有活跃课堂列表（需登录，学生签到页使用）"""
    from sqlmodel import select
    query = select(CourseSession).where(
        CourseSession.status == "active",
        CourseSession.semester_id == get_current_semester_id(session),
    )
    active_sessions = session.exec(query).all()
    name_map = get_class_display_names(session, (s.class_id for s in active_sessions))

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                'id': s.id,
                'course_name': s.course_name,
                'class_name': name_map.get(s.class_id),
                'teacher_id': s.teacher_id,
                'teacher_name': s.teacher_name,
                'start_time': s.start_time
            }
            for s in active_sessions
        ]
    }


@router.get("/course-sessions/class/{class_id}", response_model=StudentSessionResponse)
async def get_course_session_for_student(
    class_id: int,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取指定班级的活跃课堂状态（学生端使用）"""
    cs = get_active_course_session_by_class_id(session, class_id)

    if cs and cs.status == "active":
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'id': cs.id,
                'session_code': cs.session_code,
                'active': True,
                'course_name': cs.course_name,
                'class_name': get_class_display_name_by_id(session, cs.class_id),
                'teacher_name': cs.teacher_name,
                'start_time': cs.start_time
            }
        }

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {'active': False}
    }
