"""
学生科目分数 API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.term import get_current_term
from app.api.deps import get_current_user, require_admin_or_teacher, verify_teacher_class_access
from app.crud.student_subject_score import update_student_subject_score
from app.models import StudentSubjectScore, StudentSubjectScoreLog, Subject, Student, User
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse

router = APIRouter(tags=["student-subject-scores"])


class UpdateScoreRequest(BaseModel):
    """更新学生科目分数请求"""
    score_change: float = Field(..., description="分数变化值（正数加分，负数扣分）")
    reason: str = Field(..., min_length=1, max_length=200, description="原因")


def _verify_student_access(user: dict, student_id: str, session: Session) -> None:
    """校验访问权限：学生只能看自己，教师看自己班（admin 放行）"""
    role = user.get("role", "")
    if role == "student":
        if student_id != user.get("sub", ""):
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权查看其他学生信息")
    elif role == "teacher":
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
        verify_teacher_class_access(user, student.class_name, session)


@router.get("/students/{student_id}/subjects", response_model=ApiResponse[List[dict]])
def get_student_subjects(
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生所有科目分数（学生只能看自己，教师看自己班）"""
    # 权限校验
    _verify_student_access(user, student_id, session)

    # 查询当前学期的所有科目分数
    scores = session.exec(
        select(StudentSubjectScore, Subject, User)
        .join(Subject, StudentSubjectScore.subject_id == Subject.id)
        .join(User, StudentSubjectScore.teacher_id == User.id)
        .where(
            StudentSubjectScore.student_id == student_id,
            StudentSubjectScore.semester == get_current_term(),
        )
    ).all()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "subject_id": score.subject_id,
                "subject_name": subject.name,
                "teacher_id": score.teacher_id,
                "teacher_name": teacher.name,
                "score": score.score,
            }
            for score, subject, teacher in scores
        ]
    }


@router.put("/students/{student_id}/subjects/{subject_id}/score", response_model=ApiSuccessResponse)
def update_score(
    student_id: str,
    subject_id: int,
    data: UpdateScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """更新学生科目分数（admin 或负责该班的教师）"""
    # 权限校验
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
    verify_teacher_class_access(user, student.class_name, session)

    # 更新分数
    username = user.get("username", "")
    result = update_student_subject_score(session, student_id, subject_id, data.score_change, data.reason, username)
    if not result:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生科目分数记录不存在")

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "分数已更新"
    }


@router.get("/students/{student_id}/subjects/{subject_id}/logs", response_model=ApiResponse[List[dict]])
def get_student_subject_score_logs(
    student_id: str,
    subject_id: int,
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生某科目分数历史（学生只能看自己，教师看自己班）"""
    # 权限校验
    _verify_student_access(user, student_id, session)

    # 查询日志
    logs = session.exec(
        select(StudentSubjectScoreLog)
        .where(
            StudentSubjectScoreLog.student_id == student_id,
            StudentSubjectScoreLog.subject_id == subject_id,
            StudentSubjectScoreLog.semester == get_current_term(),
        )
        .order_by(StudentSubjectScoreLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "old_score": log.old_score,
                "new_score": log.new_score,
                "delta": log.delta,
                "reason": log.reason,
                "operator": log.operator,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }
