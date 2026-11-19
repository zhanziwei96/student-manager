"""占座规则：首次固定 / 本人固定座 / 故障临坐 / 冲突拒绝。"""
from datetime import datetime

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
                             semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
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
                    semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
        again = occupy_seat(session, student_id="S001", seat_id=seat.id,
                            course_session_id=course_session.id,
                            semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
        assert again["created_fixed"] is False

    def test_other_seat_refused(self, session, seed_refs, room, course_session):
        occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
        with pytest.raises(NotMySeatError):
            occupy_seat(session, student_id="S001",
                        seat_id=_seat(session, room, "P12").id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])

    def test_broken_seat_refused(self, session, seed_refs, room, course_session):
        seat = set_seat_broken(session, _seat(session, room, "P21").id, True)
        with pytest.raises(SeatBrokenError):
            occupy_seat(session, student_id="S001", seat_id=seat.id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])

    def test_fixed_broken_allows_temporary(self, session, seed_refs, room, course_session):
        fixed_seat = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=fixed_seat.id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
        set_seat_broken(session, fixed_seat.id, True)
        result = occupy_seat(session, student_id="S001",
                             seat_id=_seat(session, room, "P22").id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
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
                    semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
        from app.models.checkin import CheckinRecord
        session.add(CheckinRecord(session_id=course_session.id, student_id="S001",
                                  student_name="张三", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat.id))
        session.commit()
        with pytest.raises(SeatOccupiedError):
            occupy_seat(session, student_id="S002", seat_id=seat.id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])

    def test_others_fixed_seat_refused(self, session, seed_refs, room, course_session):
        # A 先固定 P11
        occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id, semester_id=seed_refs["semester_id"],
                    class_id=seed_refs["一班"])
        # B（本教室无固定分配）选 P11 → SeatOccupiedError，而不是 500
        with pytest.raises(SeatOccupiedError):
            occupy_seat(session, student_id="S002", seat_id=_seat(session, room, "P11").id,
                        course_session_id=course_session.id, semester_id=seed_refs["semester_id"],
                        class_id=seed_refs["一班"])

    def test_other_class_fixed_seat_is_selectable(self, session, seed_refs, room):
        """跨班不霸占：A 班的固定座位，B 班学生应能正常选择（各自班级维度独立）。"""
        from app.crud.course_session import start_course_session
        class_a, class_b = seed_refs["一班"], seed_refs["二班"]
        seat = _seat(session, room, "P11")

        # A 班学生在该教室留下固定座位分配
        session.add(SeatAssignment(
            seat_id=seat.id, student_id="S001", class_id=class_a,
            classroom_id=room.id, semester_id=seed_refs["semester_id"],
            created_at=datetime.now(),
        ))
        session.commit()

        # B 班在该教室开课
        cs_b = start_course_session(
            session, class_id=class_b, teacher_id=1,
            teacher_name="王老师", classroom=room.name,
        )
        result = occupy_seat(session, student_id="S002", seat_id=seat.id,
                             course_session_id=cs_b.id,
                             semester_id=seed_refs["semester_id"], class_id=class_b)
        assert result["created_fixed"] is True
        assert result["seat_no"] == "P11"

        # 两个班的分配行共存（维度 = 班级 × 学期 × 座位）
        rows = session.exec(
            select(SeatAssignment).where(SeatAssignment.seat_id == seat.id)
        ).all()
        assert {r.class_id for r in rows} == {class_a, class_b}

    def test_seat_map_isolated_per_class(self, session, seed_refs, room):
        """座位图按班级隔离：A 班的 assigned 对 B 班而言是 empty/可选。"""
        from app.crud.seat import get_seat_map
        class_a, class_b = seed_refs["一班"], seed_refs["二班"]
        seat = _seat(session, room, "P11")
        session.add(SeatAssignment(
            seat_id=seat.id, student_id="S001", class_id=class_a,
            classroom_id=room.id, semester_id=seed_refs["semester_id"],
            created_at=datetime.now(),
        ))
        session.commit()

        cells_b = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                               class_id=class_b)
        cell = next(c for c in cells_b if c["seat_id"] == seat.id)
        assert cell["state"] == "empty"

        cells_a = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                               class_id=class_a, viewer_student_id="S002")
        cell_a = next(c for c in cells_a if c["seat_id"] == seat.id)
        assert cell_a["state"] == "assigned"

    def test_concurrent_first_choice_translated_to_occupied(
            self, session, seed_refs, room, course_session):
        """并发首次选座：竞态胜者在快照建立后提交，IntegrityError 须翻译为 SeatOccupiedError。"""
        from datetime import datetime
        from sqlmodel import Session
        seat = _seat(session, room, "P11")
        session.commit()  # 结束当前事务，以便切换隔离级别
        # REPEATABLE READ 快照：模拟"校验通过 → 提交"窗口内胜者已提交的竞态
        session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
        session.exec(select(SeatAssignment)).all()  # 建立快照（看不到之后的提交）
        winner = Session(session.get_bind())
        try:
            winner.add(SeatAssignment(
                seat_id=seat.id, student_id="S002", classroom_id=room.id,
                class_id=seed_refs["一班"],
                semester_id=seed_refs["semester_id"], created_at=datetime.now(),
            ))
            winner.commit()
        finally:
            winner.close()
        with pytest.raises(SeatOccupiedError):
            occupy_seat(session, student_id="S001", seat_id=seat.id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])


class TestOverride:
    def test_override_allows_other_seat(self, session, seed_refs, room, course_session):
        occupy_seat(session, student_id="S001",
                    seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
        target = _seat(session, room, "P22")
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=target.id)
        result = occupy_seat(session, student_id="S001", seat_id=target.id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
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
                    course_session_id=course_session.id, semester_id=seed_refs["semester_id"], class_id=seed_refs["一班"])
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
