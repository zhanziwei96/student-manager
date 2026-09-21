"""课表调整记录查询范围（授权）集成测试

GET /schedule-adjustments 必须按角色收敛范围：
- admin   → 全量
- teacher → 仅自己课表（CourseSchedule.teacher_id == 自己）
- student → 仅自己班级课表
- 未登录  → 401

越权目标设计（teacher_client = teacher1，student_client = 一班学生 S001）：
- s_own   一班 / teacher1  → teacher1 可见，一班学生可见
- s_peer  一班 / teacher2  → 同班不同老师，teacher1 **不可见**，一班学生可见
- s_other 二班 / teacher2  → teacher1 不可见（非自己课表），一班学生不可见
- s_third 三班 / teacher2  → 同上
"""
import pytest
from sqlmodel import Session


@pytest.fixture
def other_teacher(test_engine):
    """第二个教师（用于验证「同班不同老师」的记录不可见）"""
    from app.core.security import generate_password_hash
    from app.models import User, UserRoleConst

    with Session(test_engine) as session:
        password_hash, salt = generate_password_hash("teacher456")
        user = User(
            username="teacher2",
            name="教师2",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.TEACHER,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _login(client, username: str, password: str, role: str):
    resp = client.post("/api/v1/login", json={
        "username": username, "password": password, "role": role})
    assert resp.status_code == 200, resp.json()
    return client


@pytest.fixture
def other_teacher_client(client, other_teacher):
    """已登录的第二个教师客户端（复用 client 夹具，避免重复覆盖依赖）"""
    return _login(client, "teacher2", "teacher456", "teacher")


@pytest.fixture
def scope_data(test_engine, seed_refs, teacher_user, other_teacher):
    """4 条课表各 1 条停课记录，返回 {别名: schedule_id}"""
    from app.crud.schedule_adjustment import create_adjustment
    from app.models import CourseSchedule

    with Session(test_engine) as session:
        def mk(course_name: str, class_key: str, teacher) -> int:
            schedule = CourseSchedule(
                course_name=course_name,
                class_id=seed_refs[class_key],
                semester_id=seed_refs["semester_id"],
                teacher_id=teacher.id,
                teacher_name=teacher.name,
                day_of_week=1,
                start_time="08:00",
                end_time="09:40",
                classroom="A-101",
            )
            session.add(schedule)
            session.commit()
            session.refresh(schedule)
            create_adjustment(
                session=session,
                schedule_id=schedule.id,
                week_number=2,
                adjustment_type="cancel",
                created_by=teacher.id,
                reason=f"{course_name} 停课",
            )
            return schedule.id

        return {
            "s_own": mk("教师1在一班的课", "一班", teacher_user),
            "s_peer": mk("教师2在一班的课", "一班", other_teacher),
            "s_other": mk("教师2在二班的课", "二班", other_teacher),
            "s_third": mk("教师2在三班的课", "三班", other_teacher),
        }


def _schedule_ids(resp) -> set:
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    return {item["schedule_id"] for item in body["data"]}


class TestScheduleAdjustmentScope:
    """GET /schedule-adjustments 角色范围收敛"""

    def test_admin_sees_all_adjustments(self, admin_client, scope_data):
        """管理员不带参数 → 全量（含任意老师的课表）"""
        assert _schedule_ids(
            admin_client.get("/api/v1/schedule-adjustments")) == set(scope_data.values())

    def test_admin_can_query_any_schedule_id(self, admin_client, scope_data):
        """管理员可指定任意老师的 schedule_id"""
        resp = admin_client.get(
            "/api/v1/schedule-adjustments", params={"schedule_id": scope_data["s_peer"]})
        assert _schedule_ids(resp) == {scope_data["s_peer"]}

    def test_teacher_sees_only_own_schedule_adjustments(self, teacher_client, scope_data):
        """教师不带参数 → 只有自己课表的记录（同班其他老师、其他班一律不可见）"""
        assert _schedule_ids(
            teacher_client.get("/api/v1/schedule-adjustments")) == {scope_data["s_own"]}

    def test_teacher_can_query_own_schedule_id(self, teacher_client, scope_data):
        """教师指定自己的 schedule_id → 200"""
        resp = teacher_client.get(
            "/api/v1/schedule-adjustments", params={"schedule_id": scope_data["s_own"]})
        assert _schedule_ids(resp) == {scope_data["s_own"]}

    def test_teacher_week_number_filter_still_works(self, teacher_client, scope_data):
        """教师侧 week_number 过滤保持可用"""
        own = scope_data["s_own"]
        assert _schedule_ids(teacher_client.get(
            "/api/v1/schedule-adjustments",
            params={"schedule_id": own, "week_number": 2})) == {own}
        assert _schedule_ids(teacher_client.get(
            "/api/v1/schedule-adjustments",
            params={"schedule_id": own, "week_number": 3})) == set()

    @pytest.mark.parametrize("key", ["s_peer", "s_other", "s_third"])
    def test_teacher_cannot_query_other_teacher_schedule_id(
        self, teacher_client, scope_data, key
    ):
        """教师指定别人的 schedule_id → 403（同班的其他老师也不行）"""
        resp = teacher_client.get(
            "/api/v1/schedule-adjustments", params={"schedule_id": scope_data[key]})
        assert resp.status_code == 403
        assert "无权查看此课程" in resp.text

    def test_teacher_unknown_schedule_id_returns_404(self, teacher_client, scope_data):
        """不存在的 schedule_id → 404"""
        resp = teacher_client.get(
            "/api/v1/schedule-adjustments", params={"schedule_id": 999999})
        assert resp.status_code == 404

    def test_other_teacher_sees_own_records(self, other_teacher_client, scope_data):
        """第二个教师 → 只看到自己 3 条（证明过滤不是「一律返回空」）"""
        assert _schedule_ids(other_teacher_client.get(
            "/api/v1/schedule-adjustments")) == {
            scope_data["s_peer"], scope_data["s_other"], scope_data["s_third"]}

    def test_student_sees_only_own_class_adjustments(self, student_client, scope_data):
        """学生不带参数 → 只看到自己班级（一班）的课表记录，不看老师是谁"""
        assert _schedule_ids(
            student_client.get("/api/v1/schedule-adjustments")) == {
            scope_data["s_own"], scope_data["s_peer"]}

    def test_student_can_query_own_class_schedule_id(self, student_client, scope_data):
        """学生指定自己班级的 schedule_id → 200"""
        resp = student_client.get(
            "/api/v1/schedule-adjustments", params={"schedule_id": scope_data["s_peer"]})
        assert _schedule_ids(resp) == {scope_data["s_peer"]}

    @pytest.mark.parametrize("key", ["s_other", "s_third"])
    def test_student_cannot_query_other_class_schedule_id(
        self, student_client, scope_data, key
    ):
        """学生指定别的班级的 schedule_id → 403"""
        resp = student_client.get(
            "/api/v1/schedule-adjustments", params={"schedule_id": scope_data[key]})
        assert resp.status_code == 403
        assert "无权查看此课程" in resp.text

    def test_unauthenticated_returns_401(self, client, scope_data):
        """未登录 → 401"""
        resp = client.get("/api/v1/schedule-adjustments")
        assert resp.status_code == 401
