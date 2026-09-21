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
    - teacher → 授课教学班关联的 class_id 列表
    - 其他角色 / 无效用户 / 无教学班 / **教学班未关联任何班级** → []（空集，fail-closed）

    ⚠️ 安全语义（2026-09-21 收紧）：教学班没有关联班级时**不再**按「通配＝全部班级」处理。
    通配会让「关联没配全」的老师直接拿到全校班级权限（开发库中曾真实发生过）。
    未配关联的老师现在看不到任何班级，需管理员在「教学班」页补配班级关联。

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
        # fail-closed：不按通配放行。老师看不到任何班级，直到管理员补配关联。
        logger.warning(
            "教师 %s 的教学班未关联任何班级（course_offering_classes 无行），按无权限处理；"
            "请管理员在教学班页面补配班级关联",
            user_obj.id,
        )
        return []
    return sorted(set(class_ids))


def verify_teacher_class_access(user: dict, class_id: int, session: Session) -> None:
    """校验教师是否有权操作指定班级（admin 放行，teacher 校验班级归属）

    权限唯一真源：course_offering_classes 关联表。fail-closed——
    教师没有教学班、或教学班未关联任何班级时，一律拒绝。

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
    if not accessible or class_id not in accessible:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权操作该班级")


def verify_teacher_group_access(user: dict, group_id: int, session: Session) -> None:
    """校验教师是否有权操作指定小组（按小组所属班级判定）

    用于只有 group_id、拿不到 class_id 的端点（小组详情/解散/踢人/转让组长等）。

    Raises:
        HTTPException 404: 小组不存在
        HTTPException 403: 小组不属于该教师的班级
    """
    from app.models import Group

    group = session.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="小组不存在")
    verify_teacher_class_access(user, group.class_id, session)


def verify_class_has_active_students(class_id: int, session: Session) -> None:
    """校验班级存在且有启用学生（防止为禁用/不存在班级创建内容）

    Args:
        class_id: 班级 ID
        session: 数据库会话

    Raises:
        HTTPException 400: 班级不存在或所有学生已禁用
    """
    from app.models import Student

    count = session.exec(
        select(func.count()).select_from(Student).where(
            Student.class_id == class_id,
            Student.is_account_enabled.is_(True)
        )
    ).one()

    if count == 0:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="班级不存在或所有学生已禁用"
        )
