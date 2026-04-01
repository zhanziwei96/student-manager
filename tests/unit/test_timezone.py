"""
测试时区处理 - 确保所有模型使用统一时区
"""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo


class TestTimezone:
    """测试时区统一处理"""

    def test_timezone_module_import(self):
        """测试时区模块可导入"""
        from app.core.timezone import get_now, APP_TIMEZONE

        assert APP_TIMEZONE is not None
        assert str(APP_TIMEZONE) == "Asia/Shanghai"

    def test_get_now_returns_shanghai_time(self):
        """测试 get_now 返回上海时区时间"""
        from app.core.timezone import get_now, APP_TIMEZONE

        now = get_now()
        assert now.tzinfo is not None
        assert now.tzinfo == APP_TIMEZONE

    def test_student_model_created_at(self):
        """测试学生模型创建时间使用正确时区"""
        from sqlmodel import Session
        from app.models import Student
        from app.core.timezone import get_now, APP_TIMEZONE

        student = Student(
            student_id="TZ001",
            name="时区测试",
            class_name="测试班级",
            created_at=get_now()
        )

        assert student.created_at.tzinfo is not None
        assert student.created_at.tzinfo == APP_TIMEZONE

    def test_checkin_record_default_timezone(self):
        """测试签到记录默认时间使用正确时区"""
        from app.models import CheckinRecord
        from app.core.timezone import APP_TIMEZONE

        record = CheckinRecord(
            student_id="TZ001",
            checkin_type="self"
        )

        # 检查是否自动设置了带时区的时间
        assert record.checkin_time is not None
        assert record.checkin_time.tzinfo is not None
        assert record.checkin_time.tzinfo == APP_TIMEZONE

    def test_user_model_created_at(self):
        """测试用户模型创建时间使用正确时区"""
        from app.models import User
        from app.core.timezone import get_now, APP_TIMEZONE

        user = User(
            username="tztest",
            name="时区测试",
            password_hash="$2b$12$test",
            created_at=get_now()
        )

        assert user.created_at.tzinfo is not None
        assert user.created_at.tzinfo == APP_TIMEZONE

    def test_audit_log_created_at(self):
        """测试审计日志创建时间使用正确时区"""
        from app.models import AuditLog
        from app.core.timezone import get_now, APP_TIMEZONE

        log = AuditLog(
            action="test",
            created_at=get_now()
        )

        assert log.created_at.tzinfo is not None
        assert log.created_at.tzinfo == APP_TIMEZONE

    def test_security_functions_use_correct_timezone(self):
        """测试安全函数使用正确时区"""
        from datetime import timedelta
        from app.core.security import calculate_lockout_time, is_account_locked
        from app.core.timezone import get_now, APP_TIMEZONE

        # 测试锁定时间计算
        lock_time = calculate_lockout_time(10)  # 10次失败
        assert lock_time is not None
        assert lock_time.tzinfo == APP_TIMEZONE

        # 测试锁定状态检查
        future_time = get_now() + timedelta(minutes=30)
        assert is_account_locked(future_time) is True

        past_time = get_now() - timedelta(minutes=30)
        assert is_account_locked(past_time) is False

    def test_convert_to_app_timezone(self):
        """测试时间转换函数"""
        from app.core.timezone import convert_to_app_timezone, APP_TIMEZONE

        # 测试无时区时间转换
        naive_time = datetime(2024, 1, 1, 12, 0, 0)
        converted = convert_to_app_timezone(naive_time)
        assert converted.tzinfo == APP_TIMEZONE

        # 测试有时区时间转换
        utc_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        converted = convert_to_app_timezone(utc_time)
        assert converted.tzinfo == APP_TIMEZONE
        # UTC 转上海时区，时间应该 +8 小时
        assert converted.hour == 20

    def test_format_datetime(self):
        """测试时间格式化函数"""
        from app.core.timezone import format_datetime, APP_TIMEZONE

        dt = datetime(2024, 1, 15, 14, 30, 0, tzinfo=APP_TIMEZONE)
        formatted = format_datetime(dt)
        assert formatted == "2024-01-15 14:30:00"

        # 测试无时区时间格式化
        naive_dt = datetime(2024, 1, 15, 14, 30, 0)
        formatted = format_datetime(naive_dt)
        assert formatted == "2024-01-15 14:30:00"
