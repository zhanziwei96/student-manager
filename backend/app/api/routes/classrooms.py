"""教室与座位 API。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, func

from app.api.deps import get_current_user, require_admin_or_teacher
from app.core.db import get_session
from app.core.term import get_current_semester_id
from app.crud.course_session import get_active_course_session_by_class_id
from app.crud.seat import (
    ClassroomNameConflictError, SeatBrokenError, SeatLayoutConflictError,
    SeatNotFoundError, SeatOccupiedError,
    clear_seat_override, create_classroom, get_classroom, get_classroom_by_name,
    get_my_seat_assignments, get_seat_map, list_classrooms,
    set_classroom_status, set_seat_broken, set_seat_override,
    update_classroom_layout,
)
from app.models.constants import ApiResponseConst
from app.models.course_session import CourseSession
from app.models.seat import Classroom, Seat
from app.models.student import Student

router = APIRouter(tags=["classrooms"])


def ok(data):
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: data}


class ClassroomCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    rows: int = Field(ge=1, le=50)
    cols: int = Field(ge=1, le=50)


class ClassroomUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    rows: Optional[int] = Field(default=None, ge=1, le=50)
    cols: Optional[int] = Field(default=None, ge=1, le=50)
    status: Optional[str] = Field(default=None, pattern="^(active|archived)$")


class BrokenIn(BaseModel):
    is_broken: bool


class OverrideIn(BaseModel):
    student_id: str
    seat_id: int


def _classroom_out(session: Session, room: Classroom) -> dict:
    count = session.exec(
        select(func.count()).select_from(Seat).where(Seat.classroom_id == room.id)
    ).one()
    return {"id": room.id, "name": room.name, "rows": room.rows, "cols": room.cols,
            "status": room.status, "seat_count": count}


@router.get("/classrooms")
def list_all(session: Session = Depends(get_session),
             user=Depends(require_admin_or_teacher)):
    return ok([_classroom_out(session, c)
               for c in list_classrooms(session, include_archived=True)])


@router.post("/classrooms", status_code=201)
def create(body: ClassroomCreateIn, session: Session = Depends(get_session),
           user=Depends(require_admin_or_teacher)):
    try:
        room = create_classroom(session, name=body.name, rows=body.rows, cols=body.cols)
    except ClassroomNameConflictError:
        raise HTTPException(409, "教室名已存在")
    return ok(_classroom_out(session, room))


@router.put("/classrooms/{classroom_id}")
def update(classroom_id: int, body: ClassroomUpdateIn,
           session: Session = Depends(get_session),
           user=Depends(require_admin_or_teacher)):
    room = get_classroom(session, classroom_id)
    if room is None:
        raise HTTPException(404, "教室不存在")
    try:
        if body.rows is not None or body.cols is not None:
            room = update_classroom_layout(
                session, classroom_id,
                rows=body.rows if body.rows is not None else room.rows,
                cols=body.cols if body.cols is not None else room.cols,
            )
        if body.status is not None:
            room = set_classroom_status(session, classroom_id, body.status)
        if body.name is not None and body.name != room.name:
            if get_classroom_by_name(session, body.name) is not None:
                raise HTTPException(409, "教室名已存在")
            room.name = body.name
            session.add(room)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                raise HTTPException(409, "教室名已存在")
            session.refresh(room)
    except SeatLayoutConflictError as e:
        # 409 的 removed_seat_nos 需要进 data：HTTPException.detail 只会落到 message
        return JSONResponse(
            status_code=409,
            content={
                ApiResponseConst.SUCCESS: False,
                ApiResponseConst.DATA: {"removed_seat_nos": e.removed_seat_nos},
                ApiResponseConst.MESSAGE: str(e),
            },
        )
    return ok(_classroom_out(session, room))


@router.get("/classrooms/{classroom_id}/seats")
def seat_map(classroom_id: int,
             session_id: Optional[int] = Query(default=None),
             session: Session = Depends(get_session),
             user=Depends(get_current_user)):
    room = get_classroom(session, classroom_id)
    if room is None or room.status != "active":
        raise HTTPException(404, "教室不存在")

    role = user.get("role")
    viewer_student_id: Optional[str] = None
    if role == "student":
        viewer_student_id = str(user["sub"])
        student = session.get(Student, viewer_student_id)
        cs = (get_active_course_session_by_class_id(session, student.class_id)
              if student and student.class_id else None)
        # 学生只能看自己班级活跃课堂所在教室的座位图
        if cs is None or cs.classroom != room.name:
            raise HTTPException(403, "当前没有可用的座位图")
        session_id = cs.id
    else:
        if session_id is not None:
            cs = session.get(CourseSession, session_id)
            if cs is None:
                raise HTTPException(404, "课堂不存在")
            if role != "admin" and cs.teacher_id != int(user["sub"]):
                raise HTTPException(403, "只能查看自己课堂的座位图")

    cells = get_seat_map(session, classroom_id,
                         semester_id=get_current_semester_id(session),
                         session_id=session_id,
                         viewer_student_id=viewer_student_id)
    # 补学生姓名（assigned/occupied/mine 需要显示名）
    ids = [c["student_id"] for c in cells if c["student_id"]]
    if ids:
        names = {s.student_id: s.name for s in session.exec(
            select(Student).where(Student.student_id.in_(ids))).all()}
        for c in cells:
            c["student_name"] = names.get(c["student_id"])
    return ok({"classroom": _classroom_out(session, room), "seats": cells})


@router.get("/seat-assignments/mine")
def mine(session: Session = Depends(get_session), user=Depends(get_current_user)):
    if user.get("role") != "student":
        raise HTTPException(403, "仅学生可用")
    return ok(get_my_seat_assignments(
        session, str(user["sub"]), get_current_semester_id(session)))


@router.post("/seats/{seat_id}/broken")
def mark_broken(seat_id: int, body: BrokenIn,
                session: Session = Depends(get_session),
                user=Depends(require_admin_or_teacher)):
    try:
        seat = set_seat_broken(session, seat_id, body.is_broken)
    except SeatNotFoundError:
        raise HTTPException(404, "座位不存在")
    return ok({"id": seat.id, "is_broken": seat.is_broken})


@router.post("/sessions/{session_id}/seat-overrides")
def set_override(session_id: int, body: OverrideIn,
                 session: Session = Depends(get_session),
                 user=Depends(get_current_user)):
    cs = session.get(CourseSession, session_id)
    if cs is None:
        raise HTTPException(404, "课堂不存在")
    if user.get("role") not in ("admin", "teacher"):
        raise HTTPException(403, "仅教师或管理员可调座")
    if user.get("role") != "admin" and cs.teacher_id != int(user["sub"]):
        raise HTTPException(403, "只能调整自己课堂的座位")
    try:
        override = set_seat_override(session, session_id=session_id,
                                     student_id=body.student_id, seat_id=body.seat_id)
    except SeatNotFoundError:
        raise HTTPException(404, "座位不存在")
    except SeatBrokenError:
        raise HTTPException(409, "该座位电脑故障，不可调座")
    except SeatOccupiedError:
        raise HTTPException(409, "该座位本课堂已被占用")
    return ok({"session_id": override.session_id,
               "student_id": override.student_id, "seat_id": override.seat_id})


@router.delete("/sessions/{session_id}/seat-overrides/{student_id}")
def delete_override(session_id: int, student_id: str,
                    session: Session = Depends(get_session),
                    user=Depends(get_current_user)):
    cs = session.get(CourseSession, session_id)
    if cs is None:
        raise HTTPException(404, "课堂不存在")
    if user.get("role") not in ("admin", "teacher"):
        raise HTTPException(403, "仅教师或管理员可调座")
    if user.get("role") != "admin" and cs.teacher_id != int(user["sub"]):
        raise HTTPException(403, "只能调整自己课堂的座位")
    clear_seat_override(session, session_id, student_id)
    return ok({"cleared": True})
