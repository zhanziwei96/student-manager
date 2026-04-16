"""
设备绑定 CRUD 操作
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
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


def upsert_device_bind(session: Session, session_id: int, student_id: str, device_id: str) -> DeviceBind:
    """在同一事务内创建或更新设备绑定记录，防止并发竞态"""
    bind = get_device_bind(session, session_id, student_id)
    if bind:
        if bind.device_id != device_id:
            bind.device_id = device_id
            bind.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            session.add(bind)
            session.commit()
            session.refresh(bind)
        return bind

    new_bind = DeviceBind(
        session_id=session_id,
        student_id=student_id,
        device_id=device_id,
        created_at=datetime.now(ZoneInfo("Asia/Shanghai")),
        updated_at=datetime.now(ZoneInfo("Asia/Shanghai")),
    )
    session.add(new_bind)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        # 并发时另一请求已插入，重新查询并更新
        bind = get_device_bind(session, session_id, student_id)
        if bind and bind.device_id != device_id:
            bind.device_id = device_id
            bind.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
            session.add(bind)
            session.commit()
            session.refresh(bind)
        elif bind:
            new_bind = bind
    session.refresh(new_bind)
    return new_bind
