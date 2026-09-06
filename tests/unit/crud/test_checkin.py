"""
签到 CRUD 单元测试
"""
import pytest
from datetime import datetime, date, time
from sqlmodel import Session
from app.crud.checkin import (
    get_today_checkins, create_checkin, has_checked_in_today,
    get_student_score_logs, is_device_checked_in_session
)
from app.crud.course_session import start_course_session, end_course_session
from app.models import CheckinRecord, ScoreLog


class TestCheckinCRUD:
    """测试签到 CRUD"""

    def test_create_checkin(self, session: Session):
        """测试创建签到记录 - 使用 session_id"""
        # 先创建课堂会话
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        checkin = create_checkin(
            session,
            student_id="S001",
            student_name="张三",
            class_name="软件1班",
            session_id=cs.id,
            checkin_type="self"
        )

        assert checkin.student_id == "S001"
        assert checkin.student_name == "张三"
        assert checkin.class_name == "软件1班"
        assert checkin.checkin_type == "self"
        assert checkin.session_id == cs.id

    def test_has_checked_in_today(self, session: Session):
        """测试检查今日是否已签到"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")
        create_checkin(session, "S001", "张三", "软件1班", session_id=cs.id)

        # 应该返回已签到
        assert has_checked_in_today(session, "S001") is True

        # 其他学生未签到
        assert has_checked_in_today(session, "S002") is False

    def test_get_today_checkins(self, session: Session):
        """测试获取今日签到列表"""
        # 先创建课堂会话
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        # 创建今日签到
        create_checkin(session, "S001", "张三", "软件1班", session_id=cs.id)
        create_checkin(session, "S002", "李四", "软件1班", session_id=cs.id)
        create_checkin(session, "S003", "王五", "软件2班", session_id=cs.id)

        # 获取所有今日签到
        checkins = get_today_checkins(session)
        assert len(checkins) == 3

        # 按班级过滤
        checkins = get_today_checkins(session, class_name="软件1班")
        assert len(checkins) == 2

    def test_create_checkin_with_device(self, session: Session):
        """测试创建签到记录（带设备信息）"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        checkin = create_checkin(
            session,
            student_id="S001",
            student_name="张三",
            class_name="软件1班",
            session_id=cs.id,
            device_id="device123",
            device_info='{"platform": "test"}'
        )

        assert checkin.student_id == "S001"
        assert checkin.device_id == "device123"
        assert checkin.device_info == '{"platform": "test"}'

    def test_is_device_checked_in_session(self, session: Session):
        """测试检查设备是否已在课堂签到"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        # 初始状态：设备未签到
        assert is_device_checked_in_session(session, "device123", cs.id) is False

        # 创建设备签到
        create_checkin(
            session, "S001", "张三", "软件1班", session_id=cs.id,
            device_id="device123"
        )

        # 设备已签到
        assert is_device_checked_in_session(session, "device123", cs.id) is True

        # 其他设备未签到
        assert is_device_checked_in_session(session, "device456", cs.id) is False

    def test_is_device_checked_in_session_empty_device_id(self, session: Session):
        """测试空设备ID检查"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        # 空设备ID应返回False
        assert is_device_checked_in_session(session, "", cs.id) is False
        assert is_device_checked_in_session(session, None, cs.id) is False


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

    def test_get_student_score_logs_with_offset(self, session: Session):
        """测试分数日志 offset 分页（加载更多场景）"""
        # 创建 10 条分数日志
        for i in range(10):
            log = ScoreLog(
                student_id="S002",
                old_score=80.0 + i,
                new_score=81.0 + i,
                delta=1.0,
                reason=f"加分{i+1}",
                operator="老师"
            )
            session.add(log)
        session.commit()

        page1 = get_student_score_logs(session, "S002", limit=4, offset=0)
        page2 = get_student_score_logs(session, "S002", limit=4, offset=4)
        page3 = get_student_score_logs(session, "S002", limit=4, offset=8)

        assert len(page1) == 4
        assert len(page2) == 4
        assert len(page3) == 2

        # 三页 id 互不重复且覆盖全部 10 条
        ids = {log.id for log in page1 + page2 + page3}
        assert len(ids) == 10

    def test_get_student_score_logs_offset_without_limit(self, session: Session):
        """offset 单独使用时仍受默认 limit 约束"""
        for i in range(5):
            log = ScoreLog(
                student_id="S003",
                old_score=80.0 + i,
                new_score=81.0 + i,
                delta=1.0,
                reason=f"加分{i+1}",
                operator="老师"
            )
            session.add(log)
        session.commit()

        logs = get_student_score_logs(session, "S003", offset=3)
        assert len(logs) == 2
