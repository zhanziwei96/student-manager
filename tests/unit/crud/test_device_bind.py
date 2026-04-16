"""
DeviceBind CRUD 单元测试
"""
import pytest
from sqlmodel import Session
from app.crud.device_bind import (
    create_device_bind,
    get_device_bind,
    update_device_bind,
    delete_device_bind,
)
from app.models.device_bind import DeviceBindCreate
from app.crud.course_session import start_course_session


class TestDeviceBindCRUD:
    """测试设备绑定 CRUD"""

    def test_create_device_bind(self, session: Session):
        """测试创建设备绑定"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        bind_data = DeviceBindCreate(
            session_id=cs.id,
            student_id="S001",
            device_id="device_abc_123",
        )
        bind = create_device_bind(session, bind_data)

        assert bind.session_id == cs.id
        assert bind.student_id == "S001"
        assert bind.device_id == "device_abc_123"
        assert bind.id is not None
        assert bind.created_at is not None
        assert bind.updated_at is not None

    def test_get_device_bind_existing(self, session: Session):
        """测试获取已存在的设备绑定"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        bind_data = DeviceBindCreate(
            session_id=cs.id,
            student_id="S001",
            device_id="device_abc_123",
        )
        created = create_device_bind(session, bind_data)

        found = get_device_bind(session, cs.id, "S001")
        assert found is not None
        assert found.id == created.id
        assert found.device_id == "device_abc_123"

    def test_get_device_bind_not_found(self, session: Session):
        """测试获取不存在的设备绑定"""
        result = get_device_bind(session, 99999, "NOBODY")
        assert result is None

    def test_update_device_bind(self, session: Session):
        """测试更新设备绑定"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        bind_data = DeviceBindCreate(
            session_id=cs.id,
            student_id="S001",
            device_id="device_old",
        )
        create_device_bind(session, bind_data)

        updated = update_device_bind(session, cs.id, "S001", "device_new")
        assert updated is not None
        assert updated.device_id == "device_new"
        assert updated.student_id == "S001"
        assert updated.session_id == cs.id

        # 确认更新已持久化
        found = get_device_bind(session, cs.id, "S001")
        assert found is not None
        assert found.device_id == "device_new"

    def test_delete_device_bind(self, session: Session):
        """测试删除设备绑定"""
        cs = start_course_session(session, "软件1班", teacher_id=1, teacher_name="张老师")

        bind_data = DeviceBindCreate(
            session_id=cs.id,
            student_id="S001",
            device_id="device_to_delete",
        )
        create_device_bind(session, bind_data)

        assert get_device_bind(session, cs.id, "S001") is not None

        deleted = delete_device_bind(session, cs.id, "S001")
        assert deleted is True

        assert get_device_bind(session, cs.id, "S001") is None
