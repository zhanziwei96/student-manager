"""占座规则：首次固定 / 本人固定座 / 故障临坐 / 冲突拒绝。"""
import pytest
from sqlmodel import select

from app.crud.course_session import start_course_session
from app.crud.seat import (
    NotMySeatError, SeatBrokenError, SeatOccupiedError,
    clear_seat_override, create_classroom, occupy_seat,
    set_seat_broken, set_seat_override,
)
from app.models import Student
from app.models.seat import Seat, SeatAssignment


@pytest.fixture()
def room(session):
    return create_classroom(session, name="机房501", rows=2, cols=2)


def _seat(session, room, no):
    return session.exec(
        select(Seat).where(Seat.classroom_id == room.id, Seat.seat_no == no)
    ).one()


@pytest.fixture(autouse=True)
def _students(session):
    """SeatAssignment/SeatSessionOverride.student_id 是 FK，插入前必须先有学生行。"""
    session.add(Student(student_id="S001", name="张三"))
    session.add(Student(student_id="S002", name="李四"))
    session.commit()


@pytest.fixture()
def course_session(session, seed_refs, room):
    return start_course_session(
        session, class_id=seed_refs["一班"], teacher_id=1,
        teacher_name="王老师", classroom=room.name,
    )


class TestOccupy:
    def test_first_choice_creates_fixed(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        result = occupy_seat(session, student_id="S001", seat_id=seat.id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"])
        assert result["created_fixed"] is True
        assert result["temporary"] is False
        fixed = session.exec(
            select(SeatAssignment).where(SeatAssignment.student_id == "S001")
        ).one()
        assert fixed.seat_id == seat.id

    def test_own_fixed_seat_ok(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=seat.id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        again = occupy_seat(session, student_id="S001", seat_id=seat.id,
                            course_session_id=course_session.id,
                            semester_id=seed_refs["semester_id"])
        assert again["created_fixed"] is False

    def test_other_seat_refused(self, session, seed_refs, room, course_session):
        occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        with pytest.raises(NotMySeatError):
            occupy_seat(session, student_id="S001",
                        seat_id=_seat(session, room, "P12").id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"])

    def test_broken_seat_refused(self, session, seed_refs, room, course_session):
        seat = set_seat_broken(session, _seat(session, room, "P21").id, True)
        with pytest.raises(SeatBrokenError):
            occupy_seat(session, student_id="S001", seat_id=seat.id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"])

    def test_fixed_broken_allows_temporary(self, session, seed_refs, room, course_session):
        fixed_seat = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=fixed_seat.id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        set_seat_broken(session, fixed_seat.id, True)
        result = occupy_seat(session, student_id="S001",
                             seat_id=_seat(session, room, "P22").id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"])
        assert result["temporary"] is True
        # 固定分配不变
        fixed = session.exec(
            select(SeatAssignment).where(SeatAssignment.student_id == "S001")
        ).one()
        assert fixed.seat_id == fixed_seat.id

    def test_occupied_by_other_refused(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=seat.id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        from app.models.checkin import CheckinRecord
        session.add(CheckinRecord(session_id=course_session.id, student_id="S001",
                                  student_name="张三", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat.id))
        session.commit()
        with pytest.raises(SeatOccupiedError):
            occupy_seat(session, student_id="S002", seat_id=seat.id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"])

    def test_others_fixed_seat_refused(self, session, seed_refs, room, course_session):
        # A 先固定 P11
        occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id, semester_id=seed_refs["semester_id"])
        # B（本教室无固定分配）选 P11 → SeatOccupiedError，而不是 500
        with pytest.raises(SeatOccupiedError):
            occupy_seat(session, student_id="S002", seat_id=_seat(session, room, "P11").id,
                        course_session_id=course_session.id, semester_id=seed_refs["semester_id"])


class TestOverride:
    def test_override_allows_other_seat(self, session, seed_refs, room, course_session):
        occupy_seat(session, student_id="S001",
                    seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        target = _seat(session, room, "P22")
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=target.id)
        result = occupy_seat(session, student_id="S001", seat_id=target.id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"])
        assert result["temporary"] is True

    def test_clear_override(self, session, seed_refs, room, course_session):
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=_seat(session, room, "P22").id)
        clear_seat_override(session, course_session.id, "S001")
        from app.models.seat import SeatSessionOverride
        assert session.exec(
            select(SeatSessionOverride).where(
                SeatSessionOverride.session_id == course_session.id)
        ).first() is None

    def test_override_to_broken_refused(self, session, seed_refs, room, course_session):
        broken = set_seat_broken(session, _seat(session, room, "P12").id, True)
        with pytest.raises(SeatBrokenError):
            set_seat_override(session, session_id=course_session.id,
                              student_id="S001", seat_id=broken.id)

    def test_override_moves_existing_checkin(self, session, seed_refs, room, course_session):
        from app.models.checkin import CheckinRecord
        seat_a = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=seat_a.id,
                    course_session_id=course_session.id, semester_id=seed_refs["semester_id"])
        session.add(CheckinRecord(session_id=course_session.id, student_id="S001",
                                  student_name="张三", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat_a.id))
        session.commit()
        seat_b = _seat(session, room, "P22")
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=seat_b.id)
        record = session.exec(select(CheckinRecord).where(
            CheckinRecord.session_id == course_session.id,
            CheckinRecord.student_id == "S001")).one()
        assert record.seat_id == seat_b.id
