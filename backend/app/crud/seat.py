"""座位系统 CRUD。惯例：模块级裸函数，第一参数 session，自行 commit/refresh。"""
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.seat_layout import build_seat_rows
from app.models.checkin import CheckinRecord
from app.models.seat import Classroom, Seat, SeatAssignment
from app.models.seat import SeatSessionOverride


class ClassroomNameConflictError(Exception):
    pass


class ClassroomNotFoundError(Exception):
    pass


class SeatLayoutConflictError(Exception):
    """缩布局会删掉已有分配/故障标记的座位。removed_seat_nos 供前端提示。"""

    def __init__(self, removed_seat_nos: list[str]):
        super().__init__(f"布局变更将删除已有占用的座位: {', '.join(removed_seat_nos)}")
        self.removed_seat_nos = removed_seat_nos


def create_classroom(session: Session, *, name: str, rows: int, cols: int) -> Classroom:
    room = Classroom(name=name, rows=rows, cols=cols,
                     created_at=datetime.now(), updated_at=datetime.now())
    session.add(room)
    try:
        session.flush()  # 拿 id，先不 commit，座位与教室同一事务
    except IntegrityError:
        session.rollback()
        raise ClassroomNameConflictError(name)
    for row in build_seat_rows(room.id, rows, cols):
        session.add(Seat(**row))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ClassroomNameConflictError(name)
    session.refresh(room)
    return room


def get_classroom(session: Session, classroom_id: int) -> Optional[Classroom]:
    return session.get(Classroom, classroom_id)


def get_classroom_by_name(session: Session, name: str) -> Optional[Classroom]:
    return session.exec(select(Classroom).where(Classroom.name == name)).first()


def list_classrooms(session: Session, *, include_archived: bool = False) -> list[Classroom]:
    q = select(Classroom)
    if not include_archived:
        q = q.where(Classroom.status == "active")
    return list(session.exec(q.order_by(Classroom.name)).all())


def set_classroom_status(session: Session, classroom_id: int, status: str) -> Classroom:
    room = session.get(Classroom, classroom_id)
    if room is None:
        raise ClassroomNotFoundError(classroom_id)
    room.status = status
    room.updated_at = datetime.now()
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def update_classroom_layout(session: Session, classroom_id: int, *,
                            rows: int, cols: int) -> Classroom:
    """重建座位网格。保留仍在新网格内的座位（含其分配/故障标记）；新增差量座位；
    会被删掉的座位若带有分配或故障标记 → 拒绝，由调用方提示。"""
    room = session.get(Classroom, classroom_id)
    if room is None:
        raise ClassroomNotFoundError(classroom_id)

    existing = session.exec(select(Seat).where(Seat.classroom_id == classroom_id)).all()
    keep_positions = {(r, c) for r in range(1, rows + 1) for c in range(1, cols + 1)}
    to_delete = [s for s in existing if (s.row, s.col) not in keep_positions]

    if to_delete:
        delete_ids = [s.id for s in to_delete]
        assigned = session.exec(
            select(SeatAssignment).where(SeatAssignment.seat_id.in_(delete_ids))
        ).all()
        blocked = {s.seat_no for s in to_delete if s.is_broken}
        blocked |= {s.seat_no for s in to_delete
                    if s.id in {a.seat_id for a in assigned}}
        if blocked:
            raise SeatLayoutConflictError(sorted(blocked))
        for seat in to_delete:
            session.delete(seat)

    existing_positions = {(s.row, s.col) for s in existing if (s.row, s.col) in keep_positions}
    for row in build_seat_rows(classroom_id, rows, cols):
        if (row["row"], row["col"]) not in existing_positions:
            session.add(Seat(**row))

    room.rows = rows
    room.cols = cols
    room.updated_at = datetime.now()
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def get_seat_map(session: Session, classroom_id: int, *, semester_id: int,
                 session_id: Optional[int] = None,
                 viewer_student_id: Optional[str] = None) -> list[dict]:
    """座位图：四态 empty/assigned/occupied/mine。

    mine      = 本学期分配给 viewer，或本课堂 override 指向 viewer
    occupied  = 本课堂已有他人签到占用，或 override 指向他人（需传 session_id）
    assigned  = 本学期分配给他人且本课堂未占用
    empty     = 其余
    """
    seats = session.exec(
        select(Seat).where(Seat.classroom_id == classroom_id)
        .order_by(Seat.row, Seat.col)
    ).all()
    seat_ids = [s.id for s in seats]

    assignments = session.exec(
        select(SeatAssignment).where(
            SeatAssignment.seat_id.in_(seat_ids),
            SeatAssignment.semester_id == semester_id,
        )
    ).all() if seat_ids else []
    assigned_by_seat = {a.seat_id: a for a in assignments}

    occupied_by_seat: dict[int, str] = {}
    override_by_seat: dict[int, str] = {}
    override_by_student: dict[str, int] = {}
    if session_id is not None and seat_ids:
        records = session.exec(
            select(CheckinRecord).where(
                CheckinRecord.session_id == session_id,
                CheckinRecord.seat_id.in_(seat_ids),
            )
        ).all()
        occupied_by_seat = {r.seat_id: r.student_id for r in records if r.seat_id}
        overrides = session.exec(
            select(SeatSessionOverride).where(
                SeatSessionOverride.session_id == session_id,
                SeatSessionOverride.seat_id.in_(seat_ids),
            )
        ).all()
        override_by_seat = {o.seat_id: o.student_id for o in overrides}
        override_by_student = {o.student_id: o.seat_id for o in overrides}

    cells = []
    for s in seats:
        occupier = occupied_by_seat.get(s.id) or override_by_seat.get(s.id)
        fixed = assigned_by_seat.get(s.id)
        student_id = occupier or (fixed.student_id if fixed else None)
        if viewer_student_id and (
            student_id == viewer_student_id
            or override_by_student.get(viewer_student_id) == s.id
        ):
            state = "mine"
        elif occupier:
            state = "occupied"
        elif fixed:
            state = "assigned"
        else:
            state = "empty"
        cells.append({
            "seat_id": s.id, "seat_no": s.seat_no, "row": s.row, "col": s.col,
            "is_broken": s.is_broken, "state": state,
            "student_id": student_id, "student_name": None,
        })
    return cells


def get_my_seat_assignments(session: Session, student_id: str,
                            semester_id: int) -> list[dict]:
    rows = session.exec(
        select(SeatAssignment, Seat, Classroom)
        .join(Seat, SeatAssignment.seat_id == Seat.id)
        .join(Classroom, SeatAssignment.classroom_id == Classroom.id)
        .where(SeatAssignment.student_id == student_id,
               SeatAssignment.semester_id == semester_id)
    ).all()
    return [
        {
            "classroom_id": room.id, "classroom_name": room.name,
            "seat_id": seat.id, "seat_no": seat.seat_no, "is_broken": seat.is_broken,
        }
        for assignment, seat, room in rows
    ]
