"""座位 API 集成测试。"""
import pytest


def _login(client, username, password, role):
    resp = client.post("/api/v1/login",
                       json={"username": username, "password": password, "role": role})
    assert resp.status_code == 200, resp.text


@pytest.fixture()
def classroom(client, admin_client):
    resp = admin_client.post("/api/v1/classrooms",
                             json={"name": "机房601", "rows": 2, "cols": 3})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


@pytest.fixture()
def active_session(test_engine, seed_refs, classroom):
    """一班的活跃课堂（教室=机房601）——学生读座位图的权限前提。"""
    from sqlmodel import Session
    from app.models import CourseSession
    with Session(test_engine) as s:
        cs = CourseSession(
            session_code="SEATMAP1",
            course_name="高等数学",
            class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
            classroom="机房601",
            teacher_id=1,
            teacher_name="教师1",
            status="active",
        )
        s.add(cs)
        s.commit()
        s.refresh(cs)
        return cs.id


class TestClassroomCrud:
    def test_create_and_list(self, admin_client, classroom):
        resp = admin_client.get("/api/v1/classrooms")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()["data"]]
        assert "机房601" in names
        item = [c for c in resp.json()["data"] if c["name"] == "机房601"][0]
        assert item["seat_count"] == 6

    def test_create_duplicate_409(self, admin_client, classroom):
        resp = admin_client.post("/api/v1/classrooms",
                                 json={"name": "机房601", "rows": 1, "cols": 1})
        assert resp.status_code == 409

    def test_student_forbidden(self, student_client):
        resp = student_client.post("/api/v1/classrooms",
                                   json={"name": "机房X", "rows": 1, "cols": 1})
        assert resp.status_code == 403

    def test_layout_conflict_409(self, admin_client, client, test_engine,
                                 seed_refs, student_user, classroom):
        from sqlmodel import Session, select
        from app.models.seat import Seat, SeatAssignment
        with Session(test_engine) as s:
            seat = s.exec(select(Seat).where(
                Seat.classroom_id == classroom["id"], Seat.seat_no == "P23")).one()
            s.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                 classroom_id=classroom["id"],
                                 semester_id=seed_refs["semester_id"]))
            s.commit()
        resp = admin_client.put(f"/api/v1/classrooms/{classroom['id']}",
                                json={"rows": 1, "cols": 1})
        assert resp.status_code == 409
        assert "P23" in resp.json()["data"]["removed_seat_nos"]

    def test_rename_conflict_409(self, admin_client, classroom):
        admin_client.post("/api/v1/classrooms", json={"name": "机房602", "rows": 1, "cols": 1})
        resp = admin_client.put(f"/api/v1/classrooms/{classroom['id']}", json={"name": "机房602"})
        assert resp.status_code == 409


class TestSeatMap:
    def test_student_reads_own_classroom_map(self, student_client, classroom,
                                             active_session):
        resp = student_client.get(f"/api/v1/classrooms/{classroom['id']}/seats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["classroom"]["rows"] == 2
        assert len(data["seats"]) == 6
        assert all(s["state"] == "empty" for s in data["seats"])

    def test_unauthenticated_401(self, client, classroom):
        resp = client.get(f"/api/v1/classrooms/{classroom['id']}/seats")
        assert resp.status_code == 401


class TestBrokenAndOverride:
    def test_mark_broken(self, teacher_client, test_engine, classroom):
        from sqlmodel import Session, select
        from app.models.seat import Seat
        with Session(test_engine) as s:
            seat = s.exec(select(Seat).where(
                Seat.classroom_id == classroom["id"], Seat.seat_no == "P11")).one()
            seat_id = seat.id
        resp = teacher_client.post(f"/api/v1/seats/{seat_id}/broken",
                                   json={"is_broken": True})
        assert resp.status_code == 200
        assert resp.json()["data"]["is_broken"] is True

    def test_seat_override_and_clear(self, teacher_client, teacher_user,
                                     student_user, test_engine, seed_refs,
                                     classroom):
        from sqlmodel import Session, select
        from app.models import CourseSession
        from app.models.seat import Seat
        with Session(test_engine) as s:
            cs = CourseSession(
                session_code="SEATOVR1",
                course_name="高等数学",
                class_id=seed_refs["一班"],
                semester_id=seed_refs["semester_id"],
                classroom="机房601",
                teacher_id=teacher_user.id,
                teacher_name=teacher_user.name,
                status="active",
            )
            s.add(cs)
            s.commit()
            s.refresh(cs)
            session_id = cs.id
            seat = s.exec(select(Seat).where(
                Seat.classroom_id == classroom["id"], Seat.seat_no == "P12")).one()
            seat_id = seat.id
        resp = teacher_client.post(
            f"/api/v1/sessions/{session_id}/seat-overrides",
            json={"student_id": "S001", "seat_id": seat_id})
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["seat_id"] == seat_id
        resp = teacher_client.delete(
            f"/api/v1/sessions/{session_id}/seat-overrides/S001")
        assert resp.status_code == 200, resp.text

    def test_student_override_forbidden(self, student_client, test_engine, seed_refs, classroom):
        from sqlmodel import Session
        from app.crud.course_session import start_course_session
        with Session(test_engine) as s:
            cs = start_course_session(s, class_id=seed_refs["一班"], teacher_id=1,
                                      teacher_name="王老师", classroom="机房601")
        resp = student_client.post(f"/api/v1/sessions/{cs.id}/seat-overrides",
                                   json={"student_id": "S001", "seat_id": 1})
        assert resp.status_code == 403
