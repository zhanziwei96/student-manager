"""
学生 CRUD 操作 - 使用领域事件模式

REVIEW-P1: 权限检查统一在 API 层处理
- CRUD 层只负责纯粹的数据操作
- 权限控制、业务逻辑在 API 层实现
"""
from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import event as sa_event
from app.core.class_cache import get_class_id_by_name
from app.core.transition_filters import class_filter
from app.models import Student
from app.core.events import ScoreUpdated, event_bus


def get_student(session: Session, student_id: str) -> Optional[Student]:
    """根据学号获取学生"""
    return session.get(Student, student_id)


def get_students(
    session: Session,
    class_name: Optional[str] = None,
    include_disabled: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Student]:
    """获取学生列表（默认只返回启用学生，支持分页）

    Args:
        session: 数据库会话
        class_name: 班级名称（可选）
        include_disabled: 是否包含已禁用学生（admin 恢复场景用）
        limit: 返回数量限制（None=全部，保持向后兼容）
        offset: 偏移量（分页用）
    """
    query = select(Student).order_by(Student.student_id)
    if not include_disabled:
        query = query.where(Student.is_account_enabled.is_(True))
    if class_name:
        query = query.where(class_filter(
            Student.class_id, Student.class_name,
            get_class_id_by_name(session, class_name), class_name,
        ))
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return session.exec(query).all()


def count_students_filtered(
    session: Session,
    class_name: Optional[str] = None,
    class_names: Optional[List[str]] = None,
    include_disabled: bool = False,
) -> int:
    """按筛选条件统计学生总数（分页 total 用）

    Args:
        session: 数据库会话
        class_name: 单个班级名称（可选）
        class_names: 多个班级名称（可选，教师全部负责班级场景）
        include_disabled: 是否包含已禁用学生
    """
    from sqlalchemy import func
    query = select(func.count()).select_from(Student)
    if not include_disabled:
        query = query.where(Student.is_account_enabled.is_(True))
    if class_name:
        query = query.where(Student.class_name == class_name)
    elif class_names is not None:
        query = query.where(Student.class_name.in_(class_names))
    return session.exec(query).one()


def get_students_by_class(
    session: Session,
    class_name: str,
    include_disabled: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Student]:
    """根据班级获取学生（默认只返回启用学生，支持分页）

    Args:
        session: 数据库会话
        class_name: 班级名称
        include_disabled: 是否包含已禁用学生（admin 恢复场景用）
        limit: 返回数量限制（None=全部）
        offset: 偏移量（分页用）
    """
    query = select(Student).where(class_filter(
        Student.class_id, Student.class_name,
        get_class_id_by_name(session, class_name), class_name,
    )).order_by(Student.student_id)
    if not include_disabled:
        query = query.where(Student.is_account_enabled.is_(True))
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return session.exec(query).all()


def get_students_by_classes(
    session: Session,
    class_names: List[str],
    include_disabled: bool = False,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Student]:
    """
    根据多个班级获取学生 - 性能优化（REVIEW-P1），支持分页

    使用 SQL IN 查询替代循环查询，减少数据库往返次数。
    同时使用 SQL DISTINCT 去重，避免 Python 内存去重。
    默认只返回启用学生。

    Args:
        session: 数据库会话
        class_names: 班级名称列表
        include_disabled: 是否包含已禁用学生（admin 恢复场景用）
        limit: 返回数量限制（None=全部）
        offset: 偏移量（分页用）

    Returns:
        学生列表（已去重）
    """
    from sqlalchemy import distinct

    if not class_names:
        return []

    # 使用 IN 查询一次性获取所有班级学生
    query = select(Student).where(Student.class_name.in_(class_names)).order_by(Student.student_id)
    if not include_disabled:
        query = query.where(Student.is_account_enabled.is_(True))
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    return session.exec(query).all()


def create_student(session: Session, student_id: str, name: str, class_name: str) -> Student:
    """创建学生 - SEC-003: 使用简化密码哈希接口"""
    from app.core.security import hash_password

    # 使用学号作为默认密码
    password_hash = hash_password(student_id)
    
    student = Student(
        student_id=student_id,
        name=name,
        class_name=class_name,
        password_hash=password_hash
        # SEC-003: salt 字段不再设置（bcrypt 已内置盐值）
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def delete_student(session: Session, student_id: str) -> bool:
    """删除学生"""
    student = get_student(session, student_id)
    if not student:
        return False
    session.delete(student)
    session.commit()
    return True


def get_all_classes(session: Session) -> List[str]:
    """获取所有班级列表：classes 表 ∪ 启用学生的 class_name（过渡期合并，
    Phase 4 删除 students 部分后只保留 classes）"""
    from app.models import Class_
    class_names = set(session.exec(select(Class_.name)).all())
    student_names = set(session.exec(
        select(Student.class_name)
        .where(Student.is_account_enabled.is_(True))
        .distinct()
    ).all())
    return sorted(class_names | student_names)


def disable_students_by_class(session: Session, class_name: str) -> int:
    """批量禁用指定班级的所有学生账号（学期归档）

    只更新当前处于启用状态的学生，重复调用返回 0（幂等）。
    历史数据（签到/分数记录）保留，仅账号无法登录。

    Args:
        session: 数据库会话
        class_name: 班级名称

    Returns:
        int: 本次禁用的学生数量
    """
    from sqlalchemy import update
    result = session.exec(
        update(Student)
        .where(
            class_filter(
                Student.class_id, Student.class_name,
                get_class_id_by_name(session, class_name), class_name,
            ),
            Student.is_account_enabled.is_(True),
        )
        .values(is_account_enabled=False)
    )
    session.commit()
    return result.rowcount


def count_students(session: Session, include_disabled: bool = False) -> int:
    """使用 SQL COUNT 计算学生总数（性能优化）

    相比 get_students() + len()，此函数使用数据库聚合查询，
    不加载完整对象，内存占用更少，执行更快。
    默认只统计启用学生（禁用学生不计入仪表盘等统计）。

    Args:
        session: 数据库会话
        include_disabled: 是否包含已禁用学生（默认 False）

    Returns:
        int: 学生总数
    """
    from sqlalchemy import func
    query = select(func.count()).select_from(Student)
    if not include_disabled:
        query = query.where(Student.is_account_enabled.is_(True))
    result = session.exec(query)
    return result.one()


def reset_student_password(session: Session, student_id: str, password_hash: str) -> Optional[Student]:
    """重置学生密码 - SEC-003: 移除 salt 参数；顺带解锁（与教师侧 reset_password 一致）"""
    student = get_student(session, student_id)
    if not student:
        return None
    student.password_hash = password_hash
    # SEC-003: salt 字段不再设置（bcrypt 已内置盐值）
    # 重置密码顺带解锁（防止"改了密码还被锁"的困惑）
    student.locked_until = None
    student.login_fail_count = 0
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def unlock_student_account(session: Session, student_id: str) -> Optional[Student]:
    """手动解锁学生账号（管理员/教师操作）

    Returns:
        Student: 解锁后的学生对象，不存在返回 None
    """
    student = get_student(session, student_id)
    if not student:
        return None
    student.locked_until = None
    student.login_fail_count = 0
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def record_student_login_failure(session: Session, student: Student) -> bool:
    """
    记录学生登录失败，达到上限时锁定账号 - 与 record_login_failure（user.py）同逻辑

    使用乐观锁确保并发登录失败计数准确。
    如果检测到版本冲突，自动重试最多3次。

    时区说明：locked_until 使用 naive datetime.now()，与 User 侧保持一致
    （数据库列为 timestamp without time zone，登录比较也用 naive now）。

    Args:
        session: 数据库会话
        student: 学生对象

    Returns:
        bool: 如果账号已被锁定返回 True，否则返回 False
    """
    from datetime import timedelta
    from sqlalchemy.exc import IntegrityError
    from app.core.config import get_settings

    settings = get_settings()
    max_retries = 3

    for attempt in range(max_retries):
        # 刷新学生对象获取最新版本号
        session.refresh(student)

        student.login_fail_count += 1

        if student.login_fail_count >= settings.security.max_login_failures:
            student.locked_until = datetime.now() + timedelta(
                minutes=settings.security.lockout_duration_minutes
            )

        # 乐观锁：递增版本号（与 BE-008 修复同模式）
        student.version += 1
        session.add(student)

        try:
            session.commit()
            return student.locked_until is not None
        except IntegrityError:
            session.rollback()
            if attempt == max_retries - 1:
                # 最后一次重试失败，返回保守结果（视为锁定）
                return True
            # 继续重试
            continue

    return False


def reset_student_login_lock(session: Session, student: Student) -> None:
    """登录成功后重置学生失败计数与锁定状态"""
    student.login_fail_count = 0
    student.locked_until = None
    session.add(student)
    session.commit()
