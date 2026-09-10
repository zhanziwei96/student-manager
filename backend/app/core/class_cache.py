"""
班级映射缓存 - class_id ↔ class_name 双向映射（方案 4.2）

进程级简单值缓存（只缓存字符串/整数，不缓存 ORM 对象——避免对象跨
session 生命周期的 detached 属性刷新问题，与 term.py 缓存策略一致）。
班级 CRUD 变更后调用 invalidate_class_cache 清除。
"""
from typing import Dict, Iterable, List, Optional

from sqlmodel import Session, col, select

_class_name_by_id: Dict[int, str] = {}
_class_id_by_name: Dict[str, int] = {}


def get_class_name_by_id(session: Session, class_id: Optional[int]) -> Optional[str]:
    """按 ID 解析班级名（带缓存；None/不存在返回 None）"""
    if class_id is None:
        return None
    if class_id in _class_name_by_id:
        return _class_name_by_id[class_id]
    from app.models import Class_
    cls = session.get(Class_, class_id)
    if cls is None:
        return None
    _class_name_by_id[cls.id] = cls.name
    _class_id_by_name[cls.name] = cls.id
    return cls.name


def get_class_names(
    session: Session, class_ids: Iterable[Optional[int]],
) -> Dict[int, str]:
    """批量解析班级名（命中缓存跳过；未命中一次查询回填）"""
    ids = {i for i in class_ids if i is not None}
    missing = [i for i in ids if i not in _class_name_by_id]
    if missing:
        from app.models import Class_
        for cls in session.exec(select(Class_).where(col(Class_.id).in_(missing))).all():
            _class_name_by_id[cls.id] = cls.name
            _class_id_by_name[cls.name] = cls.id
    return {i: _class_name_by_id[i] for i in ids if i in _class_name_by_id}


def get_class_id_by_name(session: Session, class_name: Optional[str]) -> Optional[int]:
    """按班级名解析 class_id（不存在返回 None）"""
    if not class_name:
        return None
    if class_name in _class_id_by_name:
        return _class_id_by_name[class_name]
    from app.models import Class_
    cls = session.exec(select(Class_).where(Class_.name == class_name)).first()
    if cls is not None:
        _class_name_by_id[cls.id] = cls.name
        _class_id_by_name[cls.name] = cls.id
        return cls.id
    return None


def get_class_ids_by_names(
    session: Session, class_names: Iterable[str],
) -> List[int]:
    """批量按班级名解析 class_id（命中缓存跳过；未命中的一次查询回填；不存在的名称忽略）"""
    names = {n for n in class_names if n}
    missing = [n for n in names if n not in _class_id_by_name]
    if missing:
        from app.models import Class_
        for cls in session.exec(select(Class_).where(col(Class_.name).in_(missing))).all():
            _class_name_by_id[cls.id] = cls.name
            _class_id_by_name[cls.name] = cls.id
    return [i for i in (_class_id_by_name.get(n) for n in names) if i is not None]


def invalidate_class_cache() -> None:
    """清除班级映射缓存（班级创建/改名/删除后调用）"""
    _class_name_by_id.clear()
    _class_id_by_name.clear()
