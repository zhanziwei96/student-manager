"""
签到 CRUD 单元测试 - 已修复 API 变更
"""
import pytest
from datetime import datetime, date, time
from sqlmodel import Session
from app.crud import (
    get_class_session, start_class, end_class,
    get_today_checkins, create_checkin, has_checked_in_today,
    get_student_score_logs
)
from app.models import ClassSession, CheckinRecord, ScoreLog


class TestClassSessionCRUD:
    """测试上课状态 CRUD"""
    
    def test_start_class(self, session: Session):
        """测试开始上课"""
        class_session = start_class(session, "软件1班", teacher_id=1, teacher_name="张老师")
        
        assert class_session.active is True
        assert class_session.class_name == "软件1班"
        assert class_session.start_time is not None
        assert class_session.teacher_id == 1
        assert class_session.teacher_name == "张老师"
    
    def test_get_class_session(self, session: Session):
        """测试获取上课状态 - 使用 teacher_id"""
        start_class(session, "软件1班", teacher_id=1, teacher_name="张老师")
        
        found = get_class_session(session, teacher_id=1)
        assert found is not None
        assert found.class_name == "软件1班"
    
    def test_end_class(self, session: Session):
        """测试结束上课 - 使用 teacher_id"""
        start_class(session, "软件1班", teacher_id=1, teacher_name="张老师")
        end_class(session, teacher_id=1)
        
        class_session = get_class_session(session, teacher_id=1)
        assert class_session is None  # 结束后没有活跃的课堂


class TestCheckinCRUD:
    """测试签到 CRUD"""
    
    def test_create_checkin(self, session: Session):
        """测试创建签到记录 - 使用 session_id"""
        # 先创建课堂会话
        class_session = start_class(session, "软件1班", teacher_id=1, teacher_name="张老师")
        
        checkin = create_checkin(
            session,
            student_id="S001",
            student_name="张三",
            class_name="软件1班",
            session_id=class_session.id,  # 新增参数
            checkin_type="self"
        )
        
        assert checkin.student_id == "S001"
        assert checkin.student_name == "张三"
        assert checkin.class_name == "软件1班"
        assert checkin.checkin_type == "self"
        assert checkin.session_id == class_session.id
    
    def test_has_checked_in_today(self, session: Session):
        """测试检查今日是否已签到"""
        class_session = start_class(session, "软件1班", teacher_id=1, teacher_name="张老师")
        create_checkin(session, "S001", "张三", "软件1班", session_id=class_session.id)
        
        # 应该返回已签到
        assert has_checked_in_today(session, "S001") is True
        
        # 其他学生未签到
        assert has_checked_in_today(session, "S002") is False
    
    def test_get_today_checkins(self, session: Session):
        """测试获取今日签到列表"""
        from datetime import datetime, timedelta
        
        # 先创建课堂会话
        class_session = start_class(session, "软件1班", teacher_id=1, teacher_name="张老师")
        
        # 创建今日签到
        create_checkin(session, "S001", "张三", "软件1班", session_id=class_session.id)
        create_checkin(session, "S002", "李四", "软件1班", session_id=class_session.id)
        create_checkin(session, "S003", "王五", "软件2班", session_id=class_session.id)
        
        # 获取所有今日签到
        checkins = get_today_checkins(session)
        assert len(checkins) == 3
        
        # 按班级过滤
        checkins = get_today_checkins(session, class_name="软件1班")
        assert len(checkins) == 2


class TestScoreLogCRUD:
    """测试分数日志 CRUD"""
    
    def test_get_student_score_logs(self, session: Session):
        """测试获取学生分数日志"""
        # 创建分数日志
        for i in range(5):
            log = ScoreLog(
                student_id="S001",
                old_score=80.0 + i,
                new_score=81.0 + i,
                delta=1.0,
                reason=f"加分{i+1}",
                operator="老师"
            )
            session.add(log)
        session.commit()
        
        logs = get_student_score_logs(session, "S001", limit=3)
        assert len(logs) == 3
