"""教室 CRUD 单测：建教室自动生成座位、布局重建保护已分配座位。"""
import pytest
from sqlmodel import select

from app.crud.seat import (
    ClassroomNameConflictError,
    SeatLayoutConflictError,
    create_classroom,
    get_classroom,
    list_classrooms,
    set_classroom_status,
    update_classroom_layout,
)
from app.models.seat import Seat, SeatAssignment


class TestCreateClassroom:
    def test_creates_seats(self, session):
        room = create_classroom(session, name="机房302", rows=3, cols=4)
        seats = session.exec(select(Seat).where(Seat.classroom_id == room.id)).all()
        assert len(seats) == 12
        assert {s.seat_no for s in seats} == {f"P{r}{c}" for r in (1, 2, 3) for c in (1, 2, 3, 4)}

    def test_duplicate_name_raises(self, session):
        create_classroom(session, name="机房302", rows=2, cols=2)
        with pytest.raises(ClassroomNameConflictError):
            create_classroom(session, name="机房302", rows=2, cols=2)


class TestUpdateLayout:
    def test_grow_adds_seats(self, session):
        room = create_classroom(session, name="机房303", rows=2, cols=2)
        update_classroom_layout(session, room.id, rows=2, cols=4)
        seats = session.exec(select(Seat).where(Seat.classroom_id == room.id)).all()
        assert len(seats) == 8

    def test_shrink_with_assignment_refused(self, session, seed_refs):
        room = create_classroom(session, name="机房304", rows=2, cols=2)
        seat = session.exec(
            select(Seat).where(Seat.classroom_id == room.id, Seat.seat_no == "P22")
        ).one()
        from app.models import Student
        session.add(Student(student_id="S001", name="张三"))
        session.commit()
        session.add(SeatAssignment(
            seat_id=seat.id, student_id="S001", classroom_id=room.id,
            semester_id=seed_refs["semester_id"],
        ))
        session.commit()
        with pytest.raises(SeatLayoutConflictError) as exc:
            update_classroom_layout(session, room.id, rows=1, cols=1)  # P12/P21/P22 都会被删
        assert "P22" in exc.value.removed_seat_nos

    def test_shrink_without_assignment_ok(self, session):
        room = create_classroom(session, name="机房305", rows=2, cols=2)
        update_classroom_layout(session, room.id, rows=1, cols=2)
        seats = session.exec(select(Seat).where(Seat.classroom_id == room.id)).all()
        assert {s.seat_no for s in seats} == {"P11", "P12"}


class TestStatus:
    def test_archive_hides_from_default_list(self, session):
        room = create_classroom(session, name="机房306", rows=1, cols=1)
        set_classroom_status(session, room.id, "archived")
        assert room.id not in [c.id for c in list_classrooms(session)]
        assert room.id in [c.id for c in list_classrooms(session, include_archived=True)]
