"""
CourseSession CRUD 单元测试
测试开始上课和获取课堂状态功能
"""
import pytest
from datetime import datetime
from app.crud.course_session import (
    start_course_session,
    get_teacher_active_course_sessions,
    end_course_session,
)
from app.models import CourseSession


class TestStartCourseSession:
    """测试开始上课功能"""

    def test_start_course_session_with_course_name(self, session):
        """测试开始上课时传入 course_name 正确保存"""
        cs = start_course_session(
            session=session,
            class_name="计算机1班",
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )

        assert cs.class_name == "计算机1班"
        assert cs.teacher_id == 1
        assert cs.teacher_name == "张老师"
        assert cs.course_name == "高等数学"
        assert cs.status == "active"
        assert cs.start_time is not None
        assert cs.session_code is not None

    def test_start_course_session_without_course_name(self, session):
        """测试开始上课时不传 course_name 默认为 None"""
        cs = start_course_session(
            session=session,
            class_name="软件工程班",
            teacher_id=2,
            teacher_name="李老师"
        )

        assert cs.class_name == "软件工程班"
        assert cs.course_name is None
        assert cs.status == "active"

    def test_start_course_session_allows_multiple_sessions(self, session):
        """测试教师可以同时开始多个班级的课程（多班级并行功能）"""
        old_session = start_course_session(
            session=session,
            class_name="旧班级",
            teacher_id=1,
            teacher_name="张老师",
            course_name="旧课程"
        )

        new_session = start_course_session(
            session=session,
            class_name="新班级",
            teacher_id=1,
            teacher_name="张老师",
            course_name="新课程"
        )

        session.refresh(old_session)
        assert old_session.status == "active"
        assert old_session.end_time is None

        assert new_session.status == "active"


class TestGetCourseSession:
    """测试获取课堂状态功能"""

    def test_get_teacher_active_course_sessions_returns_course_name(self, session):
        """测试获取课堂状态返回 course_name"""
        started = start_course_session(
            session=session,
            class_name="计算机1班",
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )

        sessions = get_teacher_active_course_sessions(session, teacher_id=1)

        assert len(sessions) >= 1
        cs = sessions[0]
        assert cs.id == started.id
        assert cs.course_name == "高等数学"
        assert cs.class_name == "计算机1班"
        assert cs.status == "active"

    def test_get_teacher_active_course_sessions_no_active_session(self, session):
        """测试没有活跃课堂时返回空列表"""
        sessions = get_teacher_active_course_sessions(session, teacher_id=999)

        assert sessions == []

    def test_get_teacher_active_course_sessions_only_returns_active(self, session):
        """测试只返回活跃状态的课堂"""
        start_course_session(
            session=session,
            class_name="已结束班级",
            teacher_id=1,
            teacher_name="张老师",
            course_name="已结束课程"
        )
        end_course_session(session, teacher_id=1)

        sessions = get_teacher_active_course_sessions(session, teacher_id=1)

        assert sessions == []


class TestEndCourseSession:
    """测试结束上课功能"""

    def test_end_course_session_sets_course_name_session_inactive(self, session):
        """测试结束带 course_name 的课堂"""
        started = start_course_session(
            session=session,
            class_name="计算机1班",
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )
        session_id = started.id

        end_course_session(session, teacher_id=1)

        active = get_teacher_active_course_sessions(session, teacher_id=1)
        assert active == []

        from sqlmodel import select
        statement = select(CourseSession).where(CourseSession.id == session_id)
        results = session.exec(statement).all()
        assert len(results) == 1
        assert results[0].status == "ended"
        assert results[0].end_time is not None
        assert results[0].course_name == "高等数学"
