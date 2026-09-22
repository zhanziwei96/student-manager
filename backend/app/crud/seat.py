"""座位系统 CRUD。惯例：模块级裸函数，第一参数 session，自行 commit/refresh。"""
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.seat_layout import build_seat_rows
from app.models.seat import Classroom, Seat, SeatAssignment


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
