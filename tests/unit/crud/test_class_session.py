"""
ClassSession CRUD 单元测试
测试开始上课和获取课堂状态功能
"""
import pytest
from datetime import datetime
from app.crud.checkin import start_class, get_class_session, end_class
from app.models.checkin import ClassSession


class TestStartClass:
    """测试开始上课功能"""

    def test_start_class_with_course_name(self, session):
        """测试开始上课时传入 course_name 正确保存"""
        # 执行
        session = start_class(
            session=session,
            class_name="计算机1班",
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )
        
        # 验证
        assert session.class_name == "计算机1班"
        assert session.teacher_id == 1
        assert session.teacher_name == "张老师"
        assert session.course_name == "高等数学"
        assert session.active is True
        assert session.start_time is not None
        assert session.session_code is not None

    def test_start_class_without_course_name(self, session):
        """测试开始上课时不传 course_name 默认为 None"""
        # 执行
        new_session = start_class(
            session=session,
            class_name="软件工程班",
            teacher_id=2,
            teacher_name="李老师"
        )
        
        # 验证
        assert new_session.class_name == "软件工程班"
        assert new_session.course_name is None
        assert new_session.active is True

    def test_start_class_ends_previous_session(self, session):
        """测试开始新课程会自动结束该教师的旧课程"""
        # 先开始一个课程
        old_session = start_class(
            session=session,
            class_name="旧班级",
            teacher_id=1,
            teacher_name="张老师",
            course_name="旧课程"
        )
        
        # 再开始一个新课程
        new_session = start_class(
            session=session,
            class_name="新班级",
            teacher_id=1,
            teacher_name="张老师",
            course_name="新课程"
        )
        
        # 验证旧课程已结束
        session.refresh(old_session)
        assert old_session.active is False
        assert old_session.end_time is not None
        
        # 验证新课程是活跃的
        assert new_session.active is True


class TestGetClassSession:
    """测试获取课堂状态功能"""

    def test_get_class_session_returns_course_name(self, session):
        """测试获取课堂状态返回 course_name"""
        # 准备：创建活跃课堂
        started = start_class(
            session=session,
            class_name="计算机1班",
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )
        
        # 执行
        session = get_class_session(session, teacher_id=1)
        
        # 验证
        assert session is not None
        assert session.id == started.id
        assert session.course_name == "高等数学"
        assert session.class_name == "计算机1班"
        assert session.active is True

    def test_get_class_session_no_active_session(self, session):
        """测试没有活跃课堂时返回 None"""
        # 执行
        session = get_class_session(session, teacher_id=999)
        
        # 验证
        assert session is None

    def test_get_class_session_only_returns_active(self, session):
        """测试只返回活跃状态的课堂"""
        # 准备：创建并结束一个课堂
        start_class(
            session=session,
            class_name="已结束班级",
            teacher_id=1,
            teacher_name="张老师",
            course_name="已结束课程"
        )
        end_class(session, teacher_id=1)
        
        # 执行
        session = get_class_session(session, teacher_id=1)
        
        # 验证
        assert session is None


class TestEndClass:
    """测试结束上课功能"""

    def test_end_class_sets_course_name_session_inactive(self, session):
        """测试结束带 course_name 的课堂"""
        # 准备：创建活跃课堂
        started = start_class(
            session=session,
            class_name="计算机1班",
            teacher_id=1,
            teacher_name="张老师",
            course_name="高等数学"
        )
        session_id = started.id
        
        # 执行
        end_class(session, teacher_id=1)
        
        # 验证：通过 get_class_session 应该返回 None（已结束）
        active = get_class_session(session, teacher_id=1)
        assert active is None  # 已结束，不会返回
        
        # 从数据库直接查询验证
        from sqlmodel import select
        statement = select(ClassSession).where(ClassSession.id == session_id)
        results = session.exec(statement).all()
        assert len(results) == 1
        assert results[0].active is False
        assert results[0].end_time is not None
        assert results[0].course_name == "高等数学"
