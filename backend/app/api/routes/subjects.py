"""
科目管理 API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.term import get_current_term
from app.api.deps import require_admin_or_teacher
from app.crud.subject import (
    get_subjects_by_semester,
    create_subject,
    update_subject_name,
    derive_subjects_and_teachers,
)
from app.models import Subject
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse

router = APIRouter(tags=["subjects"])


class UpdateSubjectRequest(BaseModel):
    """修改科目名称请求"""
    name: str = Field(..., min_length=1, max_length=100, description="科目名称")


@router.get("/subjects", response_model=ApiResponse[List[dict]])
def get_subjects(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取科目列表（当前学期）"""
    subjects = get_subjects_by_semester(session)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "id": s.id,
                "name": s.name,
                "semester": s.semester,
            }
            for s in subjects
        ]
    }


@router.put("/subjects/{subject_id}", response_model=ApiSuccessResponse)
def update_subject(
    subject_id: int,
    data: UpdateSubjectRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """修改科目名称"""
    subject = update_subject_name(session, subject_id, data.name)
    if not subject:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="科目不存在")

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "科目已更新"
    }


@router.post("/subjects/derive", response_model=ApiResponse[dict])
def derive_subjects(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """从课表推导科目（当前学期）"""
    subject_teachers = derive_subjects_and_teachers(session)

    # 为每个科目创建记录（若不存在）
    created_count = 0
    for class_name, subjects in subject_teachers.items():
        for subject_name in subjects.keys():
            existing = session.exec(
                select(Subject).where(
                    Subject.name == subject_name,
                    Subject.semester == get_current_term()
                )
            ).first()
            if not existing:
                create_subject(session, subject_name)
                created_count += 1

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已推导 {created_count} 个科目",
        ApiResponseConst.DATA: {"created_count": created_count}
    }
