"""
活跃课堂 API 集成测试
测试获取活跃课堂接口（课堂管理路由已迁移到 course_session 模块）
"""
import pytest
from sqlmodel import Session


class TestActiveClassSessionsAPI:
    """测试活跃课堂相关 API"""

    def _start_class_directly(self, test_engine, class_name, course_name=None, teacher_id=1, teacher_name="张老师"):
        """直接通过 CRUD 创建活跃课堂用于测试"""
        from app.crud.course_session import start_course_session
        with Session(test_engine) as session:
            cs = start_course_session(
                session=session,
                class_name=class_name,
                teacher_id=teacher_id,
                teacher_name=teacher_name,
                course_name=course_name
            )
            return cs

    def test_get_active_class_sessions(self, student_client, test_engine, seed_refs):
        """测试获取所有活跃课堂列表（已登录学生可访问）"""
        self._start_class_directly(test_engine, "一班", "高等数学")

        response = student_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

        first_session = data["data"][0]
        assert "course_name" in first_session
        assert "class_name" in first_session
        assert "teacher_name" in first_session
        assert "start_time" in first_session

    def test_get_active_class_sessions_returns_empty_list(self, student_client):
        """测试没有活跃课堂时返回空列表"""
        response = student_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_active_class_sessions_allows_authenticated_user(self, student_client):
        """测试已登录用户可获取活跃课堂（未登录 401 见负向测试文件）"""
        response = student_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_get_active_class_sessions_after_end(self, student_client, test_engine, seed_refs):
        """测试结束上课后从活跃列表移除"""
        from app.crud.course_session import end_course_session

        self._start_class_directly(test_engine, "一班", "高等数学")

        # 活跃列表中有该课堂
        response = student_client.get("/api/v1/course-sessions/active")
        assert len(response.json()["data"]) == 1

        # 结束上课
        with Session(test_engine) as session:
            end_course_session(session, teacher_id=1)

        # 活跃列表为空
        response = student_client.get("/api/v1/course-sessions/active")
        assert response.json()["data"] == []

    def test_multiple_active_sessions(self, student_client, test_engine, seed_refs):
        """测试多个活跃课堂同时存在"""
        self._start_class_directly(test_engine, "一班", "高等数学", teacher_id=1)
        self._start_class_directly(test_engine, "二班", "数据结构", teacher_id=2)

        response = student_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

        course_names = [s["course_name"] for s in data["data"] if s["course_name"]]
        if course_names:
            assert "高等数学" in course_names or "数据结构" in course_names

    def test_active_sessions_only_current_term(self, student_client, test_engine, seed_refs):
        """学期隔离：上学期遗留的 active 课堂不得出现在当前学期活跃课堂列表"""
        from datetime import date
        from app.models import CourseSession, Semester
        from sqlmodel import Session, select

        # 上学期遗留的 active 课堂（绕过 CRUD 的当前学期默认值直接造数）
        with Session(test_engine) as session:
            old_sem = session.exec(select(Semester).where(Semester.label == "2025-2026-2")).first()
            if old_sem is None:
                old_sem = Semester(label="2025-2026-2", start_date=date(2025, 2, 17),
                                   total_weeks=20, is_current=False)
                session.add(old_sem)
                session.commit()
                session.refresh(old_sem)
            session.add(CourseSession(
                session_code="OLDSESS01",
                class_id=seed_refs["三班"],
                semester_id=old_sem.id,
                teacher_id=1,
                teacher_name="张老师",
                course_name="上学期课程",
                status="active",
            ))
            session.commit()

        # 当前学期 active 课堂（CRUD 默认填充当前学期）
        self._start_class_directly(test_engine, "一班", "高等数学", teacher_id=1)

        response = student_client.get("/api/v1/course-sessions/active")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["class_name"] == "一班"
        assert data["data"][0]["course_name"] == "高等数学"
