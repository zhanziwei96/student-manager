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
from app.models import Student, ScoreLog
from app.core.events import ScoreUpdated, event_bus


def get_student(session: Session, student_id: str) -> Optional[Student]:
    """根据学号获取学生"""
    return session.get(Student, student_id)


def get_students(session: Session, class_name: Optional[str] = None) -> List[Student]:
    """获取学生列表"""
    query = select(Student).order_by(Student.student_id)
    if class_name:
        query = query.where(Student.class_name == class_name)
    return session.exec(query).all()


def get_students_by_class(session: Session, class_name: str) -> List[Student]:
    """根据班级获取学生"""
    query = select(Student).where(Student.class_name == class_name).order_by(Student.student_id)
    return session.exec(query).all()


def get_students_by_classes(session: Session, class_names: List[str]) -> List[Student]:
    """
    根据多个班级获取学生 - 性能优化（REVIEW-P1）
    
    使用 SQL IN 查询替代循环查询，减少数据库往返次数。
    同时使用 SQL DISTINCT 去重，避免 Python 内存去重。
    
    Args:
        session: 数据库会话
        class_names: 班级名称列表
        
    Returns:
        学生列表（已去重）
    """
    from sqlalchemy import distinct
    
    if not class_names:
        return []
    
    # 使用 IN 查询一次性获取所有班级学生
    query = select(Student).where(Student.class_name.in_(class_names)).order_by(Student.student_id)
    return session.exec(query).all()


def create_student(session: Session, student_id: str, name: str, class_name: str, score: Optional[float] = None) -> Student:
    """创建学生 - SEC-003: 使用简化密码哈希接口"""
    from app.core.config import get_settings
    from app.core.security import hash_password
    settings = get_settings()
    
    if score is None:
        score = settings.score.default_score
    
    # 使用学号作为默认密码
    password_hash = hash_password(student_id)
    
    student = Student(
        student_id=student_id,
        name=name,
        class_name=class_name,
        score=score,
        password_hash=password_hash
        # SEC-003: salt 字段不再设置（bcrypt 已内置盐值）
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def update_student_score(
    session: Session, 
    student_id: str, 
    delta: float, 
    reason: str, 
    operator: str
) -> Optional[Student]:
    """
    更新学生分数 - 带乐观锁保护（BE-008 修复）
    
    事务边界明确：
    1. 更新学生分数（主业务）- 在同一会话中
    2. 记录分数日志（副作用）- 在同一会话中原子提交
    3. 发布领域事件 - 用于其他副作用（审计、通知等）
    4. 乐观锁保护 - 防止并发更新导致的数据丢失
    
    这种设计实现了：
    - 单一事务：主业务和核心副作用在同一个事务中提交
    - 职责分离：CRUD 协调操作，副作用逻辑由事件处理器封装
    - 可扩展性：新增副作用只需添加处理器，无需修改原函数
    - 并发安全：乐观锁防止并发修改导致的数据覆盖
    
    Args:
        session: 数据库会话
        student_id: 学生学号
        delta: 分数变动值
        reason: 变动原因
        operator: 操作人
        
    Returns:
        Student: 更新后的学生对象，如果不存在则返回 None
        
    Raises:
        HTTPException: 409 冲突，如果检测到并发修改
    """
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SASession
    from fastapi import HTTPException

    # 获取学生（使用 select 确保获取最新版本号）
    statement = select(Student).where(Student.student_id == student_id)
    student = session.exec(statement).first()

    if not student:
        return None

    # 执行业务操作：计算新分数（通过领域方法封装业务规则）
    old_score, new_score = student.update_score(delta)

    # 乐观锁：使用原生 UPDATE 检查 affected rows（BE-008 修复）
    # 只有版本号匹配时才更新，否则说明有其他事务已修改
    expected_version = student.version
    new_version = expected_version + 1

    # 使用底层 SQLAlchemy session.execute() 执行参数化 SQL
    sa_session: SASession = session
    result = sa_session.execute(
        text("""
            UPDATE students
            SET score = :score, version = :new_version
            WHERE student_id = :student_id AND version = :expected_version
        """),
        {
            "score": new_score,
            "new_version": new_version,
            "student_id": student_id,
            "expected_version": expected_version
        }
    )

    # 检查是否有行被更新，如果没有说明版本号已变化（并发冲突）
    if result.rowcount == 0:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="分数已被其他用户修改，请刷新后重试"
        )

    # 注意：不要在此处修改内存对象状态（student.version / student.score）。
    # 原生 UPDATE 已经正确更新了数据库，如果此时再修改内存对象，
    # session.commit() 的 dirty flush 会再次发起无条件 UPDATE，
    # 覆盖并发事务的乐观锁保护，导致 Lost Update（BE-008）。
    # commit() 后对象会被 expire，后续 lazy load 会自动读到最新值。

    # 创建领域事件
    event = ScoreUpdated(
        student_id=student_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator
    )

    # 核心副作用：记录分数日志（必须在同一事务中）
    score_log = ScoreLog(
        student_id=student_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator
    )
    session.add(score_log)

    # 使用一次性事件发布机制，确保事件只在事务成功提交后发布一次
    # 使用事件对象的 id 作为去重键，防止重复发布
    _published_events = getattr(session, '_published_events', None)
    if _published_events is None:
        _published_events = set()
        session._published_events = _published_events

    event_id = id(event)

    def _publish_event_once(session):
        # 检查事件是否已发布
        if event_id not in _published_events:
            _published_events.add(event_id)
            event_bus.publish(event)

    # 注册事务提交后的回调
    sa_event.listen(session, "after_commit", _publish_event_once, once=True)

    session.commit()

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
    """获取所有班级列表"""
    query = select(Student.class_name).distinct()
    result = session.exec(query).all()
    return [str(row) for row in result if row]


def count_students(session: Session) -> int:
    """使用 SQL COUNT 计算学生总数（性能优化）
    
    相比 get_students() + len()，此函数使用数据库聚合查询，
    不加载完整对象，内存占用更少，执行更快。
    
    Args:
        session: 数据库会话
        
    Returns:
        int: 学生总数
    """
    from sqlalchemy import func
    result = session.exec(select(func.count()).select_from(Student))
    return result.one()


def reset_student_password(session: Session, student_id: str, password_hash: str) -> Optional[Student]:
    """重置学生密码 - SEC-003: 移除 salt 参数"""
    student = get_student(session, student_id)
    if not student:
        return None
    student.password_hash = password_hash
    # SEC-003: salt 字段不再设置（bcrypt 已内置盐值）
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
