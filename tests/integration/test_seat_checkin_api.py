# tests/integration/test_seat_checkin_api.py
"""带座位的签到全流程。"""
import pytest
from sqlmodel import Session, select

from app.core.qr_signature import generate_verification_code
from app.crud.course_session import start_course_session
from app.models.checkin import CheckinRecord
from app.models.seat import Seat, SeatAssignment


@pytest.fixture()
def sample_students(student_user):
    """覆盖 conftest 版本：student_client 登录的 S001 已由 student_user 创建，
    conftest sample_students 会重复插入 S001 撞 students 主键。本模块测试只用
    sample_students[0]（必须是登录学生 S001 本人，否则 JWT sub 校验 403）。"""
    return [student_user]


@pytest.fixture()
def seat_classroom(test_engine, seed_refs):
    """造 2x2 教室 + 一班活跃课堂（classroom=机房701）。"""
    from app.crud.seat import create_classroom
    with Session(test_engine) as s:
        room = create_classroom(s, name="机房701", rows=2, cols=2)
        cs = start_course_session(s, class_id=seed_refs["一班"], teacher_id=1,
                                  teacher_name="王老师", classroom="机房701")
        return {"room_id": room.id, "session_code": cs.session_code,
                "session_id": cs.id}


def _seat_id(test_engine, room_id, no):
    with Session(test_engine) as s:
        return s.exec(select(Seat).where(
            Seat.classroom_id == room_id, Seat.seat_no == no)).one().id


def _code(session_code):
    return generate_verification_code(session_code)["code"]


def _checkin(client, student, session_code, seat_id=None):
    payload = {
        "student_id": student.student_id,
        "student_name": student.name,
        "verification_code": _code(session_code),
    }
    if seat_id is not None:
        payload["seat_id"] = seat_id
    return client.post("/api/v1/checkin", json=payload)


class TestSeatCheckin:
    def test_first_checkin_picks_and_fixes_seat(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P12")
        resp = _checkin(student_client, student,
                        seat_classroom["session_code"], seat_id)
        assert resp.status_code == 200, resp.text
        with Session(test_engine) as s:
            record = s.exec(select(CheckinRecord).where(
                CheckinRecord.student_id == student.student_id)).one()
            assert record.seat_id == seat_id
            fixed = s.exec(select(SeatAssignment).where(
                SeatAssignment.student_id == student.student_id)).one()
            assert fixed.seat_id == seat_id  # 首次自选 → 固定

    def test_wrong_code_occupies_nothing(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P11")
        resp = student_client.post("/api/v1/checkin", json={
            "student_id": student.student_id, "student_name": student.name,
            "verification_code": "000000", "seat_id": seat_id,
        })
        assert resp.status_code in (400, 401, 403)
        with Session(test_engine) as s:
            assert s.exec(select(CheckinRecord).where(
                CheckinRecord.student_id == student.student_id)).first() is None
            assert s.exec(select(SeatAssignment).where(
                SeatAssignment.student_id == student.student_id)).first() is None

    def test_same_seat_recheckin_idempotent(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P21")
        r1 = _checkin(student_client, student, seat_classroom["session_code"], seat_id)
        r2 = _checkin(student_client, student, seat_classroom["session_code"], seat_id)
        assert r1.status_code == 200 and r2.status_code == 200
        with Session(test_engine) as s:
            assert len(s.exec(select(CheckinRecord).where(
                CheckinRecord.student_id == student.student_id)).all()) == 1

    def test_other_seat_recheckin_409(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        first = _seat_id(test_engine, seat_classroom["room_id"], "P11")
        second = _seat_id(test_engine, seat_classroom["room_id"], "P22")
        assert _checkin(student_client, student,
                        seat_classroom["session_code"], first).status_code == 200
        resp = _checkin(student_client, student,
                        seat_classroom["session_code"], second)
        assert resp.status_code == 409

    def test_missing_seat_when_map_enabled_422(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        resp = _checkin(student_client, student, seat_classroom["session_code"])
        assert resp.status_code == 422

    def test_broken_seat_409(
            self, admin_client, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P11")
        admin_client.post(f"/api/v1/seats/{seat_id}/broken", json={"is_broken": True})
        student = sample_students[0]
        resp = _checkin(student_client, student,
                        seat_classroom["session_code"], seat_id)
        assert resp.status_code == 409

    def test_teacher_checkin_then_student_fills_seat(
            self, client, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        """教师先代签（无座）→ 学生带座签到 → 200 且原记录补录 seat_id，记录数仍为 1"""
        from app.core.jwt import create_access_token
        student = sample_students[0]
        # 教师代签（session_id 分支，无 seat_id）；seat_classroom 课堂 teacher_id=1
        teacher_token = create_access_token({"sub": "1", "role": "teacher"})
        client.cookies.set("access_token", teacher_token)
        r1 = client.post("/api/v1/checkin", json={
            "student_id": student.student_id, "student_name": student.name,
            "session_id": seat_classroom["session_id"],
        })
        assert r1.status_code == 200, r1.text
        # 学生带座补签
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P12")
        r2 = _checkin(student_client, student, seat_classroom["session_code"], seat_id)
        assert r2.status_code == 200, r2.text
        assert r2.json()["data"]["seat_no"] == "P12"
        with Session(test_engine) as s:
            records = s.exec(select(CheckinRecord).where(
                CheckinRecord.student_id == student.student_id)).all()
            assert len(records) == 1
            assert records[0].seat_id == seat_id
