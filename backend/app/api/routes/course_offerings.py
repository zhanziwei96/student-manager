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
from app.crud.enrollment import resolve_offering_class_ids, resolve_offering_scopes
from app.models import (
    Class_, Course, CourseOffering, CourseOfferingClass, Enrollment, Semester, Student,
)
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["course-offerings"])


class CreateOfferingRequest(BaseModel):
    course_id: int = Field(..., description="课程ID")
    semester_id: int = Field(..., description="学期ID")
    teacher_id: Optional[int] = Field(default=None, description="教师ID（可空：先排课后定教师）")
    class_ids: List[int] = Field(default_factory=list, description="面向班级ID列表（空=全部班级）")
    capacity: Optional[int] = Field(default=None, ge=1, description="容量")


class UpdateOfferingRequest(BaseModel):
    teacher_id: Optional[int] = None
    class_ids: Optional[List[int]] = Field(default=None, description="面向班级ID列表（空=全部班级）")
    capacity: Optional[int] = Field(default=None, ge=1)
    status: Optional[str] = Field(default=None, description="active|ended")


class ImportEnrollmentsRequest(BaseModel):
    student_ids: List[str] = Field(default_factory=list, description="学号列表（批量导入选课）")
    class_ids: List[int] = Field(default_factory=list,
                                 description="班级ID列表（该班全部在读学生一并加入）")


def _validate_class_ids(session: Session, class_ids: List[int]) -> None:
    """校验班级存在（任一不存在即 400）"""
    if not class_ids:
        return
    existing = set(session.exec(select(Class_.id).where(Class_.id.in_(class_ids))).all())
    invalid = [cid for cid in class_ids if cid not in existing]
    if invalid:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST,
                            detail=f"班级不存在: {invalid}")


def _offering_dict(o: CourseOffering, class_scope: str, class_ids: List[int]) -> dict:
    return {
        "id": o.id,
        "course_id": o.course_id,
        "semester_id": o.semester_id,
        "teacher_id": o.teacher_id,
        "teacher_name": o.teacher_name,
        "class_scope": class_scope,
        "class_ids": class_ids,
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
    scopes = resolve_offering_scopes(session, [o.id for o in offerings])
    class_ids = resolve_offering_class_ids(session, [o.id for o in offerings])
    return {ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: [
                _offering_dict(o, scopes[o.id], class_ids[o.id]) for o in offerings]}


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
    _validate_class_ids(session, body.class_ids)
    offering = CourseOffering(
        course_id=body.course_id, semester_id=body.semester_id,
        teacher_id=body.teacher_id, teacher_name=teacher_name,
        capacity=body.capacity, status="active",
    )
    session.add(offering)
    session.flush()  # 取 id 供关联行引用
    for cid in set(body.class_ids):
        session.add(CourseOfferingClass(offering_id=offering.id, class_id=cid))
    session.commit()
    session.refresh(offering)
    scope = resolve_offering_scopes(session, [offering.id])[offering.id]
    class_ids = resolve_offering_class_ids(session, [offering.id])[offering.id]
    return {ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: _offering_dict(offering, scope, class_ids),
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
    if body.class_ids is not None:
        _validate_class_ids(session, body.class_ids)
        # 整体替换关联行（权限真源）
        for old in session.exec(select(CourseOfferingClass).where(
            CourseOfferingClass.offering_id == offering.id,
        )).all():
            session.delete(old)
        for cid in set(body.class_ids):
            session.add(CourseOfferingClass(offering_id=offering.id, class_id=cid))
    if body.capacity is not None:
        offering.capacity = body.capacity
    if body.status is not None:
        if body.status not in ("active", "ended"):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="无效状态")
        offering.status = body.status
    session.add(offering)
    session.commit()
    session.refresh(offering)
    scope = resolve_offering_scopes(session, [offering.id])[offering.id]
    class_ids = resolve_offering_class_ids(session, [offering.id])[offering.id]
    return {ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: _offering_dict(offering, scope, class_ids),
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
    scopes = resolve_offering_scopes(session, [o.id for o, _, _ in rows])
    class_ids = resolve_offering_class_ids(session, [o.id for o, _, _ in rows])
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [
        {
            "id": o.id, "course_id": o.course_id, "course_name": c.name,
            "course_code": c.code, "teacher_name": o.teacher_name,
            "class_scope": scopes.get(o.id, "所有班级"),
            "class_ids": class_ids.get(o.id, []), "capacity": o.capacity,
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
    # class_name 为响应字段：按 class_id 运行时解析展示名
    from app.core.class_cache import get_class_display_names
    class_names = get_class_display_names(session, (s.class_id for _, s in rows))
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [
        {
            "enrollment_id": e.id,
            "student_id": s.student_id,
            "name": s.name,
            "class_name": class_names.get(s.class_id),
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
    """批量导入选课名单

    两种来源可单用或并用：student_ids（逐个学号）、class_ids（按班收全班在读学生）。
    """
    offering = session.get(CourseOffering, offering_id)
    if offering is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="教学班不存在")

    if not body.student_ids and not body.class_ids:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST,
                            detail="student_ids 与 class_ids 至少提供一个")

    student_ids = list(dict.fromkeys(body.student_ids))  # 去重且保序
    if body.class_ids:
        _validate_class_ids(session, body.class_ids)
        class_students = session.exec(
            select(Student.student_id).where(
                Student.class_id.in_(body.class_ids),
                Student.is_account_enabled.is_(True),
            )
        ).all()
        student_ids.extend(sid for sid in class_students if sid not in student_ids)

    imported, skipped = 0, 0
    for student_id in student_ids:
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
