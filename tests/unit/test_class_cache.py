"""班级映射缓存测试（class_id ↔ class_name 双向映射）"""
from app.core.class_cache import (
    get_class_id_by_name,
    get_class_ids_by_names,
    get_class_name_by_id,
    get_class_names,
    invalidate_class_cache,
)


def _seed_classes(session, *names):
    from app.models import Class_

    invalidate_class_cache()
    classes = [Class_(name=name, cohort_year="2026") for name in names]
    session.add_all(classes)
    session.commit()
    for cls in classes:
        session.refresh(cls)
    return classes


def test_get_class_id_by_name_resolves(session):
    cls, = _seed_classes(session, "一班")
    assert get_class_id_by_name(session, "一班") == cls.id


def test_get_class_name_by_id_resolves(session):
    cls, = _seed_classes(session, "一班")
    assert get_class_name_by_id(session, cls.id) == "一班"


def test_get_class_name_by_id_unknown_returns_none(session):
    invalidate_class_cache()
    assert get_class_name_by_id(session, 999999) is None
    assert get_class_name_by_id(session, None) is None


def test_get_class_ids_by_names_batch(session):
    cls1, cls2 = _seed_classes(session, "一班", "二班")
    assert set(get_class_ids_by_names(session, ["一班", "二班"])) == {cls1.id, cls2.id}
    # 不存在的名称忽略，重复名称去重
    assert get_class_ids_by_names(session, ["一班", "不存在的班"]) == [cls1.id]
    assert get_class_ids_by_names(session, ["一班", "一班"]) == [cls1.id]
    assert get_class_ids_by_names(session, []) == []


def test_get_class_names_batch(session):
    cls1, cls2 = _seed_classes(session, "一班", "二班")
    assert get_class_names(session, [cls1.id, cls2.id, None]) == {cls1.id: "一班", cls2.id: "二班"}


def test_get_class_id_by_name_unknown_returns_none(session):
    invalidate_class_cache()
    assert get_class_id_by_name(session, "不存在的班") is None


def test_invalidate_class_cache(session):
    """invalidate 后重新查 DB（改名后解析新班）"""
    from app.models import Class_
    from sqlmodel import update

    cls, = _seed_classes(session, "一班")

    assert get_class_id_by_name(session, "一班") == cls.id

    # 改名后缓存仍返回旧映射（DB 已无"一班"）；invalidate 后按新名字解析
    session.execute(update(Class_).where(Class_.id == cls.id).values(name="二班"))
    session.commit()

    assert get_class_id_by_name(session, "一班") == cls.id  # 缓存命中旧映射
    invalidate_class_cache()
    assert get_class_id_by_name(session, "一班") is None    # 失效后查 DB：一班不存在
    assert get_class_id_by_name(session, "二班") == cls.id  # 新名字解析
