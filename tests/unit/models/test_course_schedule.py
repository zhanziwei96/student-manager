"""
课表模型单元测试
"""
import pytest
from sqlmodel import Session
from app.models.course_schedule import CourseSchedule


def test_course_schedule_creation(session: Session):
    """测试课表创建"""
    schedule = CourseSchedule(
        course_name="计算机基础",
        class_name="2025康复治疗技术1班",
        teacher_name="张老师",
        day_of_week=1,
        start_time="08:00",
        end_time="09:40",
        classroom="A-101",
        week_start=1,
        week_end=20
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    
    assert schedule.id is not None
    assert schedule.course_name == "计算机基础"
    assert schedule.class_name == "2025康复治疗技术1班"
    assert schedule.teacher_name == "张老师"
    assert schedule.day_of_week == 1
    assert schedule.start_time == "08:00"
    assert schedule.end_time == "09:40"
    assert schedule.classroom == "A-101"
    assert schedule.week_start == 1
    assert schedule.week_end == 20


def test_course_schedule_default_values(session: Session):
    """测试课表默认值"""
    schedule = CourseSchedule(
        course_name="测试课程",
        class_name="测试班级",
        teacher_name="测试教师",
        day_of_week=2,
        start_time="10:00",
        end_time="11:40"
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    
    assert schedule.week_start == 1
    assert schedule.week_end == 20
    assert schedule.classroom is None


def test_course_schedule_all_weekdays(session: Session):
    """测试所有星期几的课程"""
    for day in range(1, 8):
        schedule = CourseSchedule(
            course_name=f"课程{day}",
            class_name="测试班级",
            teacher_name="测试教师",
            day_of_week=day,
            start_time="08:00",
            end_time="09:40"
        )
        session.add(schedule)
    
    session.commit()
    
    # 验证所有课程都已创建
    schedules = session.query(CourseSchedule).all()
    assert len(schedules) == 7
    
    # 验证星期几正确
    for i, schedule in enumerate(sorted(schedules, key=lambda x: x.day_of_week)):
        assert schedule.day_of_week == i + 1


def test_course_schedule_query_by_day(session: Session):
    """测试按星期查询课表"""
    # 创建周一的课程
    schedule1 = CourseSchedule(
        course_name="周一课程1",
        class_name="班级A",
        teacher_name="教师A",
        day_of_week=1,
        start_time="08:00",
        end_time="09:40"
    )
    schedule2 = CourseSchedule(
        course_name="周一课程2",
        class_name="班级B",
        teacher_name="教师B",
        day_of_week=1,
        start_time="10:00",
        end_time="11:40"
    )
    schedule3 = CourseSchedule(
        course_name="周二课程",
        class_name="班级C",
        teacher_name="教师C",
        day_of_week=2,
        start_time="08:00",
        end_time="09:40"
    )
    
    session.add_all([schedule1, schedule2, schedule3])
    session.commit()
    
    # 查询周一的课程
    monday_schedules = session.query(CourseSchedule).filter(
        CourseSchedule.day_of_week == 1
    ).all()
    
    assert len(monday_schedules) == 2
    assert all(s.day_of_week == 1 for s in monday_schedules)


def test_course_schedule_query_by_class(session: Session):
    """测试按班级查询课表"""
    schedule1 = CourseSchedule(
        course_name="课程1",
        class_name="2025康复治疗技术1班",
        teacher_name="教师A",
        day_of_week=1,
        start_time="08:00",
        end_time="09:40"
    )
    schedule2 = CourseSchedule(
        course_name="课程2",
        class_name="2025康复治疗技术1班",
        teacher_name="教师B",
        day_of_week=2,
        start_time="10:00",
        end_time="11:40"
    )
    schedule3 = CourseSchedule(
        course_name="课程3",
        class_name="2025中药学1班",
        teacher_name="教师C",
        day_of_week=1,
        start_time="08:00",
        end_time="09:40"
    )
    
    session.add_all([schedule1, schedule2, schedule3])
    session.commit()
    
    # 查询特定班级的课程
    class_schedules = session.query(CourseSchedule).filter(
        CourseSchedule.class_name == "2025康复治疗技术1班"
    ).all()
    
    assert len(class_schedules) == 2
    assert all(s.class_name == "2025康复治疗技术1班" for s in class_schedules)


def test_course_schedule_delete(session: Session):
    """测试删除课表"""
    schedule = CourseSchedule(
        course_name="待删除课程",
        class_name="测试班级",
        teacher_name="测试教师",
        day_of_week=1,
        start_time="08:00",
        end_time="09:40"
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    
    schedule_id = schedule.id
    
    # 删除课程
    session.delete(schedule)
    session.commit()
    
    # 验证已删除
    deleted_schedule = session.get(CourseSchedule, schedule_id)
    assert deleted_schedule is None
