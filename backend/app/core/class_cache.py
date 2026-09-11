"""
班级缓存 - class_id → display_name 单向映射

进程级简单值缓存（只缓存字符串，不缓存 ORM 对象——避免对象跨
session 生命周期的 detached 属性刷新问题，与 term.py 缓存策略一致）。
班级 CRUD 变更后调用 invalidate_class_cache 清除。

裸名解析（name → class_id）已删除：classes 唯一约束为 (name, major, cohort_year)，
裸班级名（如 "1班"）可跨专业/跨届重复，按裸名反查必然歧义。解析一律以 class_id 为锚点。
"""
from typing import Dict, Iterable, Optional

from sqlmodel import Session, col, select

_display_name_by_id: Dict[int, str] = {}


def build_class_display_name(cls) -> str:
    """拼装完整班级展示名（唯一拼装点）：{cohort_year}届{major}{name}"""
    return f"{cls.cohort_year}届{cls.major}{cls.name}"


def get_class_display_name_by_id(session: Session, class_id: Optional[int]) -> Optional[str]:
    """按 ID 解析班级展示名（带缓存；None/不存在返回 None）"""
    if class_id is None:
        return None
    if class_id in _display_name_by_id:
        return _display_name_by_id[class_id]
    from app.models import Class_
    cls = session.get(Class_, class_id)
    if cls is None:
        return None
    _display_name_by_id[cls.id] = build_class_display_name(cls)
    return _display_name_by_id[cls.id]


def get_class_display_names(
    session: Session, class_ids: Iterable[Optional[int]],
) -> Dict[int, str]:
    """批量解析班级展示名（命中缓存跳过；未命中一次查询回填）"""
    ids = {i for i in class_ids if i is not None}
    missing = [i for i in ids if i not in _display_name_by_id]
    if missing:
        from app.models import Class_
        for cls in session.exec(select(Class_).where(col(Class_.id).in_(missing))).all():
            _display_name_by_id[cls.id] = build_class_display_name(cls)
    return {i: _display_name_by_id[i] for i in ids if i in _display_name_by_id}


def invalidate_class_cache() -> None:
    """清除班级缓存（班级创建/改名/删除后调用）"""
    _display_name_by_id.clear()
