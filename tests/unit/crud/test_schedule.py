"""
课表 CRUD 单元测试 - 架构分层修复
"""
import pytest
from sqlmodel import Session
from datetime import datetime
from app.crud.schedule import (
    get_schedule, get_schedules, delete_schedule,
    create_schedule, import_schedules
)
from app.models import CourseSchedule, User


class TestScheduleCRUD:
    """测试课表 CRUD 操作"""

    @pytest.fixture(autouse=True)
    def _seed_class_students(self, session: Session):
        """课表导入校验要求班级有启用学生：为导入测试所用班级预置启用学生"""
        from app.models import Student
        for i, cls in enumerate(["导入班级1", "导入班级2", "班级1", "班级2"]):
            session.add(Student(
                student_id=f"TS{i:03d}", name=f"学生{i}", class_name=cls, score=60.0,
            ))
        session.commit()

    def test_create_schedule(self, session: Session):
        """测试创建课表"""
        schedule = create_schedule(
            session=session,
            course_name="计算机基础",
            class_name="软件1班",
            teacher_id=1,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="A-101",
            week_start=1,
            week_end=20
        )
        
        assert schedule.course_name == "计算机基础"
        assert schedule.class_name == "软件1班"
        assert schedule.teacher_id == 1
        assert schedule.day_of_week == 1

    def test_get_schedule(self, session: Session):
        """测试获取课表"""
        schedule = create_schedule(
            session=session,
            course_name="数据结构",
            class_name="软件2班",
            teacher_id=None,
            teacher_name="",
            day_of_week=2,
            start_time="10:00",
            end_time="11:40",
            classroom="B-202",
            week_start=1,
            week_end=16
        )
        
        found = get_schedule(session, schedule.id)
        assert found is not None
        assert found.course_name == "数据结构"

    def test_get_schedule_not_found(self, session: Session):
        """测试获取不存在的课表"""
        result = get_schedule(session, 99999)
        assert result is None

    def test_get_schedules_with_filters(self, session: Session):
        """测试筛选课表"""
        # 创建测试数据
        create_schedule(session, "课程A", "班级A", 1, "教师A", 1, "08:00", "09:40", "A1", 1, 20)
        create_schedule(session, "课程B", "班级B", 2, "教师B", 2, "10:00", "11:40", "B2", 1, 20)
        create_schedule(session, "课程C", "班级A", 1, "教师A", 3, "14:00", "15:40", "A2", 1, 20)
        
        # 按班级筛选
        result = get_schedules(session, class_name="班级A")
        assert len(result) == 2
        
        # 按星期筛选
        result = get_schedules(session, day_of_week=1)
        assert len(result) == 1
        
        # 按教师筛选
        result = get_schedules(session, teacher_id=2)
        assert len(result) == 1

    def test_delete_schedule(self, session: Session):
        """测试删除课表"""
        schedule = create_schedule(
            session=session,
            course_name="待删除课程",
            class_name="班级X",
            teacher_id=None,
            teacher_name="",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="X-101",
            week_start=1,
            week_end=20
        )
        
        success = delete_schedule(session, schedule.id)
        assert success is True
        
        # 确认已删除
        assert get_schedule(session, schedule.id) is None

    def test_delete_schedule_not_found(self, session: Session):
        """测试删除不存在的课表"""
        success = delete_schedule(session, 99999)
        assert success is False

    def test_delete_schedule_cascade_adjustments(self, session: Session):
        """测试删除课表级联删除关联的 ScheduleAdjustment"""
        from app.models import ScheduleAdjustment
        from app.crud.schedule_adjustment import create_adjustment

        # 1. 创建课表
        schedule = create_schedule(
            session=session,
            course_name="待删除课程",
            class_name="班级X",
            teacher_id=1,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="X-101",
            week_start=1,
            week_end=20
        )

        # 2. 创建关联的调课记录
        adjustment = create_adjustment(
            session=session,
            schedule_id=schedule.id,
            week_number=10,
            adjustment_type="modify",
            created_by=1,
            reason="测试调课",
            new_classroom="B202"
        )
        session.commit()

        # 验证调课记录存在
        assert adjustment.id is not None

        # 3. 删除课表
        success = delete_schedule(session, schedule.id)
        assert success is True

        # 4. 验证调课记录也被级联删除
        remaining = session.get(ScheduleAdjustment, adjustment.id)
        assert remaining is None

    def test_delete_schedule_cascade_non_active_sessions(self, session: Session):
        """测试删除课表级联删除非活跃的 CourseSession"""
        from app.crud.course_session import start_course_session
        from app.models import CourseSession

        # 1. 创建课表
        schedule = create_schedule(
            session=session,
            course_name="待删除课程",
            class_name="班级Y",
            teacher_id=1,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="Y-101",
            week_start=1,
            week_end=20
        )

        # 2. 创建 ended 状态的课堂
        ended_session = start_course_session(
            session=session,
            class_name="班级Y",
            teacher_id=1,
            teacher_name="张老师",
            course_name="待删除课程",
            schedule_id=schedule.id,
            source_type="scheduled"
        )
        ended_session.status = "ended"
        session.add(ended_session)

        # 3. 创建 cancelled 状态的课堂
        cancelled_session = start_course_session(
            session=session,
            class_name="班级Y",
            teacher_id=1,
            teacher_name="张老师",
            course_name="待删除课程",
            schedule_id=schedule.id,
            source_type="scheduled"
        )
        cancelled_session.status = "cancelled"
        session.add(cancelled_session)

        # 4. 创建 scheduled 状态的课堂
        scheduled_session = start_course_session(
            session=session,
            class_name="班级Y",
            teacher_id=1,
            teacher_name="张老师",
            course_name="待删除课程",
            schedule_id=schedule.id,
            source_type="scheduled"
        )
        scheduled_session.status = "scheduled"
        session.add(scheduled_session)

        session.commit()

        ended_id = ended_session.id
        cancelled_id = cancelled_session.id
        scheduled_id = scheduled_session.id

        # 5. 删除课表
        success = delete_schedule(session, schedule.id)
        assert success is True

        # 6. 验证非活跃课堂都被级联删除
        assert session.get(CourseSession, ended_id) is None
        assert session.get(CourseSession, cancelled_id) is None
        assert session.get(CourseSession, scheduled_id) is None

    def test_delete_schedule_blocked_by_active_session(self, session: Session):
        """测试活跃课堂阻止删除课表"""
        from app.crud.course_session import start_course_session
        from app.models import CourseSession
        from fastapi import HTTPException

        # 1. 创建课表
        schedule = create_schedule(
            session=session,
            course_name="有活跃课堂的课程",
            class_name="班级Z",
            teacher_id=1,
            teacher_name="张老师",
            day_of_week=1,
            start_time="08:00",
            end_time="09:40",
            classroom="Z-101",
            week_start=1,
            week_end=20
        )

        # 2. 创建 active 状态的课堂
        active_session = start_course_session(
            session=session,
            class_name="班级Z",
            teacher_id=1,
            teacher_name="张老师",
            course_name="有活跃课堂的课程",
            schedule_id=schedule.id,
            source_type="scheduled"
        )
        session.commit()

        # 3. 尝试删除课表应该失败
        with pytest.raises(HTTPException) as exc_info:
            delete_schedule(session, schedule.id)

        assert exc_info.value.status_code == 400
        assert "进行中的课堂" in exc_info.value.detail

        # 4. 验证课表和课堂都还在
        assert get_schedule(session, schedule.id) is not None
        assert session.get(CourseSession, active_session.id) is not None

        # 清理
        active_session.status = "ended"
        session.add(active_session)
        session.commit()
        delete_schedule(session, schedule.id)

    def test_import_schedules(self, session: Session):
        """测试批量导入课表 - 完整业务逻辑封装"""
        records = [
            {
                'course_name': '导入课程1',
                'class_name': '导入班级1',
                'teacher_name': '',
                'day_of_week': '1',
                'start_time': '08:00',
                'end_time': '09:40',
                'classroom': 'C-101',
                'week_start': '1',
                'week_end': '20'
            },
            {
                'course_name': '导入课程2',
                'class_name': '导入班级2',
                'teacher_name': '',
                'day_of_week': '2',
                'start_time': '10:00',
                'end_time': '11:40',
                'classroom': 'C-102',
                'week_start': '1',
                'week_end': '20'
            }
        ]
        
        imported, errors = import_schedules(session, records)
        
        assert imported == 2
        assert len(errors) == 0
        
        # 验证导入的数据
        schedules = get_schedules(session)
        assert len(schedules) == 2

    def test_import_schedules_with_errors(self, session: Session):
        """测试批量导入课表（含错误）- 完整业务逻辑封装"""
        records = [
            {
                'course_name': '有效课程',
                'class_name': '班级1',
                'teacher_name': '',
                'day_of_week': '1',
                'start_time': '08:00',
                'end_time': '09:40',
                'classroom': 'D-101',
                'week_start': '1',
                'week_end': '20'
            },
            {
                # 无效记录：缺少必需字段
                'course_name': '无效课程',
                'class_name': '班级2'
            }
        ]
        
        imported, errors = import_schedules(session, records)
        
        assert imported == 1
        assert len(errors) == 1
        assert "第 3 行" in errors[0]  # 索引+2

    def test_import_schedules_validation(self, session: Session):
        """测试导入数据校验 - 空值检查"""
        records = [
            {
                'course_name': '',  # 空值
                'class_name': '班级1',
                'teacher_name': '教师1',
                'day_of_week': '1',
                'start_time': '08:00',
                'end_time': '09:40',
            }
        ]
        
        imported, errors = import_schedules(session, records)
        
        assert imported == 0
        assert len(errors) == 1
        assert "存在空值" in errors[0]

    def test_import_schedules_day_of_week_validation(self, session: Session):
        """测试导入星期范围校验"""
        records = [
            {
                'course_name': '课程1',
                'class_name': '班级1',
                'teacher_name': '教师1',
                'day_of_week': '8',  # 无效：大于7
                'start_time': '08:00',
                'end_time': '09:40',
            }
        ]
        
        imported, errors = import_schedules(session, records)
        
        assert imported == 0
        assert len(errors) == 1
        assert "星期必须在 1-7 之间" in errors[0]

    def test_import_schedules_duplicate_check(self, session: Session):
        """测试导入查重检查"""
        # 先创建一个课程
        create_schedule(
            session, "重复课程", "班级1", None, "教师1", 1, "08:00", "09:40", "A101", 1, 20
        )
        
        # 尝试导入相同课程
        records = [
            {
                'course_name': '重复课程',
                'class_name': '班级1',
                'teacher_name': '教师1',
                'day_of_week': '1',
                'start_time': '08:00',
                'end_time': '09:40',
            }
        ]
        
        imported, errors = import_schedules(session, records)
        
        assert imported == 0
        assert len(errors) == 1
        assert "课程已存在" in errors[0]
