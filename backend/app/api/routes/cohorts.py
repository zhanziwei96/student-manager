"""
届管理 API — 创建/更新/毕业归档
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import require_admin, require_admin_or_teacher
from app.core.config import HttpStatus
from app.core.db import get_session
from app.models import Cohort
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["cohorts"])


class CreateCohortRequest(BaseModel):
    year: str = Field(..., min_length=4, max_length=10, description="届（入学年份，如 2026）")
    label: str = Field(default="", max_length=50, description="显示名（如 2026届）")


class UpdateCohortRequest(BaseModel):
    label: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, description="active|graduated")


def _cohort_dict(c: Cohort) -> dict:
    return {
        "year": c.year,
        "label": c.label or f"{c.year}届",
        "entry_semester_id": c.entry_semester_id,
        "status": c.status,
    }


@router.get("/cohorts", response_model=ApiResponse[list])
def list_cohorts(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """届列表"""
    cohorts = session.exec(select(Cohort).order_by(Cohort.year)).all()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [_cohort_dict(c) for c in cohorts]}


@router.post("/cohorts", response_model=ApiResponse[dict])
def create_cohort(
    body: CreateCohortRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """创建届"""
    if session.get(Cohort, body.year) is not None:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail="该届已存在")
    cohort = Cohort(year=body.year, label=body.label or f"{body.year}届", status="active")
    session.add(cohort)
    session.commit()
    session.refresh(cohort)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _cohort_dict(cohort),
            ApiResponseConst.MESSAGE: "届创建成功"}


@router.put("/cohorts/{year}", response_model=ApiResponse[dict])
def update_cohort(
    year: str,
    body: UpdateCohortRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """更新届（显示名/毕业归档/恢复）"""
    cohort = session.get(Cohort, year)
    if cohort is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="届不存在")
    if body.label is not None:
        cohort.label = body.label
    if body.status is not None:
        if body.status not in ("active", "graduated"):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="无效状态")
        cohort.status = body.status
    session.add(cohort)
    session.commit()
    session.refresh(cohort)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _cohort_dict(cohort),
            ApiResponseConst.MESSAGE: "届更新成功"}
