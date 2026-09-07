# backend/app/api/routes/leaderboard.py
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.core.db import get_session
from app.core.jwt import get_current_user
from app.crud import get_leaderboard
from app.crud.leaderboard import get_subject_leaderboard
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["leaderboard"])


class LeaderboardResponse(ApiResponse[dict]):
    """排行榜响应"""
    pass


@router.get("/students/leaderboard", response_model=LeaderboardResponse)
def get_student_leaderboard(
    scope: str = Query("class", description="范围: class 或 school"),
    class_name: Optional[str] = Query(None, description="班级名称（scope=class 时）"),
    subject_id: Optional[int] = Query(None, description="科目ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """
    获取学生排行榜（支持按教师+科目聚合）

    - subject_id + teacher_id：按教师+科目排（如"张老师的数学"）
    - 只有 subject_id：按科目排（全校数学排名）
    - 只有 teacher_id：按教师排（张老师教的所有科目）
    - 都不传：按 scope/class_name 排（现有逻辑）
    """
    # 获取当前学生ID
    current_student_id = None
    if user.get("role") == "student":
        current_student_id = user.get("sub")

    # 如果有 subject_id 或 teacher_id，按科目分数排
    if subject_id or teacher_id:
        data = get_subject_leaderboard(
            session,
            subject_id=subject_id,
            teacher_id=teacher_id,
            limit=limit,
            current_student_id=current_student_id
        )
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: data
        }

    # 如果 scope=class 但没有提供 class_name，尝试从学生信息获取
    if scope == "class" and not class_name and current_student_id:
        from app.crud import get_student
        student = get_student(session, current_student_id)
        if student:
            class_name = student.class_name

    data = get_leaderboard(
        session,
        scope=scope,
        class_name=class_name,
        limit=limit,
        current_student_id=current_student_id
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: data
    }
