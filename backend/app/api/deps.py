"""
API 依赖注入 - JWT 版本
"""
import logging
from typing import Optional
from sqlmodel import Session, select
from sqlalchemy import func
from fastapi import Request
from app.core.db import get_session
from app.core.jwt import (
    get_current_user as jwt_get_current_user,
    require_login as jwt_require_login,
    require_admin as jwt_require_admin,
)
from fastapi import HTTPException
from app.core.config import HttpStatus

logger = logging.getLogger(__name__)

# 数据库会话依赖
SessionDep = get_session


# JWT 依赖导出
get_current_user = jwt_get_current_user
require_login = jwt_require_login
require_admin = jwt_require_admin


def is_admin(request: Request) -> bool:
    """检查是否为管理员"""
    from fastapi import HTTPException
    try:
        user = jwt_get_current_user(request)
        return user.get("is_admin", False)
    except HTTPException:
        return False


def get_session_user_id(request: Request) -> Optional[str]:
    """获取会话中的用户ID"""
    try:
        user = jwt_get_current_user(request)
        return user.get("sub")
    except HTTPException:
        return None


async def require_admin_or_teacher(request: Request):
    """要求管理员或教师权限"""
    user = await jwt_get_current_user(request)
    role = user.get("role", "")
    if role not in ["admin", "teacher"]:
        raise HTTPException(
            status_code=HttpStatus.FORBIDDEN,
            detail="需要管理员或教师权限"
        )
    return user


def get_teacher_accessible_classes(user: dict, session: Session):
    """教师可访问班级集合（唯一真源：course_offering_classes 关联表）

    - admin → None（表示不限范围）
    - teacher → 授课教学班关联的 class_id 列表；
      有教学班但关联表无行 → None（通配：面向全部班级，Phase 6 决策，过渡期语义）
    - 其他角色/无效用户/无教学班 → []（空集，任何班级都不可访问）

    供 verify_teacher_class_access 与排行榜/列表类端点复用。
    """
    from app.models import CourseOffering, CourseOfferingClass, User

    role = user.get("role", "")
    if role == "admin":
        return None

    user_id = user.get("sub")
    if not user_id:
        return []
    user_obj = session.get(User, int(user_id))
    if user_obj is None or role != "teacher":
        return []

    offerings = session.exec(select(CourseOffering).where(
        CourseOffering.teacher_id == user_obj.id,
    )).all()
    if not offerings:
        return []
    offering_ids = [o.id for o in offerings]
    class_ids = session.exec(select(CourseOfferingClass.class_id).where(
        CourseOfferingClass.offering_id.in_(offering_ids),
    )).all()
    if not class_ids:
        # 通配（Phase 6 决策）：offering 无关联行 = 面向全部班级
        logger.warning("教师 %s 的教学班无 course_offering_classes 关联行，按通配（全部班级）处理", user_obj.id)
        return None
    return sorted(set(class_ids))


def verify_teacher_class_access(user: dict, class_id: int, session: Session) -> None:
    """校验教师是否有权操作指定班级（admin 放行，teacher 校验班级归属）

    权限唯一真源：course_offering_classes 关联表（offering 无关联行 = 面向全部班级）。

    Args:
        user: get_current_user 返回的 JWT claims dict
        class_id: 目标班级 ID
        session: 数据库会话

    Raises:
        HTTPException 403: 无权限
    """
    role = user.get("role", "")
    if role == "admin":
        return
    if role != "teacher":
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="需要管理员或教师权限")

    accessible = get_teacher_accessible_classes(user, session)
    if accessible is None:
        return  # 通配：面向全部班级
    if not accessible or class_id not in accessible:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权操作该班级")


def verify_class_has_active_students(class_name: str, session: Session) -> None:
    """校验班级存在且有启用学生（防止为禁用/不存在班级创建内容）

    Args:
        class_name: 班级名称
        session: 数据库会话

    Raises:
        HTTPException 400: 班级不存在或所有学生已禁用
    """
    from app.core.class_cache import get_class_ids_by_names
    from app.models import Student

    count = session.exec(
        select(func.count()).select_from(Student).where(
            Student.class_id.in_(get_class_ids_by_names(session, [class_name])),
            Student.is_account_enabled.is_(True)
        )
    ).one()

    if count == 0:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="班级不存在或所有学生已禁用"
        )
