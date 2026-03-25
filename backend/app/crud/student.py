"""
学生 CRUD 操作 - 使用领域事件模式
"""
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select
from sqlalchemy import event as sa_event
from app.models import Student, ScoreLog, User
from app.core.events import ScoreUpdated, event_bus


def get_students_by_permission(
    session: Session, 
    user: Dict, 
    class_name: Optional[str] = None
) -> Tuple[List[Student], Optional[str]]:
    """
    根据用户权限获取学生列表
    
    将权限检查逻辑从 API 层移至 CRUD 层，实现关注点分离。
    API 层只负责 HTTP 协议转换，业务逻辑在 CRUD 层处理。
    
    Args:
        session: 数据库会话
        user: 当前用户信息（JWT token payload）
        class_name: 可选的班级名称过滤
        
    Returns:
        Tuple[List[Student], Optional[str]]: 
            - 成功时: (学生列表, None)
            - 权限不足时: (None, 错误信息)
    """
    is_admin = user.get("is_admin", False)
    
    if is_admin:
        # 管理员可以查看所有学生
        if class_name:
            return get_students_by_class(session, class_name), None
        return get_students(session), None
    
    # 教师逻辑
    user_id = user.get("sub")
    if not user_id:
        return None, "无效的用户信息"
    
    user_obj = session.get(User, int(user_id))
    assigned_classes = user_obj.get_assigned_classes() if user_obj else []
    
    if not assigned_classes:
        return [], None
    
    # 如果指定了班级，检查权限
    if class_name:
        if class_name not in assigned_classes:
            return None, "无权查看该班级学生"
        return get_students_by_class(session, class_name), None
    
    # 获取所有负责班级的学生
    students = []
    for cls in assigned_classes:
        students.extend(get_students_by_class(session, cls))
    
    # 去重（防止同一学生在多个班级的情况）
    seen = set()
    unique_students = []
    for s in students:
        if s.student_id not in seen:
            seen.add(s.student_id)
            unique_students.append(s)
    
    return unique_students, None


def get_classes_by_permission(
    session: Session,
    user: Dict
) -> Tuple[List[str], Optional[str]]:
    """
    根据用户权限获取班级列表
    
    Args:
        session: 数据库会话
        user: 当前用户信息
        
    Returns:
        Tuple[List[str], Optional[str]]:
            - 成功时: (班级列表, None)
            - 权限不足时: (None, 错误信息)
    """
    is_admin = user.get("is_admin", False)
    
    if is_admin:
        # 管理员可以看到所有班级
        return get_all_classes(session), None
    
    # 教师只能看到负责的班级
    user_id = user.get("sub")
    if not user_id:
        return None, "无效的用户信息"
    
    user_obj = session.get(User, int(user_id))
    assigned_classes = user_obj.get_assigned_classes() if user_obj else []
    
    return assigned_classes, None


def get_student(session: Session, student_id: str) -> Optional[Student]:
    """根据学号获取学生"""
    return session.get(Student, student_id)


def get_students(session: Session, class_name: Optional[str] = None) -> List[Student]:
    """获取学生列表"""
    query = select(Student)
    if class_name:
        query = query.where(Student.class_name == class_name)
    return session.exec(query).all()


def get_students_by_class(session: Session, class_name: str) -> List[Student]:
    """根据班级获取学生"""
    query = select(Student).where(Student.class_name == class_name)
    return session.exec(query).all()


def create_student(session: Session, student_id: str, name: str, class_name: str, score: float = None) -> Student:
    """创建学生"""
    from app.core.config import get_settings
    from app.core.security import generate_password_hash
    settings = get_settings()
    
    if score is None:
        score = settings.score.default_score
    
    # 使用学号作为默认密码
    password_hash, salt = generate_password_hash(student_id)
    
    student = Student(
        student_id=student_id,
        name=name,
        class_name=class_name,
        score=score,
        password_hash=password_hash,
        salt=salt
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
    from sqlalchemy.exc import IntegrityError
    from fastapi import HTTPException
    
    # 获取学生（使用 select 确保获取最新版本号）
    statement = select(Student).where(Student.student_id == student_id)
    student = session.exec(statement).first()
    
    if not student:
        return None
    
    # 执行业务操作：更新分数（通过领域方法封装业务规则）
    old_score, new_score = student.update_score(delta)
    
    # 乐观锁：递增版本号（BE-008 修复）
    student.version += 1
    
    session.add(student)
    
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
    
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="分数已被其他用户修改，请刷新后重试"
        )
    
    # 注册事务提交后的回调，用于处理其他非核心副作用
    # 使用 SQLAlchemy 的事件机制确保事件在事务成功提交后才发布
    # 这样可以保证：
    # 1. 如果业务提交失败，事件不会发布
    # 2. 避免事件处理成功但业务数据回滚的不一致情况
    @sa_event.listens_for(session, "after_commit")
    def publish_event_once(session):
        event_bus.publish(event)
        # 移除监听器避免重复
        sa_event.remove(session, "after_commit", publish_event_once)
    
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


def reset_student_password(session: Session, student_id: str, password_hash: str, salt: str) -> Optional[Student]:
    """重置学生密码"""
    student = get_student(session, student_id)
    if not student:
        return None
    student.password_hash = password_hash
    student.salt = salt
    session.add(student)
    session.commit()
    session.refresh(student)
    return student
