"""
问答相关 CRUD 操作
"""
from typing import List, Optional
from sqlalchemy import and_, or_
from sqlmodel import Session, select, func
from app.models.question import Question, Answer
from app.core.class_cache import get_class_id_by_name
from app.core.term import get_current_term, get_current_semester_id
from app.core.transition_filters import class_filter, semester_filter
from app.core.timezone import get_now


def create_question(
    session: Session,
    teacher_id: int,
    content: str,
    class_name: Optional[str] = None,
    is_realtime: bool = False,
) -> Question:
    """创建问题"""
    question = Question(
        teacher_id=teacher_id,
        class_name=class_name,
        class_id=get_class_id_by_name(session, class_name) if class_name else None,  # 双写：FK 列
        semester_id=get_current_semester_id(session),                                # 双写：FK 列
        content=content,
        status="active",
        is_realtime=is_realtime,
    )
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


def get_question(session: Session, question_id: int) -> Optional[Question]:
    """获取单个问题"""
    return session.get(Question, question_id)


def get_questions_by_teacher(
    session: Session,
    teacher_id: int,
    class_name: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Question]:
    """获取老师当前学期的问题列表"""
    query = select(Question).where(
        Question.teacher_id == teacher_id,
        semester_filter(
            Question.semester_id, Question.semester,
            get_current_semester_id(session), get_current_term(),
        ),
    )
    if class_name:
        query = query.where(class_filter(
            Question.class_id, Question.class_name,
            get_class_id_by_name(session, class_name), class_name,
        ))
    if status:
        query = query.where(Question.status == status)
    query = query.order_by(Question.created_at.desc())
    return list(session.exec(query).all())


def get_questions_by_class(
    session: Session,
    class_name: str,
    status: Optional[str] = "active",
) -> List[Question]:
    """获取班级当前学期的问题列表（含所有班级可见的问题）"""
    query = select(Question).where(
        or_(
            class_filter(
                Question.class_id, Question.class_name,
                get_class_id_by_name(session, class_name), class_name,
            ),
            and_(Question.class_id.is_(None), Question.class_name.is_(None)),
        ),
        semester_filter(
            Question.semester_id, Question.semester,
            get_current_semester_id(session), get_current_term(),
        ),
    )
    if status:
        query = query.where(Question.status == status)
    query = query.order_by(Question.created_at.desc())
    return list(session.exec(query).all())


def close_question(session: Session, question_id: int) -> Optional[Question]:
    """结束问题"""
    question = session.get(Question, question_id)
    if question:
        question.status = "closed"
        question.closed_at = get_now()
        session.add(question)
        session.commit()
        session.refresh(question)
    return question


def count_answers(session: Session, question_id: int) -> int:
    """统计问题的回答数（只统计直接回答，不含追问）"""
    query = select(func.count()).select_from(Answer).where(
        Answer.question_id == question_id,
        Answer.parent_id.is_(None),
    )
    return session.exec(query).one()


class DuplicateAnswerError(Exception):
    """重复回答异常"""
    pass


def create_answer(
    session: Session,
    question_id: int,
    student_id: str,
    content: str,
    is_anonymous: bool = False,
    parent_id: Optional[int] = None,
) -> Answer:
    """创建回答（同一学生对同一问题只能有一条直接回答）"""
    # 应用层检查：直接回答不允许重复
    if parent_id is None:
        existing = session.exec(
            select(Answer).where(
                Answer.question_id == question_id,
                Answer.student_id == student_id,
                Answer.parent_id.is_(None),
            )
        ).first()
        if existing:
            raise DuplicateAnswerError("您已回答过该问题")

    answer = Answer(
        question_id=question_id,
        student_id=student_id,
        content=content,
        is_anonymous=is_anonymous,
        parent_id=parent_id,
    )
    session.add(answer)
    session.commit()
    session.refresh(answer)
    return answer


def get_answer(session: Session, answer_id: int) -> Optional[Answer]:
    """获取单个回答"""
    return session.get(Answer, answer_id)


def get_answers_by_question(
    session: Session,
    question_id: int,
) -> List[Answer]:
    """获取问题的所有回答（按时间排序，追问紧跟父回答）"""
    query = select(Answer).where(Answer.question_id == question_id)
    answers = list(session.exec(query).all())

    parent_answers = [a for a in answers if a.parent_id is None]
    result = []
    for parent in sorted(parent_answers, key=lambda a: a.created_at):
        result.append(parent)
        replies = [a for a in answers if a.parent_id == parent.id]
        result.extend(sorted(replies, key=lambda a: a.created_at))
    return result


def update_answer(
    session: Session,
    answer_id: int,
    content: str,
) -> Optional[Answer]:
    """修改回答内容"""
    answer = session.get(Answer, answer_id)
    if answer:
        answer.content = content
        session.add(answer)
        session.commit()
        session.refresh(answer)
    return answer


def star_answer(session: Session, answer_id: int, starred: bool = True) -> Optional[Answer]:
    """标记/取消标记优秀"""
    answer = session.get(Answer, answer_id)
    if answer:
        answer.is_starred = starred
        session.add(answer)
        session.commit()
        session.refresh(answer)
    return answer


def delete_answer(session: Session, answer_id: int) -> bool:
    """删除回答（同时删除所有追问）"""
    answer = session.get(Answer, answer_id)
    if not answer:
        return False

    # 自引用 FK（answers.parent_id → answers.id）要求自底向上删除：
    # PG 强制 FK 时，父与子不能在同一条 executemany 中删除（SQLite 无 FK 未暴露此问题）
    to_delete = [answer]
    pending = session.exec(select(Answer).where(Answer.parent_id == answer_id)).all()
    while pending:
        to_delete = list(pending) + to_delete
        pending_ids = [a.id for a in pending]
        pending = session.exec(
            select(Answer).where(Answer.parent_id.in_(pending_ids))
        ).all()

    for a in to_delete:
        session.delete(a)
        session.flush()
    session.commit()
    return True
