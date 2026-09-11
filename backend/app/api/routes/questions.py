"""
课堂问答 API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.db import get_session
from app.core.jwt import get_current_user
from app.api.deps import require_admin_or_teacher, verify_class_has_active_students
from app.crud.question import (
    create_question, get_question, get_questions_by_teacher,
    get_questions_by_class, close_question, count_answers,
    create_answer, get_answer, get_answers_by_question,
    update_answer, star_answer, delete_answer,
    DuplicateAnswerError,
)
from app.crud.user import get_user
from app.crud.student import get_student

router = APIRouter(tags=["questions"])


# ============== 请求/响应模型 ==============

class CreateQuestionRequest(BaseModel):
    content: str = Field(..., description="问题内容")
    class_id: Optional[int] = Field(default=None, description="目标班级ID，None表示所有班级")
    is_realtime: bool = Field(default=False, description="是否实时提问")


class CreateAnswerRequest(BaseModel):
    question_id: int = Field(..., description="问题ID")
    content: str = Field(..., description="回答内容")
    is_anonymous: bool = Field(default=False, description="是否匿名")


class CreateReplyRequest(BaseModel):
    answer_id: int = Field(..., description="父回答ID")
    content: str = Field(..., description="追问内容")


class UpdateAnswerRequest(BaseModel):
    content: str = Field(..., description="回答内容")


class QuestionListItem(BaseModel):
    id: int
    teacher_id: int
    teacher_name: Optional[str]
    class_name: Optional[str]
    content: str
    status: str
    is_realtime: bool
    answer_count: int
    created_at: str
    closed_at: Optional[str]


class AnswerItem(BaseModel):
    id: int
    question_id: int
    student_id: str
    student_name: Optional[str]
    content: str
    is_anonymous: bool
    is_starred: bool
    parent_id: Optional[int]
    created_at: str
    is_own: bool = False


# ============== 教师端路由 ==============

@router.post("/teacher/questions")
async def teacher_create_question(
    request: Request,
    req: CreateQuestionRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """老师发布问题"""
    # 学期归档后，禁用/不存在班级不可提问（class_id 为 None 表示所有班级，跳过校验）
    if req.class_id is not None:
        verify_class_has_active_students(req.class_id, session)

    teacher_id = int(user["sub"])
    question = create_question(
        session, teacher_id=teacher_id,
        content=req.content, class_id=req.class_id,
        is_realtime=req.is_realtime,
    )
    return {
        "success": True,
        "data": {"question_id": question.id},
    }


@router.get("/teacher/questions")
async def teacher_list_questions(
    request: Request,
    class_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """老师获取自己的问题列表"""
    teacher_id = int(user["sub"])
    questions = get_questions_by_teacher(session, teacher_id, class_id, status)

    from app.core.class_cache import get_class_display_names
    class_name_map = get_class_display_names(session, (q.class_id for q in questions))
    result = []
    for q in questions:
        teacher = get_user(session, q.teacher_id)
        result.append(QuestionListItem(
            id=q.id,
            teacher_id=q.teacher_id,
            teacher_name=teacher.name if teacher else None,
            class_name=class_name_map.get(q.class_id),
            content=q.content,
            status=q.status,
            is_realtime=q.is_realtime,
            answer_count=count_answers(session, q.id),
            created_at=q.created_at.isoformat(),
            closed_at=q.closed_at.isoformat() if q.closed_at else None,
        ).model_dump())
    return {"success": True, "data": result}


@router.put("/teacher/questions/{question_id}/close")
async def teacher_close_question(
    request: Request,
    question_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """老师结束问题"""
    teacher_id = int(user["sub"])
    question = get_question(session, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    if question.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="无权操作此问题")

    close_question(session, question_id)
    return {"success": True, "message": "问题已结束"}


@router.post("/teacher/answers/{answer_id}/reply")
async def teacher_reply_answer(
    request: Request,
    answer_id: int,
    req: CreateReplyRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """老师追问某条回答"""
    teacher_sub = user["sub"]
    answer = get_answer(session, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="回答不存在")

    reply = create_answer(
        session, question_id=answer.question_id,
        student_id=teacher_sub, content=req.content,
        parent_id=answer_id,
    )
    return {"success": True, "data": {"answer_id": reply.id}}


@router.put("/teacher/answers/{answer_id}/star")
async def teacher_star_answer(
    request: Request,
    answer_id: int,
    starred: bool = Query(True),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """老师标记/取消标记优秀"""
    answer = star_answer(session, answer_id, starred)
    if not answer:
        raise HTTPException(status_code=404, detail="回答不存在")
    return {"success": True, "message": "已标记优秀" if starred else "已取消标记"}


# ============== 学生端路由 ==============

@router.get("/student/questions")
async def student_list_questions(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生获取本班问题列表（含所有班级可见的问题）"""
    student = get_student(session, user.get("sub", ""))
    if student is None or student.class_id is None:
        raise HTTPException(status_code=400, detail="未设置班级")

    questions = get_questions_by_class(session, student.class_id, status="active")

    from app.core.class_cache import get_class_display_names
    class_name_map = get_class_display_names(session, (q.class_id for q in questions))
    result = []
    for q in questions:
        teacher = get_user(session, q.teacher_id)
        result.append(QuestionListItem(
            id=q.id,
            teacher_id=q.teacher_id,
            teacher_name=teacher.name if teacher else None,
            class_name=class_name_map.get(q.class_id),
            content=q.content,
            status=q.status,
            is_realtime=q.is_realtime,
            answer_count=count_answers(session, q.id),
            created_at=q.created_at.isoformat(),
            closed_at=q.closed_at.isoformat() if q.closed_at else None,
        ).model_dump())
    return {"success": True, "data": result}


@router.get("/student/questions/{question_id}/answers")
async def student_get_answers(
    request: Request,
    question_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """获取某问题的所有回答"""
    current_user_sub = user["sub"]
    is_teacher = user.get("role") in ("admin", "teacher")

    answers = get_answers_by_question(session, question_id)
    result = []
    for a in answers:
        # 获取回答者姓名：先尝试 Student 表（学号），再尝试 User 表（数字ID）
        student_obj = get_student(session, a.student_id)
        user_obj = get_user(session, int(a.student_id)) if a.student_id.isdigit() else None
        name = (student_obj.name if student_obj else None) or (user_obj.name if user_obj else None)

        show_name = is_teacher or not a.is_anonymous or a.student_id == current_user_sub
        result.append(AnswerItem(
            id=a.id,
            question_id=a.question_id,
            student_id=a.student_id if is_teacher else "",
            student_name=name if show_name else ("匿名" if a.is_anonymous else None),
            content=a.content,
            is_anonymous=a.is_anonymous,
            is_starred=a.is_starred,
            parent_id=a.parent_id,
            created_at=a.created_at.isoformat(),
            is_own=a.student_id == current_user_sub,
        ).model_dump())
    return {"success": True, "data": result}


@router.post("/student/answers")
async def student_create_answer(
    request: Request,
    req: CreateAnswerRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生提交回答"""
    student_sub = user["sub"]
    question = get_question(session, req.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")
    if question.status != "active":
        raise HTTPException(status_code=400, detail="问题已结束，无法回答")

    try:
        answer = create_answer(
            session, question_id=req.question_id,
            student_id=student_sub, content=req.content,
            is_anonymous=req.is_anonymous,
        )
    except DuplicateAnswerError:
        raise HTTPException(status_code=400, detail="您已回答过该问题")
    return {"success": True, "data": {"answer_id": answer.id}}


@router.put("/student/answers/{answer_id}")
async def student_update_answer(
    request: Request,
    answer_id: int,
    req: UpdateAnswerRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生修改自己的回答"""
    student_sub = user["sub"]
    answer = get_answer(session, answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="回答不存在")
    if answer.student_id != student_sub:
        raise HTTPException(status_code=403, detail="只能修改自己的回答")

    updated = update_answer(session, answer_id, req.content)
    return {"success": True, "data": {"answer_id": updated.id}}


@router.delete("/student/answers/{answer_id}")
async def student_delete_answer(
    request: Request,
    answer_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生删除自己的回答"""
    student_sub = user["sub"]
    answer = get_answer(session, answer_id)
    if not answer:
        raise HTTPException(status_code=403, detail="只能删除自己的回答")
    if answer.student_id != student_sub:
        raise HTTPException(status_code=403, detail="只能删除自己的回答")

    delete_answer(session, answer_id)
    return {"success": True, "message": "回答已删除"}
