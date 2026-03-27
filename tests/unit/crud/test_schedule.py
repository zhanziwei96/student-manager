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
