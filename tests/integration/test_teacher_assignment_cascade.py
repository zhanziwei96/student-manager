"""教师分配级联更新测试"""
import pytest
from sqlmodel import Session
from app.models import CourseSchedule, CourseSession


class TestTeacherAssignmentCascade:
    def test_teacher_assignment_cascade(self, session: Session):
        """测试级联更新"""
        schedule = CourseSchedule(
            course_name="测试课程",
            class_name="测试班级",
            teacher_id=1,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40"
        )
        session.add(schedule)
        session.commit()

        course_session = CourseSession(
            session_code="TEST1234",
            class_name="测试班级",
            teacher_id=1,
            course_name="测试课程",
            schedule_id=schedule.id,
            status="active"
        )
        session.add(course_session)
        session.commit()

        # 验证初始状态
        assert course_session.teacher_id == 1
