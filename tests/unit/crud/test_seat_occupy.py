"""占座规则：每节课自选座位；固定座位分配不再参与限制。"""

import pytest
from sqlmodel import Session, select

from app.crud.course_session import start_course_session
from app.crud.checkin import create_checkin
from app.crud.seat import (
    NotMySeatError, SeatBrokenError, SeatOccupiedError,
    clear_seat_override, create_classroom, occupy_seat,
    set_seat_broken, set_seat_override,
)
from app.models import Student
from app.models.checkin import CheckinRecord
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
    """SeatAssignment/SeatSessionOverride/CheckinRecord 的 student_id 是 FK，插入前必须先有学生行。"""
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
    def test_free_choice_does_not_create_fixed_assignment(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        result = occupy_seat(session, student_id="S001", seat_id=seat.id,
                             course_session_id=course_session.id)
        assert result["created_fixed"] is False
        assert result["temporary"] is False
        assert session.exec(select(SeatAssignment)).all() == []

    def test_reselect_before_checkin_is_allowed(self, session, seed_refs, room, course_session):
        # 不读/不写固定座位：同一个学生在真正产生签到记录前，直接占座校验可换座位
        occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id)
        again = occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P22").id,
                            course_session_id=course_session.id)
        assert again["created_fixed"] is False
        assert session.exec(select(SeatAssignment)).all() == []

    def test_broken_seat_refused(self, session, room, course_session):
        seat = set_seat_broken(session, _seat(session, room, "P21").id, True)
        with pytest.raises(SeatBrokenError):
            occupy_seat(session, student_id="S001", seat_id=seat.id,
                        course_session_id=course_session.id)

    def test_occupied_by_other_refused(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        session.add(CheckinRecord(session_id=course_session.id, student_id="S001",
                                  student_name="张三", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat.id))
        session.commit()
        with pytest.raises(SeatOccupiedError):
            occupy_seat(session, student_id="S002", seat_id=seat.id,
                        course_session_id=course_session.id)

    def test_stale_fixed_assignment_is_ignored(self, session, seed_refs, room, course_session):
        # 旧固定座位数据即使存在，也不再阻止别人选座
        seat = _seat(session, room, "P11")
        session.add(SeatAssignment(
            seat_id=seat.id, student_id="S001", class_id=seed_refs["一班"],
            classroom_id=room.id, semester_id=seed_refs["semester_id"],
        ))
        session.commit()
        result = occupy_seat(session, student_id="S002", seat_id=seat.id,
                             course_session_id=course_session.id)
        assert result["created_fixed"] is False
        rows = session.exec(select(SeatAssignment)).all()
        assert len(rows) == 1  # 没有新增固定座位

    def test_concurrent_same_seat_conflict_translated_to_occupied(
            self, session, seed_refs, room, course_session):
        """并发抢同一座位：竞态胜者先提交 checkin，后提交者撞 uix_checkin_session_seat。"""
        seat = _seat(session, room, "P11")
        session.commit()  # 结束当前事务，以便切换隔离级别
        session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        session.exec(select(CheckinRecord)).all()  # 建立快照（看不到之后的提交）

        winner = Session(session.get_bind())
        try:
            winner.add(CheckinRecord(
                session_id=course_session.id, student_id="S002", student_name="李四",
                class_id=seed_refs["一班"], semester_id=seed_refs["semester_id"],
                checkin_type="code", seat_id=seat.id,
            ))
            winner.commit()
        finally:
            winner.close()

        with pytest.raises(SeatOccupiedError):
            create_checkin(session, "S001", "张三", seed_refs["一班"], course_session.id,
                           seat_id=seat.id)


class TestOverride:
    def test_override_allows_other_seat(self, session, room, course_session):
        target = _seat(session, room, "P22")
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=target.id)
        result = occupy_seat(session, student_id="S001", seat_id=target.id,
                             course_session_id=course_session.id)
        assert result["temporary"] is True

    def test_override_wrong_seat_refused(self, session, room, course_session):
        target = _seat(session, room, "P22")
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=target.id)
        with pytest.raises(NotMySeatError):
            occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P11").id,
                        course_session_id=course_session.id)

    def test_clear_override(self, session, room, course_session):
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=_seat(session, room, "P22").id)
        clear_seat_override(session, course_session.id, "S001")
        from app.models.seat import SeatSessionOverride
        assert session.exec(
            select(SeatSessionOverride).where(
                SeatSessionOverride.session_id == course_session.id)
        ).first() is None

    def test_override_to_broken_refused(self, session, room, course_session):
        broken = set_seat_broken(session, _seat(session, room, "P12").id, True)
        with pytest.raises(SeatBrokenError):
            set_seat_override(session, session_id=course_session.id,
                              student_id="S001", seat_id=broken.id)

    def test_override_moves_existing_checkin(self, session, seed_refs, room, course_session):
        seat_a = _seat(session, room, "P11")
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
