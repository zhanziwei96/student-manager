"""
ScheduleAdjustment CRUD 单元测试
"""
import pytest
from datetime import date
from sqlmodel import Session
from app.crud.schedule_adjustment import (
    create_adjustment,
    get_adjustment,
    get_adjustments,
    has_active_session,
    has_ended_session,
)
from app.crud.course_session import start_course_session, end_course_session
from app.models import CourseSchedule, ScheduleAdjustment


class TestScheduleAdjustmentCRUD:
    """测试 ScheduleAdjustment CRUD 操作"""

    def _create_schedule(self, session: Session, refs: dict, course_name: str = "测试课程",
                         class_name: str = "一班", teacher_id: int = 1) -> CourseSchedule:
        """辅助方法：创建课表记录（class_id/semester_id 为纯 FK 锚点，取自 seed_refs）"""
        schedule = CourseSchedule(
            course_name=course_name,
            class_id=refs[class_name],
            semester_id=refs["semester_id"],
            teacher_id=teacher_id,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A101",
            week_start=1,
            week_end=16,
            week_type="all"
        )
        session.add(schedule)
        session.commit()
        session.refresh(schedule)
        return schedule

    def test_create_adjustment(self, session: Session, seed_refs):
        """测试创建调整记录"""
        schedule = self._create_schedule(session, seed_refs)
        adj = create_adjustment(
            session=session,
            schedule_id=schedule.id,
            week_number=3,
            adjustment_type="cancel",
            created_by=1,
            reason="教师请假"
        )

        assert adj.schedule_id == schedule.id
        assert adj.week_number == 3
        assert adj.type == "cancel"
        assert adj.reason == "教师请假"
        assert adj.created_by == 1
        assert adj.id is not None

    def test_create_adjustment_with_new_fields(self, session: Session, seed_refs):
        """测试创建调整记录时包含新日期、时间和地点"""
        schedule = self._create_schedule(session, seed_refs)
        adj = create_adjustment(
            session=session,
            schedule_id=schedule.id,
            week_number=5,
            adjustment_type="modify",
            created_by=2,
            reason="调课",
            new_date=date(2026, 4, 10),
            new_start_time="14:00",
            new_end_time="15:40",
            new_classroom="B203",
            generated_session_id=None
        )

        assert adj.new_date == date(2026, 4, 10)
        assert adj.new_start_time == "14:00"
        assert adj.new_end_time == "15:40"
        assert adj.new_classroom == "B203"

    def test_get_adjustment(self, session: Session, seed_refs):
        """测试按 schedule_id 和 week_number 获取单条调整记录"""
        schedule = self._create_schedule(session, seed_refs)
        created = create_adjustment(
            session=session,
            schedule_id=schedule.id,
            week_number=4,
            adjustment_type="makeup",
            created_by=1
        )

        fetched = get_adjustment(session, schedule_id=schedule.id, week_number=4)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.type == "makeup"

    def test_get_adjustment_not_found(self, session: Session):
        """测试不存在的调整记录返回 None"""
        result = get_adjustment(session, schedule_id=9999, week_number=99)
        assert result is None

    def test_get_adjustments_by_schedule_id(self, session: Session, seed_refs):
        """测试按条件查询调整记录列表（按 schedule_id）"""
        schedule1 = self._create_schedule(session, seed_refs, course_name="课程A")
        schedule2 = self._create_schedule(session, seed_refs, course_name="课程B", class_name="二班")
        create_adjustment(session, schedule_id=schedule1.id, week_number=2, adjustment_type="cancel", created_by=1)
        create_adjustment(session, schedule_id=schedule1.id, week_number=3, adjustment_type="modify", created_by=1)
        create_adjustment(session, schedule_id=schedule2.id, week_number=2, adjustment_type="makeup", created_by=1)

        results = get_adjustments(session, schedule_id=schedule1.id)
        assert len(results) == 2
        for r in results:
            assert r.schedule_id == schedule1.id

    def test_get_adjustments_by_week_number(self, session: Session, seed_refs):
        """测试按周次过滤调整记录"""
        schedule = self._create_schedule(session, seed_refs)
        create_adjustment(session, schedule_id=schedule.id, week_number=2, adjustment_type="cancel", created_by=1)
        create_adjustment(session, schedule_id=schedule.id, week_number=3, adjustment_type="modify", created_by=1)

        results = get_adjustments(session, week_number=3)
        assert len(results) == 1
        assert results[0].type == "modify"

    def test_get_adjustments_by_class_name(self, session: Session, seed_refs):
        """测试按班级名称过滤调整记录"""
        schedule_a = self._create_schedule(session, seed_refs, class_name="一班")
        schedule_b = self._create_schedule(session, seed_refs, class_name="二班")
        create_adjustment(session, schedule_id=schedule_a.id, week_number=2, adjustment_type="cancel", created_by=1)
        create_adjustment(session, schedule_id=schedule_b.id, week_number=2, adjustment_type="makeup", created_by=1)

        results = get_adjustments(session, class_name="一班")
        assert len(results) == 1
        assert results[0].schedule_id == schedule_a.id

    def test_has_active_session_true(self, session: Session, seed_refs):
        """测试 has_active_session 在存在活跃课堂时返回 True"""
        schedule = self._create_schedule(session, seed_refs)
        start_course_session(
            session=session,
            class_name="一班",
            teacher_id=schedule.teacher_id,
            teacher_name=schedule.teacher_name,
            schedule_id=schedule.id,
            week_number=2
        )

        assert has_active_session(session, schedule.id, 2) is True

    def test_has_active_session_false(self, session: Session, seed_refs):
        """测试 has_active_session 在无活跃课堂时返回 False"""
        schedule = self._create_schedule(session, seed_refs)
        start_course_session(
            session=session,
            class_name="一班",
            teacher_id=schedule.teacher_id,
            teacher_name=schedule.teacher_name,
            schedule_id=schedule.id,
            week_number=2
        )
        end_course_session(session, teacher_id=schedule.teacher_id, class_name="一班")

        assert has_active_session(session, schedule.id, 2) is False
        assert has_active_session(session, schedule.id, 3) is False  # 不同周次

    def test_has_ended_session_true(self, session: Session, seed_refs):
        """测试 has_ended_session 在存在已结束课堂时返回 True"""
        schedule = self._create_schedule(session, seed_refs)
        start_course_session(
            session=session,
            class_name="一班",
            teacher_id=schedule.teacher_id,
            teacher_name=schedule.teacher_name,
            schedule_id=schedule.id,
            week_number=4
        )
        end_course_session(session, teacher_id=schedule.teacher_id, class_name="一班")

        assert has_ended_session(session, schedule.id, 4) is True

    def test_has_ended_session_false(self, session: Session, seed_refs):
        """测试 has_ended_session 在没有已结束课堂时返回 False"""
        schedule = self._create_schedule(session, seed_refs)
        # 未创建任何课堂
        assert has_ended_session(session, schedule.id, 1) is False

        # 活跃中不算 ended
        start_course_session(
            session=session,
            class_name="一班",
            teacher_id=schedule.teacher_id,
            teacher_name=schedule.teacher_name,
            schedule_id=schedule.id,
            week_number=1
        )
        assert has_ended_session(session, schedule.id, 1) is False
