"""
API 依赖注入 - JWT 版本
"""
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


def verify_teacher_class_access(user: dict, class_name: str, session: Session) -> None:
    """校验教师是否有权操作指定班级（admin 放行，teacher 校验班级归属）

    过渡期兼容双路径：assigned_classes 旧路径优先；
    为空/未配置时从 course_offerings 派生（教师授课班级集合，方案 9.7）。

    Args:
        user: get_current_user 返回的 JWT claims dict
        class_name: 目标班级名
        session: 数据库会话

    Raises:
        HTTPException 403: 无权限
    """
    from app.models import CourseOffering, User

    role = user.get("role", "")
    if role == "admin":
        return
    if role != "teacher":
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="需要管理员或教师权限")

    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无效的用户信息")

    user_obj = session.get(User, int(user_id))
    if user_obj is None:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="用户不存在")

    assigned = user_obj.get_assigned_classes()
    if assigned and class_name in assigned:
        return

    # 派生路径：offerings.teacher_id 的 class_scope 包含目标班级
    offering = session.exec(select(CourseOffering).where(
        CourseOffering.teacher_id == user_obj.id,
        CourseOffering.class_scope.contains(class_name),
    )).first()
    if offering is None:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权操作该班级")


def verify_class_has_active_students(class_name: str, session: Session) -> None:
    """校验班级存在且有启用学生（防止为禁用/不存在班级创建内容）

    Args:
        class_name: 班级名称
        session: 数据库会话

    Raises:
        HTTPException 400: 班级不存在或所有学生已禁用
    """
    from app.models import Student

    count = session.exec(
        select(func.count()).select_from(Student).where(
            Student.class_name == class_name,
            Student.is_account_enabled.is_(True)
        )
    ).one()

    if count == 0:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="班级不存在或所有学生已禁用"
        )
