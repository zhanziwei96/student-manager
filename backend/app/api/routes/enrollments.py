"""
选课成绩 API — 我的成绩查看 + 个人成绩加减分 + 期末成绩登记
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import require_admin_or_teacher, verify_teacher_class_access
from app.core.config import HttpStatus
from app.core.db import get_session
from app.core.jwt import get_current_user
from app.core.term import get_current_semester_id
from app.crud.enrollment import (
    get_student_enrollments,
    set_final_score,
    set_final_scores_for_group,
    update_enrollment_score,
)
from app.models import CourseOffering, Enrollment, Student, User
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["enrollments"])


def _operator_name(session: Session, user: dict) -> str:
    """操作人姓名（成绩日志记录用）"""
    user_id = user.get("sub")
    if user_id is None:
        return "unknown"
    user_obj = session.get(User, int(user_id))
    return user_obj.name if user_obj else "unknown"


class UpdateEnrollmentScoreRequest(BaseModel):
    score_change: float = Field(..., description="分数变化值")
    reason: str = Field(..., min_length=1, max_length=200, description="原因")


class SetFinalScoreRequest(BaseModel):
    final_score: float = Field(..., description="期末成绩")


class SetGroupFinalScoresRequest(BaseModel):
    group_id: int = Field(..., description="小组ID")
    final_score: float = Field(..., description="期末成绩（组员同分）")


@router.get("/students/{student_id}/enrollments", response_model=ApiResponse[list])
def get_enrollments(
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """我的成绩：当前学期选课列表（学生本人/本班教师/admin）"""
    role = user.get("role", "")
    if role == "student" and user.get("sub") != student_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="只能查看自己的成绩")

    student = session.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")

    if role == "teacher":
        # 未分班学生（class_id=None）任何教师都无权按班级查看其成绩
        if student.class_id is None:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权查看未分班学生的成绩")
        verify_teacher_class_access(user, student.class_id, session)

    data = get_student_enrollments(session, student_id, get_current_semester_id(session))
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: data}


@router.put("/enrollments/{enrollment_id}/score", response_model=ApiResponse[dict])
def update_score(
    enrollment_id: int,
    body: UpdateEnrollmentScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """个人成绩加减分（授课教师/管理员，乐观锁）"""
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="选课记录不存在")

    if user.get("role") != "admin":
        offering = session.get(CourseOffering, enrollment.offering_id)
        if offering is None or offering.teacher_id != int(user.get("sub")):
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权修改该教学班成绩")

    updated = update_enrollment_score(
        session, enrollment_id, body.score_change, body.reason, _operator_name(session, user),
    )
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"enrollment_id": enrollment_id, "score": updated.score},
        ApiResponseConst.MESSAGE: "分数已更新",
    }


@router.put("/enrollments/{enrollment_id}/final-score", response_model=ApiResponse[dict])
def update_final_score(
    enrollment_id: int,
    body: SetFinalScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """期末成绩登记（试卷个人分，独立于个人成绩）"""
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="选课记录不存在")

    if user.get("role") != "admin":
        offering = session.get(CourseOffering, enrollment.offering_id)
        if offering is None or offering.teacher_id != int(user.get("sub")):
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权修改该教学班成绩")

    updated = set_final_score(session, enrollment_id, body.final_score, _operator_name(session, user))
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"enrollment_id": enrollment_id, "final_score": updated.final_score},
        ApiResponseConst.MESSAGE: "期末成绩已登记",
    }


@router.put("/offerings/{offering_id}/final-scores/group", response_model=ApiResponse[dict])
def update_group_final_scores(
    offering_id: int,
    body: SetGroupFinalScoresRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """期末成绩登记（任务小组同分）：组员∩教学班选课名单全部写同分"""
    offering = session.get(CourseOffering, offering_id)
    if offering is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="教学班不存在")

    if user.get("role") != "admin" and offering.teacher_id != int(user.get("sub")):
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权修改该教学班成绩")

    affected = set_final_scores_for_group(
        session, offering_id, body.group_id, body.final_score, _operator_name(session, user),
    )
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"affected": affected},
        ApiResponseConst.MESSAGE: f"期末成绩已登记（{affected} 人）",
    }
