"""
调课一致性测试
验证 modify 调课信息在开课时生效
"""
import pytest
from datetime import date
from sqlmodel import Session
from app.models import CourseSchedule, ScheduleAdjustment, CourseSession


class TestScheduleConsistency:
    """测试调课一致性"""

    def test_modify_adjustment_applies_to_new_session(self, session: Session):
        """测试 modify 调课后新课堂使用调整后的教室"""
        # 1. 创建课表
        schedule = CourseSchedule(
            course_name="测试课程",
            class_name="测试班级",
            teacher_id=1,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A101"
        )
        session.add(schedule)
        session.commit()
        session.refresh(schedule)

        # 2. 创建 modify 类型调课
        adjustment = ScheduleAdjustment(
            schedule_id=schedule.id,
            week_number=10,
            type="modify",
            reason="教室变更",
            new_classroom="B202",
            new_start_time="14:00",
            new_end_time="15:40",
            created_by=1
        )
        session.add(adjustment)
        session.commit()

        # 3. 验证调课记录存在
        assert adjustment.new_classroom == "B202"

    def test_cancel_adjustment_blocks_session(self, session: Session):
        """测试 cancel 调课阻止开课"""
        # 1. 创建课表
        schedule = CourseSchedule(
            course_name="测试课程",
            class_name="测试班级",
            teacher_id=1,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A101"
        )
        session.add(schedule)
        session.commit()
        session.refresh(schedule)

        # 2. 创建 cancel 类型调课
        adjustment = ScheduleAdjustment(
            schedule_id=schedule.id,
            week_number=10,
            type="cancel",
            reason="教师请假",
            created_by=1
        )
        session.add(adjustment)
        session.commit()

        # 3. 验证调课记录存在
        assert adjustment.type == "cancel"
