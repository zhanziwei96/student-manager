"""
签到 CRUD 单元测试
"""
import pytest
from datetime import datetime, date, time
from sqlmodel import Session
from app.crud.checkin import (
    create_checkin, get_today_checkins, has_checked_in_today,
    is_device_checked_in_session,
)
from app.crud.course_session import start_course_session, end_course_session
from app.models import CheckinRecord


class TestCheckinCRUD:
    """测试签到 CRUD"""

    def test_create_checkin(self, session: Session, seed_refs):
        """测试创建签到记录 - 使用 session_id"""
        refs = seed_refs
        # 先创建课堂会话
        cs = start_course_session(session, refs["一班"], teacher_id=1, teacher_name="张老师")

        checkin = create_checkin(
            session,
            student_id="S001",
            student_name="张三",
            class_id=refs["一班"],
            session_id=cs.id,
            checkin_type="self"
        )

        assert checkin.student_id == "S001"
        assert checkin.student_name == "张三"
        assert checkin.class_id == refs["一班"]
        assert checkin.checkin_type == "self"
        assert checkin.session_id == cs.id

    def test_has_checked_in_today(self, session: Session, seed_refs):
        """测试检查今日是否已签到"""
        refs = seed_refs
        cs = start_course_session(session, refs["一班"], teacher_id=1, teacher_name="张老师")
        create_checkin(session, "S001", "张三", refs["一班"], session_id=cs.id)

        # 应该返回已签到
        assert has_checked_in_today(session, "S001", refs["一班"]) is True

        # 其他学生未签到
        assert has_checked_in_today(session, "S002", refs["一班"]) is False

    def test_get_today_checkins(self, session: Session, seed_refs):
        """测试获取今日签到列表"""
        refs = seed_refs
        # 先创建课堂会话
        cs = start_course_session(session, refs["一班"], teacher_id=1, teacher_name="张老师")

        # 创建今日签到
        create_checkin(session, "S001", "张三", refs["一班"], session_id=cs.id)
        create_checkin(session, "S002", "李四", refs["一班"], session_id=cs.id)
        create_checkin(session, "S003", "王五", refs["二班"], session_id=cs.id)

        # 获取所有今日签到
        checkins = get_today_checkins(session)
        assert len(checkins) == 3

        # 按班级过滤
        checkins = get_today_checkins(session, class_id=refs["一班"])
        assert len(checkins) == 2

    def test_create_checkin_with_device(self, session: Session, seed_refs):
        """测试创建签到记录（带设备信息）"""
        refs = seed_refs
        cs = start_course_session(session, refs["一班"], teacher_id=1, teacher_name="张老师")

        checkin = create_checkin(
            session,
            student_id="S001",
            student_name="张三",
            class_id=seed_refs["一班"],
            session_id=cs.id,
            device_id="device123",
            device_info='{"platform": "test"}'
        )

        assert checkin.student_id == "S001"
        assert checkin.device_id == "device123"
        assert checkin.device_info == '{"platform": "test"}'

    def test_is_device_checked_in_session(self, session: Session, seed_refs):
        """测试检查设备是否已在课堂签到"""
        refs = seed_refs
        cs = start_course_session(session, refs["一班"], teacher_id=1, teacher_name="张老师")

        # 初始状态：设备未签到
        assert is_device_checked_in_session(session, "device123", cs.id) is False

        # 创建设备签到
        create_checkin(
            session, "S001", "张三", refs["一班"], session_id=cs.id,
            device_id="device123"
        )

        # 设备已签到
        assert is_device_checked_in_session(session, "device123", cs.id) is True

        # 其他设备未签到
        assert is_device_checked_in_session(session, "device456", cs.id) is False

    def test_is_device_checked_in_session_empty_device_id(self, session: Session, seed_refs):
        """测试空设备ID检查"""
        refs = seed_refs
        cs = start_course_session(session, refs["一班"], teacher_id=1, teacher_name="张老师")

        # 空设备ID应返回False
        assert is_device_checked_in_session(session, "", cs.id) is False
        assert is_device_checked_in_session(session, None, cs.id) is False


class TestCheckinRecordCRUD:
    """测试分数日志 CRUD"""
