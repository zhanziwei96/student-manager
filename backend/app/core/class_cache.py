"""
班级映射缓存 - class_id ↔ class_name 双向映射（方案 4.2）

进程级缓存，班级 CRUD 变更后调用 invalidate_class_cache 清除。
"""
from typing import Dict, Optional

from sqlmodel import Session, select


_class_cache: Dict[int, object] = {}
_class_name_to_id_cache: Dict[str, int] = {}


def get_class_by_id(session: Session, class_id: int):
    """按 ID 查班级（带进程级缓存）"""
    cls = _class_cache.get(class_id)
    if cls is not None:
        return cls
    from app.models import Class_
    cls = session.get(Class_, class_id)
    if cls is not None:
        _class_cache[class_id] = cls
        _class_name_to_id_cache[cls.name] = cls.id
    return cls


def get_class_id_by_name(session: Session, class_name: str) -> Optional[int]:
    """按班级名解析 class_id（未分班/不存在返回 None）"""
    if class_name in _class_name_to_id_cache:
        return _class_name_to_id_cache[class_name]
    from app.models import Class_
    cls = session.exec(select(Class_).where(Class_.name == class_name)).first()
    if cls is not None:
        _class_cache[cls.id] = cls
        _class_name_to_id_cache[cls.name] = cls.id
        return cls.id
    return None


def invalidate_class_cache() -> None:
    """清除班级映射缓存（班级创建/改名/删除后调用）"""
    _class_cache.clear()
    _class_name_to_id_cache.clear()
