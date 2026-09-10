"""
班级管理 API — 创建/更新/删除（届+专业下的班）
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

from app.api.deps import require_admin, require_admin_or_teacher
from app.core.class_cache import invalidate_class_cache
from app.core.config import HttpStatus
from app.core.db import get_session
from app.models import (
    CheckinRecord, Class_, ClassGroupSettings, Cohort, CourseSchedule,
    CourseSession, Group, Question, Student, StudentClassSemester,
)
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["classes"])

# 引用 classes.id 的外键表（均未配置 ondelete → RESTRICT）：
# 删除班级前逐表检查，命中则 409 说明来源，避免外键冲突变成 500
_CLASS_REFERENCES = (
    ("学生", "人", Student, Student.class_id),
    ("班级归属记录", "条", StudentClassSemester, StudentClassSemester.class_id),
    ("课表", "条", CourseSchedule, CourseSchedule.class_id),
    ("课堂", "条", CourseSession, CourseSession.class_id),
    ("签到记录", "条", CheckinRecord, CheckinRecord.class_id),
    ("小组", "个", Group, Group.class_id),
    ("小组设置", "条", ClassGroupSettings, ClassGroupSettings.class_id),
    ("问题", "条", Question, Question.class_id),
)


class CreateClassRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="班级名（如 1班）")
    major: str = Field(default="", max_length=50, description="专业")
    cohort_year: str = Field(..., min_length=4, max_length=10, description="所属届")


class UpdateClassRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    major: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, description="状态: active|archived")


def _class_dict(cls: Class_, student_count: int = 0) -> dict:
    return {
        "id": cls.id,
        "name": cls.name,
        "major": cls.major,
        "cohort_year": cls.cohort_year,
        "display_name": f"{cls.cohort_year}届{cls.major}{cls.name}",
        "student_count": student_count,
        "status": cls.status,
    }


@router.get("/classes", response_model=ApiResponse[list])
def list_classes(
    cohort_year: Optional[str] = Query(None, description="按届过滤"),
    include_archived: bool = Query(False, description="是否包含已归档班级"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """班级列表（默认只返回在用班级；可按届过滤，含学生数）"""
    query = select(Class_).order_by(Class_.cohort_year, Class_.name)
    if cohort_year:
        query = query.where(Class_.cohort_year == cohort_year)
    if not include_archived:
        query = query.where(Class_.status == "active")
    classes = session.exec(query).all()
    counts = {
        row[0]: row[1] for row in session.exec(
            select(Student.class_id, func.count())
            .where(Student.class_id.is_not(None))
            .group_by(Student.class_id)
        ).all()
    }
    return {ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: [_class_dict(c, counts.get(c.id, 0)) for c in classes]}


@router.post("/classes", response_model=ApiResponse[dict])
def create_class(
    body: CreateClassRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """创建班级"""
    if session.get(Cohort, body.cohort_year) is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="届不存在，请先创建届")
    exists = session.exec(select(Class_).where(
        Class_.name == body.name,
        Class_.major == body.major,
        Class_.cohort_year == body.cohort_year,
    )).first()
    if exists:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail="同届同专业下班级已存在")
    cls = Class_(name=body.name, major=body.major, cohort_year=body.cohort_year)
    session.add(cls)
    session.commit()
    session.refresh(cls)
    invalidate_class_cache()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _class_dict(cls),
            ApiResponseConst.MESSAGE: "班级创建成功"}


@router.put("/classes/{class_id}", response_model=ApiResponse[dict])
def update_class(
    class_id: int,
    body: UpdateClassRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """更新班级（改名/专业）"""
    cls = session.get(Class_, class_id)
    if cls is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="班级不存在")
    if body.name is not None:
        cls.name = body.name
    if body.major is not None:
        cls.major = body.major
    if body.status is not None:
        if body.status not in ("active", "archived"):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="无效状态")
        cls.status = body.status
    session.add(cls)
    session.commit()
    session.refresh(cls)
    invalidate_class_cache()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _class_dict(cls),
            ApiResponseConst.MESSAGE: "班级更新成功"}


@router.delete("/classes/{class_id}", response_model=ApiResponse[dict])
def delete_class(
    class_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """删除班级（RESTRICT：仍被学生/课表/课堂等引用时拒绝，并说明引用来源）"""
    cls = session.get(Class_, class_id)
    if cls is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="班级不存在")

    refs = []
    for label, unit, model, column in _CLASS_REFERENCES:
        count = session.exec(
            select(func.count()).select_from(model).where(column == class_id)
        ).one()
        if count > 0:
            refs.append(f"{label} {count} {unit}")
    if refs:
        raise HTTPException(
            status_code=HttpStatus.CONFLICT,
            detail="该班级仍被引用：" + "、".join(refs) + "，请先处理后再删除",
        )

    session.delete(cls)
    session.commit()
    invalidate_class_cache()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.MESSAGE: "班级已删除"}
