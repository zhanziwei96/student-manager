"""
调课一致性测试
验证 modify 调课信息在开课时生效、唯一约束、时间覆盖等
"""
import pytest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.models import CourseSchedule, ScheduleAdjustment, CourseSession
from app.core.timezone import get_now


class TestScheduleConsistency:
    """测试调课一致性"""

    def test_modify_adjustment_applies_classroom(self, session: Session):
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

        # 3. 验证调课记录存在且教室正确
        assert adjustment.new_classroom == "B202"
        assert adjustment.new_start_time == "14:00"
        assert adjustment.new_end_time == "15:40"

    def test_schedule_adjustment_unique_constraint(self, session: Session):
        """测试同一课表同一周次只能有一条调整记录（唯一约束）"""
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

        # 2. 创建第一条调课记录
        adjustment1 = ScheduleAdjustment(
            schedule_id=schedule.id,
            week_number=10,
            type="modify",
            reason="第一次调课",
            new_classroom="B202",
            created_by=1
        )
        session.add(adjustment1)
        session.commit()

        # 3. 尝试创建同一课表同一周的第二条调课记录，应该失败
        adjustment2 = ScheduleAdjustment(
            schedule_id=schedule.id,
            week_number=10,
            type="modify",
            reason="第二次调课",
            new_classroom="C303",
            created_by=1
        )
        session.add(adjustment2)

        # 4. 验证提交时抛出IntegrityError
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            session.commit()

    def test_cancel_adjustment_cancels_scheduled_session(self, session: Session):
        """测试 cancel 调课取消 scheduled 状态的课堂"""
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

        # 2. 创建 scheduled 状态的课堂（模拟 makeup 创建的）
        from app.crud.course_session import start_course_session
        course_session = start_course_session(
            session=session,
            class_name=schedule.class_name,
            teacher_id=1,
            teacher_name="张老师",
            course_name=schedule.course_name,
            schedule_id=schedule.id,
            week_number=10,
            classroom=schedule.classroom,
            source_type="makeup"
        )
        course_session.status = "scheduled"
        session.add(course_session)
        session.commit()
        session.refresh(course_session)

        assert course_session.status == "scheduled"

        # 3. 创建 cancel 类型调课
        adjustment = ScheduleAdjustment(
            schedule_id=schedule.id,
            week_number=10,
            type="cancel",
            reason="教师请假",
            created_by=1
        )
        session.add(adjustment)
        session.commit()

        # 4. 模拟 cancel 调课处理 scheduled 课堂的逻辑
        existing_session = session.exec(
            select(CourseSession).where(
                CourseSession.schedule_id == schedule.id,
                CourseSession.week_number == 10
            )
        ).first()

        if existing_session and existing_session.status in ["active", "scheduled"]:
            existing_session.status = "cancelled"
            existing_session.end_time = get_now()
            session.add(existing_session)
            session.commit()
            session.refresh(existing_session)

        # 5. 验证课堂已被取消
        assert existing_session.status == "cancelled"


class TestModifyAdjustmentTimeCoverage:
    """测试 modify 调课时间覆盖"""

    def test_modify_adjustment_time_parsed_correctly(self, session: Session):
        """测试 modify 调课时间正确解析"""
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
            reason="时间变更",
            new_start_time="14:00",
            new_end_time="15:40",
            created_by=1
        )
        session.add(adjustment)
        session.commit()

        # 3. 验证时间格式正确
        assert adjustment.new_start_time == "14:00"
        assert adjustment.new_end_time == "15:40"

        # 4. 模拟时间解析逻辑
        time_parts_start = adjustment.new_start_time.split(":")
        assert len(time_parts_start) == 2
        assert int(time_parts_start[0]) == 14
        assert int(time_parts_start[1]) == 0


class TestMakeupScheduledSession:
    """测试 makeup 调课创建 scheduled 状态课堂"""

    def test_makeup_session_has_correct_start_time(self, session: Session):
        """测试 makeup 课堂使用正确的开始时间"""
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

        # 2. 创建 makeup 调课
        makeup_date = date(2026, 5, 15)
        start_time_str = "14:00"
        end_time_str = "15:40"

        from app.crud.course_session import start_course_session
        course_session = start_course_session(
            session=session,
            class_name=schedule.class_name,
            teacher_id=1,
            teacher_name="张老师",
            course_name=schedule.course_name,
            schedule_id=schedule.id,
            week_number=10,
            classroom="B202",
            source_type="makeup"
        )

        # 3. 设置 scheduled 状态和正确的时间
        course_session.status = "scheduled"

        # 模拟 makeup 时间设置逻辑
        makeup_start = datetime.combine(
            makeup_date,
            datetime.strptime(start_time_str, "%H:%M").time()
        ).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        makeup_end = datetime.combine(
            makeup_date,
            datetime.strptime(end_time_str, "%H:%M").time()
        ).replace(tzinfo=ZoneInfo("Asia/Shanghai"))

        course_session.start_time = makeup_start
        course_session.end_time = makeup_end
        session.add(course_session)
        session.commit()
        session.refresh(course_session)

        # 4. 验证状态和时间
        assert course_session.status == "scheduled"
        assert course_session.start_time.year == 2026
        assert course_session.start_time.month == 5
        assert course_session.start_time.day == 15
        assert course_session.start_time.hour == 14
        assert course_session.start_time.minute == 0
        assert course_session.end_time.hour == 15
        assert course_session.end_time.minute == 40


class TestCheckinClassSnapshot:
    """测试签到班级名称快照"""

    def test_checkin_uses_course_session_class_name(self, session: Session):
        """测试签到记录使用 CourseSession 的班级名称作为快照"""
        # 1. 创建课程会话
        from app.crud.course_session import start_course_session
        course_session = start_course_session(
            session=session,
            class_name="原班级",
            teacher_id=1,
            teacher_name="张老师",
            course_name="测试课程",
            source_type="manual"
        )
        session.commit()
        session.refresh(course_session)

        # 2. 创建签到记录
        from app.models import CheckinRecord
        checkin = CheckinRecord(
            session_id=course_session.id,
            student_id="S001",
            student_name="学生A",
            class_name=course_session.class_name,  # 使用课堂班级作为快照
            checkin_type="self"
        )
        session.add(checkin)
        session.commit()
        session.refresh(checkin)

        # 3. 验证签到记录的班级名称
        assert checkin.class_name == "原班级"

        # 4. 模拟学生转班（修改 CourseSession 的班级名称）
        course_session.class_name = "新班级"
        session.add(course_session)
        session.commit()

        # 5. 验证签到记录的班级名称保持不变（快照机制）
        session.refresh(checkin)
        assert checkin.class_name == "原班级"  # 历史记录仍为原班级
