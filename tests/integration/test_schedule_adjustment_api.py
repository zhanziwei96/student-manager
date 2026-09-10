"""
课表调整 API 集成测试
"""
import pytest
from sqlmodel import Session, select


@pytest.fixture
def create_test_schedule(test_engine, teacher_user, seed_refs):
    """创建测试课表的 fixture（class_id/semester_id 为纯 FK 锚点，取自 seed_refs）"""
    from app.models.course_schedule import CourseSchedule

    def _create_schedule(**kwargs):
        with Session(test_engine) as session:
            schedule = CourseSchedule(
                course_name=kwargs.get("course_name", "测试课程"),
                class_id=seed_refs[kwargs.get("class_name", "一班")],
                semester_id=seed_refs["semester_id"],
                teacher_id=kwargs.get("teacher_id", teacher_user.id),
                teacher_name=kwargs.get("teacher_name", teacher_user.name),
                day_of_week=kwargs.get("day_of_week", 1),
                start_time=kwargs.get("start_time", "08:00"),
                end_time=kwargs.get("end_time", "09:40"),
                classroom=kwargs.get("classroom", "A-101"),
                week_start=kwargs.get("week_start", 1),
                week_end=kwargs.get("week_end", 20)
            )
            session.add(schedule)
            session.commit()
            session.refresh(schedule)
            return schedule

    return _create_schedule


@pytest.fixture
def another_teacher_user(test_engine):
    """创建另一个教师用户（用于权限测试）"""
    from app.models import User, UserRoleConst
    from app.core.security import generate_password_hash

    with Session(test_engine) as session:
        password_hash, salt = generate_password_hash("teacher456")
        user = User(
            username="teacher2",
            name="教师2",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.TEACHER,
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def unauthorized_teacher_client(client, another_teacher_user):
    """已登录但无权限的教师的客户端"""
    response = client.post("/api/v1/login", json={
        "username": "teacher2",
        "password": "teacher456",
        "role": "teacher"
    })
    assert response.status_code == 200
    return client


class TestScheduleAdjustmentAPI:
    """课表调整 API 集成测试"""

    def test_create_cancel_adjustment_success(self, teacher_client, create_test_schedule):
        """教师成功创建停课记录"""
        schedule = create_test_schedule(course_name="数学", class_name="一班")

        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 5,
            "type": "cancel",
            "reason": "教师外出培训"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "调整记录已创建" in data.get("message", "")

    def test_create_modify_adjustment_success(self, teacher_client, create_test_schedule):
        """教师成功创建调课记录"""
        schedule = create_test_schedule(course_name="英语", class_name="一班")

        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 3,
            "type": "modify",
            "reason": "教室冲突",
            "new_date": "2026-04-10",
            "new_start_time": "14:00",
            "new_end_time": "15:40",
            "new_classroom": "B-202"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_makeup_adjustment_success(self, teacher_client, create_test_schedule):
        """教师成功创建补课记录"""
        schedule = create_test_schedule(course_name="物理", class_name="一班")

        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 2,
            "type": "makeup",
            "reason": "清明节补课",
            "new_date": "2026-04-12",
            "new_start_time": "10:00",
            "new_end_time": "11:40",
            "new_classroom": "C-303"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 补课应生成 course_session
        assert "调整记录已创建" in data.get("message", "")

    def test_cancel_with_active_session_auto_ends(self, teacher_client, create_test_schedule, test_engine):
        """进行中的课程取消时自动结束课堂"""
        from app.crud.course_session import start_course_session

        schedule = create_test_schedule(course_name="化学", class_name="一班")

        # 先开始该课程的课堂
        with Session(test_engine) as session:
            start_course_session(
                session=session,
                class_name="一班",
                teacher_id=1,
                teacher_name="教师1",
                course_name="化学",
                schedule_id=schedule.id,
                week_number=4
            )

        # cancel 现在会自动结束活跃课堂并返回 200
        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 4,
            "type": "cancel",
            "reason": "临时停课"
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_modify_with_ended_session_fails(self, teacher_client, create_test_schedule, test_engine):
        """已结束的课程不能调课"""
        from app.crud.course_session import start_course_session, end_course_session

        schedule = create_test_schedule(course_name="生物", class_name="一班")

        with Session(test_engine) as session:
            cs = start_course_session(
                session=session,
                class_name="一班",
                teacher_id=1,
                teacher_name="教师1",
                course_name="生物",
                schedule_id=schedule.id,
                week_number=6
            )
            end_course_session(session, teacher_id=1, class_name="一班")

        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 6,
            "type": "modify",
            "reason": "调教室"
        })
        assert response.status_code == 400
        assert "已结束的课程不能调课" in response.text

    def test_create_adjustment_unauthorized_teacher(self, unauthorized_teacher_client, create_test_schedule, teacher_user):
        """无权限教师不能调课"""
        schedule = create_test_schedule(course_name="地理", class_name="一班", teacher_id=teacher_user.id)

        response = unauthorized_teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 1,
            "type": "cancel",
            "reason": "无理由"
        })
        assert response.status_code == 403
        assert "无权调整此课程" in response.text

    def test_list_adjustments(self, teacher_client, create_test_schedule):
        """查询调整记录"""
        schedule = create_test_schedule(course_name="历史", class_name="一班")

        # 先创建两条调整记录
        teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 2,
            "type": "cancel",
            "reason": "期中考试"
        })
        teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 4,
            "type": "modify",
            "reason": "运动会"
        })

        # 按 schedule_id 查询
        response = teacher_client.get(f"/api/v1/schedule-adjustments?schedule_id={schedule.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        types = [item["type"] for item in data["data"]]
        assert "cancel" in types
        assert "modify" in types

        # 按 week_number 查询
        response = teacher_client.get(f"/api/v1/schedule-adjustments?schedule_id={schedule.id}&week_number=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["week_number"] == 2

    def test_student_cannot_create_adjustment(self, student_client, create_test_schedule):
        """学生不能创建调整记录"""
        schedule = create_test_schedule(course_name="音乐", class_name="一班")

        response = student_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 1,
            "type": "cancel",
            "reason": "不想上课"
        })
        assert response.status_code == 403

    def test_create_adjustment_invalid_week_number(self, teacher_client, create_test_schedule):
        """创建调课时周次必须在 1-20 范围内"""
        schedule = create_test_schedule(course_name="语文", class_name="一班")

        # 周次为 0
        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 0,
            "type": "cancel",
            "reason": "测试"
        })
        assert response.status_code == 400
        assert "1-20" in response.text

        # 周次为 21
        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 21,
            "type": "cancel",
            "reason": "测试"
        })
        assert response.status_code == 400
        assert "1-20" in response.text

    def test_create_duplicate_adjustment_returns_409(self, teacher_client, create_test_schedule):
        """同一课表同一周次重复创建调课应返回 409 并包含已有记录"""
        schedule = create_test_schedule(course_name="美术", class_name="一班")

        # 第一次创建成功
        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 8,
            "type": "cancel",
            "reason": "第一次停课"
        })
        assert response.status_code == 200

        # 第二次重复创建应返回 409
        response = teacher_client.post("/api/v1/schedule-adjustments", json={
            "schedule_id": schedule.id,
            "week_number": 8,
            "type": "modify",
            "reason": "重复调课"
        })
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "已存在调课记录" in data.get("message", "")
        assert "data" in data
        assert data["data"]["schedule_id"] == schedule.id
        assert data["data"]["week_number"] == 8
        assert data["data"]["type"] == "cancel"
