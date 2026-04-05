"""
课表 CRUD 操作 - 架构分层修复

将 API 层直接操作 Session 的逻辑移到 CRUD 层，
保持 API 层只负责 HTTP 处理和参数验证。
"""
from typing import List, Optional
from sqlmodel import Session, select
from app.models import CourseSchedule, User


def get_schedule(session: Session, schedule_id: int) -> Optional[CourseSchedule]:
    """根据ID获取课表"""
    return session.get(CourseSchedule, schedule_id)


def get_schedules(
    session: Session,
    class_name: Optional[str] = None,
    day_of_week: Optional[int] = None,
    teacher_id: Optional[int] = None
) -> List[CourseSchedule]:
    """获取课表列表"""
    query = select(CourseSchedule)
    
    if class_name:
        query = query.where(CourseSchedule.class_name == class_name)
    if day_of_week:
        query = query.where(CourseSchedule.day_of_week == day_of_week)
    if teacher_id:
        query = query.where(CourseSchedule.teacher_id == teacher_id)
    
    return list(session.exec(query).all())


def delete_schedule(session: Session, schedule_id: int) -> bool:
    """
    删除课表
    
    Args:
        session: 数据库会话
        schedule_id: 课表ID
        
    Returns:
        bool: 删除成功返回 True，不存在返回 False
    """
    schedule = session.get(CourseSchedule, schedule_id)
    if not schedule:
        return False
    
    session.delete(schedule)
    session.commit()
    return True


def create_schedule(
    session: Session,
    course_name: str,
    class_name: str,
    teacher_id: Optional[int],
    teacher_name: str,
    day_of_week: int,
    start_time: str,
    end_time: str,
    classroom: str,
    week_start: int,
    week_end: int
) -> CourseSchedule:
    """
    创建课表
    
    Args:
        session: 数据库会话
        course_name: 课程名称
        class_name: 班级名称
        teacher_id: 教师ID（可选）
        teacher_name: 教师姓名
        day_of_week: 星期几（1-7）
        start_time: 开始时间（HH:MM）
        end_time: 结束时间（HH:MM）
        classroom: 教室
        week_start: 开始周
        week_end: 结束周
        
    Returns:
        创建的课表对象
    """
    from datetime import datetime
    
    schedule = CourseSchedule(
        course_name=course_name,
        class_name=class_name,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        classroom=classroom,
        week_start=week_start,
        week_end=week_end,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def import_schedules(
    session: Session,
    records: List[dict]
) -> tuple[int, List[str]]:
    """
    批量导入课表 - 完整业务逻辑封装（架构分层修复）
    
    将数据校验、查重、教师查找等业务逻辑完全封装在CRUD层，
    API层只负责HTTP处理和调用此函数。
    
    Args:
        session: 数据库会话
        records: 课表记录列表，每个记录为字典，包含：
                - course_name: 课程名称
                - class_name: 班级名称
                - teacher_name: 教师姓名
                - day_of_week: 星期（1-7）
                - start_time: 开始时间
                - end_time: 结束时间
                - classroom: 教室（可选）
                - week_start: 开始周（可选，默认1）
                - week_end: 结束周（可选，默认20）
        
    Returns:
        tuple: (导入成功数量, 错误列表)
    """
    from datetime import datetime
    
    imported_count = 0
    errors = []
    
    for index, record in enumerate(records):
        try:
            # 数据校验
            course_name = str(record.get('course_name', '')).strip()
            class_name = str(record.get('class_name', '')).strip()
            teacher_name = str(record.get('teacher_name', '')).strip()
            day_of_week = record.get('day_of_week')
            start_time = str(record.get('start_time', '')).strip()
            end_time = str(record.get('end_time', '')).strip()
            
            # teacher_name 可选，其他字段必填
            if not all([course_name, class_name, start_time, end_time]):
                errors.append(f"第 {index + 2} 行: 存在空值")
                continue
            
            # 星期范围校验
            try:
                day_of_week = int(day_of_week)
                if day_of_week < 1 or day_of_week > 7:
                    errors.append(f"第 {index + 2} 行: 星期必须在 1-7 之间")
                    continue
            except (ValueError, TypeError):
                errors.append(f"第 {index + 2} 行: 星期格式无效")
                continue
            
            # 可选字段
            classroom = str(record.get('classroom', '')).strip() if record.get('classroom') else None
            week_start = int(record.get('week_start', 1)) if record.get('week_start') else 1
            week_end = int(record.get('week_end', 20)) if record.get('week_end') else 20
            
            # 查找教师ID
            teacher = session.exec(
                select(User).where(User.name == teacher_name)
            ).first()
            
            # 查重检查
            existing = session.exec(
                select(CourseSchedule).where(
                    CourseSchedule.course_name == course_name,
                    CourseSchedule.class_name == class_name,
                    CourseSchedule.teacher_name == teacher_name,
                    CourseSchedule.day_of_week == day_of_week,
                    CourseSchedule.start_time == start_time
                )
            ).first()
            
            if existing:
                errors.append(f"第 {index + 2} 行: 课程已存在（{course_name} - {class_name} - 星期{day_of_week} {start_time}）")
                continue
            
            # 创建课表
            schedule = CourseSchedule(
                course_name=course_name,
                class_name=class_name,
                teacher_id=teacher.id if teacher else None,
                teacher_name=teacher_name,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                classroom=classroom,
                week_start=week_start,
                week_end=week_end,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            session.add(schedule)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"第 {index + 2} 行: {str(e)}")
    
    if imported_count > 0:
        session.commit()
    
    return imported_count, errors
