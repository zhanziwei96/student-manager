"""
学生 CRUD 操作
"""
from typing import List, Optional
from sqlmodel import Session, select
from app.models import Student, ScoreLog


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


def update_student_score(session: Session, student_id: str, delta: float, reason: str, operator: str) -> Optional[Student]:
    """更新学生分数"""
    from app.core.config import get_settings
    settings = get_settings()
    
    student = get_student(session, student_id)
    if not student:
        return None
    
    old_score = student.score
    min_score = settings.score.min_score
    max_score = settings.score.max_score
    new_score = max(min_score, min(max_score, old_score + delta))
    student.score = new_score
    
    session.add(student)
    session.commit()
    session.refresh(student)
    
    # 记录分数日志
    score_log = ScoreLog(
        student_id=student_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator
    )
    session.add(score_log)
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
