"""
Course Session API 集成测试
"""
import pytest
from sqlmodel import Session


@pytest.fixture
def create_test_schedule(test_engine, teacher_user):
    """创建测试课表的 fixture"""
    from app.models.course_schedule import CourseSchedule

    def _create_schedule(**kwargs):
        with Session(test_engine) as session:
            schedule = CourseSchedule(
                course_name=kwargs.get("course_name", "测试课程"),
                class_name=kwargs.get("class_name", "测试班级"),
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


class TestCourseSessionAPI:
    """课程会话 API 集成测试"""

    def test_get_course_sessions_active_default(self, teacher_client):
        """GET /course-sessions 默认返回教师活跃课堂"""
        # 先开始一个课堂
        start_resp = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "一班",
            "course_name": "高等数学"
        })
        assert start_resp.status_code == 200

        response = teacher_client.get("/api/v1/course-sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1
        # 默认只返回 active
        assert data["data"][0]["status"] == "active"
        assert data["data"][0]["session_code"] is not None
        assert data["data"][0]["class_name"] == "一班"

    def test_get_course_sessions_status_ended(self, teacher_client):
        """GET /course-sessions?status=ended 返回历史课堂"""
        start_resp = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "二班",
            "course_name": "数据结构"
        })
        assert start_resp.status_code == 200
        session_id = start_resp.json()["data"]["id"]

        # 结束课堂
        end_resp = teacher_client.post(f"/api/v1/course-sessions/{session_id}/end")
        assert end_resp.status_code == 200

        response = teacher_client.get("/api/v1/course-sessions?status=ended")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        sessions = [s for s in data["data"] if s["id"] == session_id]
        assert len(sessions) == 1
        assert sessions[0]["status"] == "ended"

    def test_start_course_session_manual(self, teacher_client):
        """POST /course-sessions/start 不带 schedule_id"""
        response = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "三班",
            "course_name": "英语"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "active"
        assert data["data"]["source_type"] == "manual"
        assert data["data"]["session_code"] is not None
        assert data["message"] == "上课开始"

    def test_start_course_session_with_schedule_id(self, teacher_client, create_test_schedule):
        """POST /course-sessions/start 带 schedule_id"""
        schedule = create_test_schedule(course_name="计算机基础", class_name="四班")

        response = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "四班",
            "schedule_id": schedule.id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["course_name"] == "计算机基础"
        assert data["data"]["source_type"] == "scheduled"
        assert data["data"]["schedule_id"] == schedule.id
        assert data["data"]["week_number"] is not None

    def test_start_course_session_conflict_same_class(self, teacher_client):
        """同一班级已有活跃课堂时无法开始新课堂"""
        teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "五班",
            "course_name": "物理"
        })

        response = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "五班",
            "course_name": "化学"
        })
        assert response.status_code == 409
        resp_text = response.text
        assert "上课" in resp_text or "冲突" in resp_text

    def test_end_course_session(self, teacher_client):
        """POST /course-sessions/{id}/end 结束课堂"""
        start_resp = teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "六班",
            "course_name": "生物"
        })
        session_id = start_resp.json()["data"]["id"]

        response = teacher_client.post(f"/api/v1/course-sessions/{session_id}/end")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "上课结束"

        # 再次结束应报错
        retry = teacher_client.post(f"/api/v1/course-sessions/{session_id}/end")
        assert retry.status_code == 400

    def test_end_course_session_not_found(self, teacher_client):
        """结束不存在的课堂返回 404"""
        response = teacher_client.post("/api/v1/course-sessions/99999/end")
        assert response.status_code == 404

    def test_get_course_session_for_student(self, student_client, teacher_client):
        """GET /course-sessions/class/{class_name} 学生端获取活跃课堂"""
        teacher_client.post("/api/v1/course-sessions/start", json={
            "class_name": "一班",
            "course_name": "历史"
        })

        response = student_client.get("/api/v1/course-sessions/class/一班")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] is True
        assert "session_code" in data["data"]
        assert data["data"]["class_name"] == "一班"

    def test_get_course_session_for_student_no_active(self, student_client):
        """学生端获取没有活跃课堂的班级状态"""
        response = student_client.get("/api/v1/course-sessions/class/无课堂班")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] is False

    def test_get_course_sessions_unauthorized(self, client):
        """未登录无法访问教师端列表"""
        response = client.get("/api/v1/course-sessions")
        assert response.status_code == 401
