"""
教学班管理 API — 开课/排教师/选课名单
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, func, select

from app.api.deps import require_admin, require_admin_or_teacher
from app.core.config import HttpStatus
from app.core.db import get_session
from app.models import Course, CourseOffering, Enrollment, Semester, Student
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["course-offerings"])


class CreateOfferingRequest(BaseModel):
    course_id: int = Field(..., description="课程ID")
    semester_id: int = Field(..., description="学期ID")
    teacher_id: Optional[int] = Field(default=None, description="教师ID（可空：先排课后定教师）")
    class_scope: str = Field(..., min_length=1, max_length=100, description="面向范围（如 计科1-2班）")
    capacity: Optional[int] = Field(default=None, ge=1, description="容量")


class UpdateOfferingRequest(BaseModel):
    teacher_id: Optional[int] = None
    class_scope: Optional[str] = Field(default=None, min_length=1, max_length=100)
    capacity: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(default=None, description="active|ended")


class ImportEnrollmentsRequest(BaseModel):
    student_ids: List[str] = Field(..., description="学号列表（批量导入选课）")


def _offering_dict(o: CourseOffering) -> dict:
    return {
        "id": o.id,
        "course_id": o.course_id,
        "semester_id": o.semester_id,
        "teacher_id": o.teacher_id,
        "teacher_name": o.teacher_name,
        "class_scope": o.class_scope,
        "capacity": o.capacity,
        "status": o.status,
    }


@router.get("/offerings", response_model=ApiResponse[list])
def list_offerings(
    semester_id: Optional[int] = Query(None, description="按学期过滤（缺省当前学期）"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教学班列表（可按学期过滤）"""
    from app.core.term import get_current_semester_id
    if semester_id is None:
        semester_id = get_current_semester_id(session)
    query = select(CourseOffering).order_by(CourseOffering.id)
    if semester_id is not None:
        query = query.where(CourseOffering.semester_id == semester_id)
    offerings = session.exec(query).all()
    return {ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: [_offering_dict(o) for o in offerings]}


@router.post("/offerings", response_model=ApiResponse[dict])
def create_offering(
    body: CreateOfferingRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """创建教学班（开课）"""
    if session.get(Course, body.course_id) is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="课程不存在")
    if session.get(Semester, body.semester_id) is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="学期不存在")
    teacher_name = ""
    if body.teacher_id is not None:
        from app.models import User
        teacher = session.get(User, body.teacher_id)
        if teacher is None:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="教师不存在")
        teacher_name = teacher.name
    offering = CourseOffering(
        course_id=body.course_id, semester_id=body.semester_id,
        teacher_id=body.teacher_id, teacher_name=teacher_name,
        class_scope=body.class_scope, capacity=body.capacity, status="active",
    )
    session.add(offering)
    session.commit()
    session.refresh(offering)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _offering_dict(offering),
            ApiResponseConst.MESSAGE: "教学班创建成功"}


@router.put("/offerings/{offering_id}", response_model=ApiResponse[dict])
def update_offering(
    offering_id: int,
    body: UpdateOfferingRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """更新教学班（排教师/范围/容量/结课）"""
    offering = session.get(CourseOffering, offering_id)
    if offering is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="教学班不存在")
    if body.teacher_id is not None:
        from app.models import User
        teacher = session.get(User, body.teacher_id)
        if teacher is None:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="教师不存在")
        offering.teacher_id = teacher.id
        offering.teacher_name = teacher.name
    if body.class_scope is not None:
        offering.class_scope = body.class_scope
    if body.capacity is not None:
        offering.capacity = body.capacity
    if body.status is not None:
        if body.status not in ("active", "ended"):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="无效状态")
        offering.status = body.status
    session.add(offering)
    session.commit()
    session.refresh(offering)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: _offering_dict(offering),
            ApiResponseConst.MESSAGE: "教学班更新成功"}


@router.get("/teacher/offerings", response_model=ApiResponse[list])
def list_teacher_offerings(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """我的教学班：本学期本人授课列表（含课程信息与选课人数）"""
    from app.core.term import get_current_semester_id
    from app.models import Course

    query = (
        select(CourseOffering, Course, func.count(Enrollment.id))
        .join(Course, CourseOffering.course_id == Course.id)
        .outerjoin(Enrollment, (Enrollment.offering_id == CourseOffering.id)
                   & (Enrollment.status == "enrolled"))
        .group_by(CourseOffering.id, Course.id)
    )
    if user.get("role") != "admin":
        query = query.where(CourseOffering.teacher_id == int(user.get("sub")))
    semester_id = get_current_semester_id(session)
    if semester_id is not None:
        query = query.where(CourseOffering.semester_id == semester_id)
    rows = session.exec(query.order_by(Course.name)).all()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [
        {
            "id": o.id, "course_id": o.course_id, "course_name": c.name,
            "course_code": c.code, "teacher_name": o.teacher_name,
            "class_scope": o.class_scope, "capacity": o.capacity,
            "status": o.status, "enrolled_count": cnt,
        }
        for o, c, cnt in rows
    ]}


@router.get("/offerings/{offering_id}/enrollments", response_model=ApiResponse[list])
def list_offering_enrollments(
    offering_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """教学班选课名单（教师限本人授课教学班）"""
    offering = session.get(CourseOffering, offering_id)
    if offering is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="教学班不存在")
    if user.get("role") != "admin" and offering.teacher_id != int(user.get("sub")):
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权查看该教学班名单")
    rows = session.exec(
        select(Enrollment, Student)
        .join(Student, Enrollment.student_id == Student.student_id)
        .where(Enrollment.offering_id == offering_id, Enrollment.status == "enrolled")
        .order_by(Student.student_id)
    ).all()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [
        {
            "enrollment_id": e.id,
            "student_id": s.student_id,
            "name": s.name,
            "class_name": s.class_name,
            "score": e.score,
            "final_score": e.final_score,
        }
        for e, s in rows
    ]}


@router.post("/offerings/{offering_id}/enrollments", response_model=ApiResponse[dict])
def import_enrollments(
    offering_id: int,
    body: ImportEnrollmentsRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """批量导入选课名单"""
    offering = session.get(CourseOffering, offering_id)
    if offering is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="教学班不存在")

    imported, skipped = 0, 0
    for student_id in body.student_ids:
        if session.get(Student, student_id) is None:
            skipped += 1
            continue
        exists = session.exec(select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.offering_id == offering_id,
        )).first()
        if exists:
            exists.status = "enrolled"  # 已退课的恢复
            session.add(exists)
            imported += 1
            continue
        session.add(Enrollment(
            student_id=student_id, offering_id=offering_id,
            semester_id=offering.semester_id, status="enrolled",
        ))
        imported += 1
    session.commit()
    return {ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {"imported": imported, "skipped": skipped},
            ApiResponseConst.MESSAGE: f"导入 {imported} 人，跳过 {skipped} 人"}


@router.put("/enrollments/{enrollment_id}/drop", response_model=ApiResponse[dict])
def drop_enrollment(
    enrollment_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """退课标记（保留历史）"""
    enrollment = session.get(Enrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="选课记录不存在")
    enrollment.status = "dropped"
    session.add(enrollment)
    session.commit()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.MESSAGE: "已退课"}
