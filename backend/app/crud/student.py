"""
学生 CRUD 操作 - 使用领域事件模式
"""
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
    更新学生分数 - 领域事件模式重构
    
    事务边界明确：
    1. 更新学生分数（主业务）- 在同一会话中
    2. 记录分数日志（副作用）- 在同一会话中原子提交
    3. 发布领域事件 - 用于其他副作用（审计、通知等）
    
    这种设计实现了：
    - 单一事务：主业务和核心副作用在同一个事务中提交
    - 职责分离：CRUD 协调操作，副作用逻辑由事件处理器封装
    - 可扩展性：新增副作用只需添加处理器，无需修改原函数
    
    Args:
        session: 数据库会话
        student_id: 学生学号
        delta: 分数变动值
        reason: 变动原因
        operator: 操作人
        
    Returns:
        Student: 更新后的学生对象，如果不存在则返回 None
    """
    student = get_student(session, student_id)
    if not student:
        return None
    
    # 执行业务操作：更新分数（通过领域方法封装业务规则）
    old_score, new_score = student.update_score(delta)
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
    # 使用事件处理器模式，但在同一 session 中执行
    score_log = ScoreLog(
        student_id=student_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator
    )
    session.add(score_log)
    
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
