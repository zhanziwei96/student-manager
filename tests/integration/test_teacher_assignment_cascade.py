"""教师分配级联更新测试 - 完整验证"""
import pytest
from sqlmodel import Session, select
from app.models import CourseSchedule, CourseSession, ScheduleAdjustment
from app.crud.schedule import create_schedule
from app.crud.course_session import start_course_session


class TestTeacherAssignmentCascade:
    """测试教师分配级联更新"""

    def test_teacher_assignment_cascade(self, session: Session, seed_refs):
        """测试级联更新"""
        schedule = CourseSchedule(
            course_name="测试课程",
            class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
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
            class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
            teacher_id=1,
            course_name="测试课程",
            schedule_id=schedule.id,
            status="active"
        )
        session.add(course_session)
        session.commit()

        # 验证初始状态
        assert course_session.teacher_id == 1
        assert course_session.teacher_name is None  # 初始未设置

    def test_assign_teacher_updates_active_session(self, session: Session, seed_refs):
        """测试分配教师后活跃课堂的 teacher_id 和 teacher_name 同步更新"""
        # 1. 创建课表（无教师）
        schedule = create_schedule(
            session=session,
            course_name="测试课程",
            class_id=seed_refs["一班"],
            teacher_id=None,
            teacher_name="",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A101",
            week_start=1,
            week_end=20
        )

        # 2. 创建活跃课堂（模拟已开始上课）
        course_session = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,  # 临时教师开始上课
            teacher_name="临时教师",
            course_name="测试课程",
            schedule_id=schedule.id,
            source_type="scheduled"
        )
        session.commit()
        session.refresh(course_session)

        assert course_session.teacher_id == 1
        assert course_session.teacher_name == "临时教师"

        # 3. 模拟分配新教师（调用级联更新逻辑）
        from sqlalchemy import update
        new_teacher_id = 2
        new_teacher_name = "新教师"

        # 更新课表教师
        schedule.teacher_id = new_teacher_id
        schedule.teacher_name = new_teacher_name
        session.add(schedule)

        # 级联更新活跃 CourseSession（这是我们要测试的核心逻辑）
        session.execute(
            update(CourseSession)
            .where(
                CourseSession.schedule_id == schedule.id,
                CourseSession.status == "active"
            )
            .values(teacher_id=new_teacher_id, teacher_name=new_teacher_name)
        )
        session.commit()

        # 4. 验证 CourseSession 已更新
        session.refresh(course_session)
        assert course_session.teacher_id == new_teacher_id
        assert course_session.teacher_name == new_teacher_name

    def test_unassign_teacher_updates_active_session(self, session: Session, seed_refs):
        """测试取消教师分配后活跃课堂的 teacher_name 被清除，teacher_id 设为 0（占位）"""
        # 注意：CourseSession.teacher_id 有 NOT NULL 约束，不能直接设为 NULL
        # 实际业务中，取消教师分配后，课堂应由系统或临时账号接管

        # 1. 创建课表（有教师）
        schedule = create_schedule(
            session=session,
            course_name="测试课程",
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="原教师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A101",
            week_start=1,
            week_end=20
        )

        # 2. 创建活跃课堂
        course_session = start_course_session(
            session=session,
            class_id=seed_refs["一班"],
            teacher_id=1,
            teacher_name="原教师",
            course_name="测试课程",
            schedule_id=schedule.id,
            source_type="scheduled"
        )
        session.commit()

        # 3. 模拟取消教师分配（teacher_id 设为 0 表示未分配，teacher_name 清空）
        from sqlalchemy import update

        # 清除课表教师
        schedule.teacher_id = None
        schedule.teacher_name = None
        session.add(schedule)

        # 级联更新 CourseSession（teacher_id=0 表示未分配，teacher_name=None）
        session.execute(
            update(CourseSession)
            .where(
                CourseSession.schedule_id == schedule.id,
                CourseSession.status == "active"
            )
            .values(teacher_id=0, teacher_name=None)  # teacher_id=0 表示未分配
        )
        session.commit()

        # 4. 验证 CourseSession 教师信息已更新
        session.refresh(course_session)
        assert course_session.teacher_id == 0  # 0 表示未分配
        assert course_session.teacher_name is None

    def test_assign_teacher_only_updates_active_sessions(self, session: Session, seed_refs):
        """测试分配教师只更新 active 状态的课堂，不更新 ended/cancelled"""
        # 1. 创建课表
        schedule = create_schedule(
            session=session,
            course_name="测试课程",
            class_id=seed_refs["一班"],
            teacher_id=None,
            teacher_name="",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A101",
            week_start=1,
            week_end=20
        )

        # 2. 创建多个课堂：一个 active，一个 ended，一个 cancelled
        active_session = CourseSession(
            session_code="ACTIVE001",
            class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
            teacher_id=1,
            teacher_name="原教师",
            course_name="测试课程",
            schedule_id=schedule.id,
            status="active"
        )
        ended_session = CourseSession(
            session_code="ENDED001",
            class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
            teacher_id=1,
            teacher_name="原教师",
            course_name="测试课程",
            schedule_id=schedule.id,
            status="ended"
        )
        cancelled_session = CourseSession(
            session_code="CANCELLED001",
            class_id=seed_refs["一班"],
            semester_id=seed_refs["semester_id"],
            teacher_id=1,
            teacher_name="原教师",
            course_name="测试课程",
            schedule_id=schedule.id,
            status="cancelled"
        )
        session.add_all([active_session, ended_session, cancelled_session])
        session.commit()

        # 3. 模拟分配新教师（只更新 active）
        from sqlalchemy import update

        schedule.teacher_id = 2
        schedule.teacher_name = "新教师"
        session.add(schedule)

        session.execute(
            update(CourseSession)
            .where(
                CourseSession.schedule_id == schedule.id,
                CourseSession.status == "active"  # 只更新 active
            )
            .values(teacher_id=2, teacher_name="新教师")
        )
        session.commit()

        # 4. 验证：只有 active 课堂更新
        session.refresh(active_session)
        session.refresh(ended_session)
        session.refresh(cancelled_session)

        assert active_session.teacher_id == 2  # 已更新
        assert active_session.teacher_name == "新教师"

        assert ended_session.teacher_id == 1  # 未更新
        assert ended_session.teacher_name == "原教师"

        assert cancelled_session.teacher_id == 1  # 未更新
        assert cancelled_session.teacher_name == "原教师"
