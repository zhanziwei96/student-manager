"""
CourseSession CRUD 单元测试
"""
import pytest
from datetime import datetime
from sqlmodel import Session
from app.crud.course_session import (
    start_course_session,
    end_course_session,
    get_active_course_session_by_class_id,
    get_teacher_active_course_sessions,
    get_course_sessions_by_schedule_and_week,
    get_teacher_course_sessions,
)
from app.models import CourseSession, CourseSchedule


class TestStartCourseSession:
    """测试开始上课功能"""

    def test_start_course_session_creates_active_session(self, session: Session, seed_refs):
        """测试开始上课后状态为 active，有 session_code"""
        cs = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )

        assert cs.class_id == seed_refs["一班"]
        assert cs.teacher_id == 1
        assert cs.teacher_name == "张老师"
        assert cs.course_name == "高等数学"
        assert cs.status == "active"
        assert cs.start_time is not None
        assert cs.session_code is not None
        assert len(cs.session_code) == 8

    def test_start_course_session_without_course_name(self, session: Session, seed_refs):
        """测试开始上课时不传 course_name 默认为 None"""
        cs = start_course_session(
            session=session,
            class_id=seed_refs["二班"],
            teacher_id=2,
            teacher_name="李老师"
        )

        assert cs.class_id == seed_refs["二班"]
        assert cs.course_name is None
        assert cs.status == "active"

    def test_start_course_session_allows_multiple_sessions_different_classes(self, session: Session, seed_refs):
        """CRUD 层允许同教师多班级活跃（API 层负责拦截重复）"""
        cs1 = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="张老师",
            course_name="课程A"
        )
        cs2 = start_course_session(
            session=session,
            class_id=seed_refs["二班"],
            teacher_id=1,
            teacher_name="张老师",
            course_name="课程B"
        )

        assert cs1.status == "active"
        assert cs2.status == "active"

    def test_start_course_session_with_schedule_and_week(self, session: Session, seed_refs):
        """测试传入 schedule_id 和 week_number"""
        # PG 强制 FK：course_sessions.schedule_id → course_schedules.id
        from app.models import CourseSchedule
        session.add(CourseSchedule(
            id=10, course_name="网络安全", class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
            day_of_week=1, start_time="08:00", end_time="09:40",
        ))
        session.commit()

        cs = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=3,
            teacher_name="王老师",
            course_name="网络安全",
            schedule_id=10,
            week_number=5,
            classroom="A101",
            source_type="scheduled"
        )
        assert cs.schedule_id == 10
        assert cs.week_number == 5
        assert cs.classroom == "A101"
        assert cs.source_type == "scheduled"


class TestGetCourseSession:
    """测试查询课程会话功能"""

    def test_get_active_course_session_by_class_id(self, session: Session, seed_refs):
        """测试按班级 ID 查询活跃课堂"""
        started = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )

        result = get_active_course_session_by_class_id(session, seed_refs["一班"])
        assert result is not None
        assert result.id == started.id
        assert result.status == "active"

    def test_get_active_course_session_by_class_id_no_active(self, session: Session):
        """测试没有活跃课堂时返回 None"""
        result = get_active_course_session_by_class_id(session, 999999)
        assert result is None

    def test_get_teacher_active_course_sessions(self, session: Session, seed_refs):
        """测试按教师查询只返回该教师的活跃课程"""
        started = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )
        # 其他教师的课堂
        start_course_session(
            session=session,
            class_id=seed_refs["二班"],
            teacher_id=2,
            teacher_name="李老师",
            course_name="数据结构"
        )

        sessions = get_teacher_active_course_sessions(session, teacher_id=1)
        assert len(sessions) == 1
        assert sessions[0].id == started.id
        assert sessions[0].teacher_id == 1

    def test_get_teacher_active_course_sessions_no_active(self, session: Session):
        """测试没有活跃课堂时返回空列表"""
        sessions = get_teacher_active_course_sessions(session, teacher_id=999)
        assert sessions == []

    def test_get_course_sessions_by_schedule_and_week(self, session: Session, seed_refs):
        """测试按课表和周次查询"""
        # PG 强制 FK：course_sessions.schedule_id → course_schedules.id
        from app.models import CourseSchedule
        session.add(CourseSchedule(
            id=100, course_name="大数据", class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
            day_of_week=1, start_time="08:00", end_time="09:40",
        ))
        session.commit()

        cs = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=4,
            teacher_name="赵老师",
            schedule_id=100,
            week_number=3
        )
        result = get_course_sessions_by_schedule_and_week(session, schedule_id=100, week_number=3)
        assert result is not None
        assert result.id == cs.id

    def test_get_course_sessions_by_schedule_and_week_not_found(self, session: Session):
        """测试按课表和周次查询无结果"""
        result = get_course_sessions_by_schedule_and_week(session, schedule_id=999, week_number=99)
        assert result is None


class TestEndCourseSession:
    """测试结束上课功能"""

    def test_end_course_session_sets_status_ended(self, session: Session, seed_refs):
        """测试结束课堂后状态变为 ended，有 end_time"""
        started = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )
        session_id = started.id

        ended_list = end_course_session(session, teacher_id=1)

        assert len(ended_list) == 1
        assert ended_list[0].id == session_id
        assert ended_list[0].status == "ended"
        assert ended_list[0].end_time is not None

        active = get_teacher_active_course_sessions(session, teacher_id=1)
        assert active == []

    def test_end_course_session_with_class_id_filter(self, session: Session, seed_refs):
        """测试按班级 ID 结束课堂"""
        cs1 = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="张老师"
        )
        cs2 = start_course_session(
            session=session,
            class_id=seed_refs["二班"],
            teacher_id=1,
            teacher_name="张老师"
        )

        ended = end_course_session(session, teacher_id=1, class_id=seed_refs["一班"])
        assert len(ended) == 1
        assert ended[0].id == cs1.id
        assert ended[0].status == "ended"

        active = get_teacher_active_course_sessions(session, teacher_id=1)
        assert len(active) == 1
        assert active[0].id == cs2.id

    def test_end_course_session_no_active(self, session: Session):
        """测试没有活跃课堂时结束返回空列表"""
        ended = end_course_session(session, teacher_id=999)
        assert ended == []


class TestGetTeacherCourseSessions:
    """测试 get_teacher_course_sessions（支持状态筛选）"""

    def test_get_teacher_course_sessions_all(self, session: Session, seed_refs):
        """测试返回教师所有课堂"""
        cs1 = start_course_session(session, seed_refs["一班"], teacher_id=1, teacher_name="张老师")
        cs2 = start_course_session(session, seed_refs["二班"], teacher_id=1, teacher_name="张老师")
        end_course_session(session, teacher_id=1, class_id=seed_refs["一班"])

        sessions = get_teacher_course_sessions(session, teacher_id=1)
        assert len(sessions) == 2
        # 默认按 start_time desc
        ids = [s.id for s in sessions]
        assert cs2.id in ids
        assert cs1.id in ids

    def test_get_teacher_course_sessions_filter_by_status_ended(self, session: Session, seed_refs):
        """测试 status='ended' 正确过滤"""
        cs_active = start_course_session(session, seed_refs["一班"], teacher_id=2, teacher_name="李老师")
        cs_ended = start_course_session(session, seed_refs["二班"], teacher_id=2, teacher_name="李老师")
        end_course_session(session, teacher_id=2, class_id=seed_refs["二班"])

        ended_sessions = get_teacher_course_sessions(session, teacher_id=2, status="ended")
        assert len(ended_sessions) == 1
        assert ended_sessions[0].id == cs_ended.id

        active_sessions = get_teacher_course_sessions(session, teacher_id=2, status="active")
        assert len(active_sessions) == 1
        assert active_sessions[0].id == cs_active.id

    def test_get_teacher_course_sessions_only_returns_own_data(self, session: Session, seed_refs):
        """测试只返回指定教师的数据"""
        start_course_session(session, seed_refs["一班"], teacher_id=1, teacher_name="张老师")
        start_course_session(session, seed_refs["二班"], teacher_id=2, teacher_name="李老师")

        sessions = get_teacher_course_sessions(session, teacher_id=1)
        assert len(sessions) == 1
        assert sessions[0].class_id == seed_refs["一班"]
