"""
签到 CRUD 单元测试
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
        class_session = start_class(session, "软件1班")
        
        assert class_session.active is True
        assert class_session.class_name == "软件1班"
        assert class_session.start_time is not None
    
    def test_get_class_session(self, session: Session):
        """测试获取上课状态"""
        start_class(session, "软件1班")
        
        found = get_class_session(session)
        assert found is not None
        assert found.class_name == "软件1班"
    
    def test_end_class(self, session: Session):
        """测试结束上课"""
        start_class(session, "软件1班")
        end_class(session)
        
        class_session = get_class_session(session)
        assert class_session.active is False
        assert class_session.class_name is None


class TestCheckinCRUD:
    """测试签到 CRUD"""
    
    def test_create_checkin(self, session: Session):
        """测试创建签到记录"""
        checkin = create_checkin(
            session,
            student_id="S001",
            student_name="张三",
            class_name="软件1班",
            checkin_type="self"
        )
        
        assert checkin.student_id == "S001"
        assert checkin.student_name == "张三"
        assert checkin.class_name == "软件1班"
        assert checkin.checkin_type == "self"
    
    def test_has_checked_in_today(self, session: Session):
        """测试检查今日是否已签到"""
        create_checkin(session, "S001", "张三", "软件1班")
        
        # 应该返回已签到
        assert has_checked_in_today(session, "S001") is True
        
        # 其他学生未签到
        assert has_checked_in_today(session, "S002") is False
    
    def test_get_today_checkins(self, session: Session):
        """测试获取今日签到列表"""
        from datetime import datetime, timedelta
        
        # 创建今日签到
        create_checkin(session, "S001", "张三", "软件1班")
        create_checkin(session, "S002", "李四", "软件1班")
        create_checkin(session, "S003", "王五", "软件2班")
        
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
