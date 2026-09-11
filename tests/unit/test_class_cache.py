"""班级缓存测试（class_id → display_name 单向映射）"""
import app.core.class_cache as class_cache_module
from app.core.class_cache import (
    build_class_display_name,
    get_class_display_name_by_id,
    get_class_display_names,
    invalidate_class_cache,
)


def _seed_classes(session, *specs):
    """specs: (name, major) 元组，cohort_year 固定 "2026" """
    from app.models import Class_

    invalidate_class_cache()
    classes = [Class_(name=name, major=major, cohort_year="2026") for name, major in specs]
    session.add_all(classes)
    session.commit()
    for cls in classes:
        session.refresh(cls)
    return classes


def test_build_class_display_name(session):
    """唯一拼装点：{cohort_year}届{major}{name}"""
    from app.models import Class_

    cls, = _seed_classes(session, ("1班", "软件工程"))
    assert build_class_display_name(cls) == "2026届软件工程1班"


def test_build_class_display_name_empty_major(session):
    cls, = _seed_classes(session, ("1班", ""))
    assert build_class_display_name(cls) == "2026届1班"


def test_get_class_display_name_by_id_resolves(session):
    cls, = _seed_classes(session, ("1班", "软件工程"))
    assert get_class_display_name_by_id(session, cls.id) == "2026届软件工程1班"


def test_get_class_display_name_by_id_empty_major(session):
    cls, = _seed_classes(session, ("1班", ""))
    assert get_class_display_name_by_id(session, cls.id) == "2026届1班"


def test_get_class_display_name_by_id_unknown_returns_none(session):
    invalidate_class_cache()
    assert get_class_display_name_by_id(session, 999999) is None
    assert get_class_display_name_by_id(session, None) is None


def test_get_class_display_names_batch(session):
    cls1, cls2 = _seed_classes(session, ("1班", "软件工程"), ("2班", ""))
    assert get_class_display_names(session, [cls1.id, cls2.id, None]) == {
        cls1.id: "2026届软件工程1班",
        cls2.id: "2026届2班",
    }
    assert get_class_display_names(session, []) == {}


def test_invalidate_class_cache(session):
    """invalidate 后重新查 DB（改名/改专业后返回新 display_name）"""
    from app.models import Class_
    from sqlmodel import update

    cls, = _seed_classes(session, ("1班", "软件工程"))

    assert get_class_display_name_by_id(session, cls.id) == "2026届软件工程1班"

    session.execute(
        update(Class_).where(Class_.id == cls.id).values(name="2班", major="计算机")
    )
    session.commit()

    # 缓存命中旧 display_name；invalidate 后重新读取新值
    assert get_class_display_name_by_id(session, cls.id) == "2026届软件工程1班"
    invalidate_class_cache()
    assert get_class_display_name_by_id(session, cls.id) == "2026届计算机2班"


def test_bare_name_resolution_removed():
    """裸名解析已删除（classes 裸名可重复，按裸名反查必歧义）——硬切换，无兼容层"""
    assert not hasattr(class_cache_module, "get_class_id_by_name")
    assert not hasattr(class_cache_module, "get_class_ids_by_names")
    assert not hasattr(class_cache_module, "get_class_name_by_id")
    assert not hasattr(class_cache_module, "get_class_names")
    assert not hasattr(class_cache_module, "_class_id_by_name")
