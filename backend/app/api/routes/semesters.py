"""
学期管理 API — 创建/更新/切换当前学期/rollover
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import require_admin, require_admin_or_teacher
from app.core.config import HttpStatus
from app.core.db import get_session
from app.core.term import get_current_semester, invalidate_semester_cache
from app.core.timezone import get_now
from app.models import Semester
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse

router = APIRouter(tags=["semesters"])


class CreateSemesterRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=20, description="学期标识（如 2026-2027-1）")
    start_date: date = Field(..., description="开学第一天")
    total_weeks: int = Field(..., ge=1, le=30, description="总周数")


class UpdateSemesterRequest(BaseModel):
    start_date: Optional[date] = None
    total_weeks: Optional[int] = Field(default=None, ge=1, le=30)
    status: Optional[str] = Field(default=None, description="active|archived")


def _semester_dict(sem: Semester) -> dict:
    return {
        "id": sem.id,
        "label": sem.label,
        "start_date": sem.start_date.isoformat(),
        "total_weeks": sem.total_weeks,
        "is_current": sem.is_current,
        "status": sem.status,
    }


@router.get("/semesters", response_model=ApiResponse[list])
def list_semesters(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """学期列表"""
    semesters = session.exec(select(Semester).order_by(Semester.label)).all()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [_semester_dict(s) for s in semesters]}


@router.post("/semesters", response_model=ApiResponse[dict])
def create_semester(
    body: CreateSemesterRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """创建学期"""
    exists = session.exec(select(Semester).where(Semester.label == body.label)).first()
    if exists:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail="学期标识已存在")
    sem = Semester(
        label=body.label, start_date=body.start_date, total_weeks=body.total_weeks,
        is_current=False, status="active",
    )
    session.add(sem)
    session.commit()
    session.refresh(sem)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _semester_dict(sem),
            ApiResponseConst.MESSAGE: "学期创建成功"}


@router.put("/semesters/{semester_id}", response_model=ApiResponse[dict])
def update_semester(
    semester_id: int,
    body: UpdateSemesterRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """更新学期（起止/周数/归档）"""
    sem = session.get(Semester, semester_id)
    if sem is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学期不存在")
    if body.start_date is not None:
        sem.start_date = body.start_date
    if body.total_weeks is not None:
        sem.total_weeks = body.total_weeks
    if body.status is not None:
        if body.status not in ("active", "archived"):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="无效状态")
        sem.status = body.status
    session.add(sem)
    session.commit()
    session.refresh(sem)
    invalidate_semester_cache()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _semester_dict(sem),
            ApiResponseConst.MESSAGE: "学期更新成功"}


@router.post("/semesters/{semester_id}/activate", response_model=ApiSuccessResponse)
def activate_semester(
    semester_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """切换当前学期（互斥标记 + 缓存失效）"""
    sem = session.get(Semester, semester_id)
    if sem is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学期不存在")

    from sqlalchemy import update
    session.execute(update(Semester).values(is_current=False))
    session.execute(update(Semester).where(Semester.id == semester_id).values(is_current=True))
    session.commit()
    invalidate_semester_cache()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.MESSAGE: f"已切换到 {sem.label}"}


@router.post("/semesters/rollover", response_model=ApiSuccessResponse)
def rollover_semester(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """学期切换 rollover：复制行政班归属/开课计划/选课名单到新的当前学期

    前置条件：目标学期已存在且已 activate。复制内容：
    - student_class_semesters：上一学期归属 → 当前学期（active 学生）
    - course_offerings：上一学期 active 教学班 → 当前学期（教师默认留任）
    - enrollments：上一学期 enrolled 选课 → 当前学期（按 course_id 映射新教学班）
    """
    from sqlalchemy import literal
    from sqlalchemy.dialects.postgresql import insert
    from sqlalchemy.orm import aliased
    from app.models import CourseOffering, Enrollment, Student, StudentClassSemester

    current = get_current_semester(session)
    if current is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="当前学期未设置")

    # 上一学期：非当前且 status=active 中 label 最新的一个
    previous = session.exec(select(Semester).where(
        Semester.is_current.is_(False), Semester.status == "active",
    ).order_by(Semester.label.desc())).first()
    if previous is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="没有可复制的上一学期")

    # 1. 行政班归属
    session.execute(insert(StudentClassSemester).from_select(
        ["student_id", "class_id", "semester_id", "created_at"],
        select(
            StudentClassSemester.student_id,
            StudentClassSemester.class_id,
            literal(current.id),
            literal(get_now()),
        ).where(
            StudentClassSemester.semester_id == previous.id,
            StudentClassSemester.student_id.in_(
                select(Student.student_id).where(Student.status == "active")
            ),
        ),
    ).on_conflict_do_nothing(index_elements=["student_id", "semester_id"]))

    # 2. 开课计划
    session.execute(insert(CourseOffering).from_select(
        ["course_id", "semester_id", "teacher_id", "teacher_name", "class_scope",
         "capacity", "status", "created_at"],
        select(
            CourseOffering.course_id,
            literal(current.id),
            CourseOffering.teacher_id,
            CourseOffering.teacher_name,
            CourseOffering.class_scope,
            CourseOffering.capacity,
            literal("active"),
            literal(get_now()),
        ).where(
            CourseOffering.semester_id == previous.id,
            CourseOffering.status == "active",
        ),
    ))
    session.commit()

    # 3. 选课名单（新旧教学班按 course_id + teacher_id 映射）
    new_offering = aliased(CourseOffering)
    session.execute(insert(Enrollment).from_select(
        ["student_id", "offering_id", "semester_id", "status", "score", "final_score",
         "version", "created_at", "updated_at"],
        select(
            Enrollment.student_id,
            new_offering.id,
            literal(current.id),
            literal("enrolled"),
            literal(0.0),
            literal(None),
            literal(1),
            literal(get_now()),
            literal(get_now()),
        )
        .select_from(Enrollment)
        .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
        .join(new_offering,
              (new_offering.course_id == CourseOffering.course_id)
              & (new_offering.teacher_id == CourseOffering.teacher_id))
        .where(
            Enrollment.semester_id == previous.id,
            Enrollment.status == "enrolled",
            new_offering.semester_id == current.id,
        ),
    ).on_conflict_do_nothing(index_elements=["student_id", "offering_id"]))
    session.commit()

    return {ApiResponseConst.SUCCESS: True,
            ApiResponseConst.MESSAGE: f"已从 {previous.label} 复制到 {current.label}"}
