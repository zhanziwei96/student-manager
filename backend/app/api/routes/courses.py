"""
课程目录管理 API — 创建/更新/归档
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import require_admin, require_admin_or_teacher
from app.core.config import HttpStatus
from app.core.db import get_session
from app.models import Course
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["courses"])


class CreateCourseRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=20, description="课程编码（如 MATH1001）")
    name: str = Field(..., min_length=1, max_length=100, description="课程名称")
    department: str = Field(default="", max_length=50, description="开课院系")


class UpdateCourseRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    department: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, description="active|archived")


def _course_dict(c: Course) -> dict:
    return {
        "id": c.id,
        "code": c.code,
        "name": c.name,
        "department": c.department,
        "status": c.status,
    }


@router.get("/courses", response_model=ApiResponse[list])
def list_courses(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """课程目录列表"""
    courses = session.exec(select(Course).order_by(Course.code)).all()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [_course_dict(c) for c in courses]}


@router.post("/courses", response_model=ApiResponse[dict])
def create_course(
    body: CreateCourseRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """创建课程"""
    exists = session.exec(select(Course).where(Course.code == body.code)).first()
    if exists:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail="课程编码已存在")
    course = Course(code=body.code, name=body.name, department=body.department, status="active")
    session.add(course)
    session.commit()
    session.refresh(course)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _course_dict(course),
            ApiResponseConst.MESSAGE: "课程创建成功"}


@router.put("/courses/{course_id}", response_model=ApiResponse[dict])
def update_course(
    course_id: int,
    body: UpdateCourseRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """更新课程（名称/院系/归档）"""
    course = session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课程不存在")
    if body.name is not None:
        course.name = body.name
    if body.department is not None:
        course.department = body.department
    if body.status is not None:
        if body.status not in ("active", "archived"):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="无效状态")
        course.status = body.status
    session.add(course)
    session.commit()
    session.refresh(course)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _course_dict(course),
            ApiResponseConst.MESSAGE: "课程更新成功"}
