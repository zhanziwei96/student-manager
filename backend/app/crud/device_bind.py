"""
设备绑定 CRUD 操作
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.models.device_bind import DeviceBind, DeviceBindCreate


def create_device_bind(session: Session, bind_data: DeviceBindCreate) -> DeviceBind:
    """创建设备绑定记录"""
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    bind = DeviceBind(
        session_id=bind_data.session_id,
        student_id=bind_data.student_id,
        device_id=bind_data.device_id,
        created_at=now,
        updated_at=now,
    )
    session.add(bind)
    session.commit()
    session.refresh(bind)
    return bind


def get_device_bind(session: Session, session_id: int, student_id: str) -> DeviceBind | None:
    """按 session_id 和 student_id 获取设备绑定记录"""
    query = select(DeviceBind).where(
        DeviceBind.session_id == session_id,
        DeviceBind.student_id == student_id,
    )
    return session.exec(query).first()


def update_device_bind(session: Session, session_id: int, student_id: str, new_device_id: str) -> DeviceBind | None:
    """更新设备绑定记录的设备ID"""
    bind = get_device_bind(session, session_id, student_id)
    if bind is None:
        return None
    bind.device_id = new_device_id
    bind.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
    session.add(bind)
    session.commit()
    session.refresh(bind)
    return bind


def delete_device_bind(session: Session, session_id: int, student_id: str) -> bool:
    """删除设备绑定记录"""
    bind = get_device_bind(session, session_id, student_id)
    if bind is None:
        return False
    session.delete(bind)
    session.commit()
    return True
