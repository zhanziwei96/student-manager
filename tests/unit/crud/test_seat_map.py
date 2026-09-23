"""座位图查询：四态判定 + 我的座位列表。"""
from app.crud.seat import create_classroom, get_my_seat_assignments, get_seat_map
from app.models import CourseSession, Student
from app.models.checkin import CheckinRecord
from app.models.seat import SeatAssignment, SeatSessionOverride
from sqlmodel import select
from app.models.seat import Seat


def _seat(session, classroom_id, seat_no):
    return session.exec(
        select(Seat).where(Seat.classroom_id == classroom_id, Seat.seat_no == seat_no)
    ).one()


def _mk_student(session, student_id, name):
    """SeatAssignment/SeatSessionOverride.student_id 是 FK，插入前必须先有学生行。"""
    session.add(Student(student_id=student_id, name=name))
    session.commit()


def _mk_session(session, session_id, refs):
    """CheckinRecord/SeatSessionOverride.session_id 是 FK，引用前必须先有课堂行。"""
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

    def test_assigned_state(self, session, seed_refs):
        room = create_classroom(session, name="机房402", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        _mk_student(session, "S001", "张三")
        session.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                   classroom_id=room.id,
                                   semester_id=seed_refs["semester_id"]))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"])
        assert cells[0]["state"] == "assigned"
        assert cells[0]["student_id"] == "S001"

    def test_mine_beats_assigned(self, session, seed_refs):
        room = create_classroom(session, name="机房403", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        _mk_student(session, "S001", "张三")
        session.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                   classroom_id=room.id,
                                   semester_id=seed_refs["semester_id"]))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                             viewer_student_id="S001")
        assert cells[0]["state"] == "mine"

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

    def test_override_marks_mine(self, session, seed_refs):
        room = create_classroom(session, name="机房405", rows=1, cols=2)
        seat = _seat(session, room.id, "P12")
        _mk_student(session, "S001", "张三")
        _mk_session(session, 9002, seed_refs)
        session.add(SeatSessionOverride(session_id=9002, student_id="S001",
                                        seat_id=seat.id))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                             session_id=9002, viewer_student_id="S001")
        assert cells[1]["state"] == "mine"


class TestMyAssignments:
    def test_lists_by_classroom(self, session, seed_refs):
        room = create_classroom(session, name="机房406", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        _mk_student(session, "S001", "张三")
        session.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                   classroom_id=room.id,
                                   semester_id=seed_refs["semester_id"]))
        session.commit()
        mine = get_my_seat_assignments(session, "S001", seed_refs["semester_id"])
        assert mine == [{
            "classroom_id": room.id, "classroom_name": "机房406",
            "seat_id": seat.id, "seat_no": "P11", "is_broken": False,
        }]

    def test_empty_for_other_semester(self, session, seed_refs):
        assert get_my_seat_assignments(session, "S001", 999999) == []
