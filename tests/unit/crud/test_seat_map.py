"""座位图查询：每节课自选座位，只保留 empty/occupied/mine。"""
from app.crud.seat import create_classroom, get_my_seat_assignments, get_seat_map
from app.models import CourseSession, Student
from app.models.checkin import CheckinRecord
from app.models.seat import Seat, SeatSessionOverride
from sqlmodel import select


def _seat(session, classroom_id, seat_no):
    return session.exec(
        select(Seat).where(Seat.classroom_id == classroom_id, Seat.seat_no == seat_no)
    ).one()


def _mk_student(session, student_id, name):
    session.add(Student(student_id=student_id, name=name))
    session.commit()


def _mk_session(session, session_id, refs):
    session.add(CourseSession(
        id=session_id, session_code=f"SEAT{session_id}",
        class_id=refs["一班"], semester_id=refs["semester_id"], teacher_id=1,
    ))
    session.commit()


class TestSeatMap:
    def test_all_empty_initially(self, session, seed_refs):
        room = create_classroom(session, name="机房401", rows=2, cols=2)
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"])
        assert all(c["state"] == "empty" for c in cells)
        assert [c["seat_no"] for c in cells] == ["P11", "P12", "P21", "P22"]

    def test_occupied_in_session(self, session, seed_refs):
        room = create_classroom(session, name="机房404", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        _mk_student(session, "S002", "李四")
        _mk_session(session, 9001, seed_refs)
        session.add(CheckinRecord(session_id=9001, student_id="S002",
                                  student_name="李四", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat.id))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                             session_id=9001)
        assert cells[0]["state"] == "occupied"
        assert cells[0]["student_id"] == "S002"

    def test_mine_when_viewer_occupied(self, session, seed_refs):
        room = create_classroom(session, name="机房403", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        _mk_student(session, "S001", "张三")
        _mk_session(session, 9003, seed_refs)
        session.add(CheckinRecord(session_id=9003, student_id="S001",
                                  student_name="张三", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat.id))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                             session_id=9003, viewer_student_id="S001")
        assert cells[0]["state"] == "mine"

    def test_override_marks_mine_and_occupied_for_others(self, session, seed_refs):
        room = create_classroom(session, name="机房405", rows=1, cols=2)
        seat = _seat(session, room.id, "P12")
        _mk_student(session, "S001", "张三")
        _mk_session(session, 9002, seed_refs)
        session.add(SeatSessionOverride(session_id=9002, student_id="S001",
                                        seat_id=seat.id))
        session.commit()
        mine_cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                                  session_id=9002, viewer_student_id="S001")
        assert mine_cells[1]["state"] == "mine"
        other_cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                                   session_id=9002, viewer_student_id="S999")
        assert other_cells[1]["state"] == "occupied"


class TestMyAssignments:
    def test_fixed_assignment_endpoint_is_deprecated_empty(self, session, seed_refs):
        room = create_classroom(session, name="机房406", rows=1, cols=2)
        _seat(session, room.id, "P11")
        _mk_student(session, "S001", "张三")
        assert get_my_seat_assignments(session, "S001", seed_refs["semester_id"]) == []
