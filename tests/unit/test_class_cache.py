"""班级映射缓存测试"""
from app.core.class_cache import (
    get_class_by_id,
    get_class_id_by_name,
    invalidate_class_cache,
)


def test_get_class_id_by_name_resolves(session):
    from app.models import Class_, Cohort

    invalidate_class_cache()
    session.add(Cohort(year="2026"))
    cls = Class_(name="一班", cohort_year="2026")
    session.add(cls)
    session.commit()

    assert get_class_id_by_name(session, "一班") == cls.id


def test_get_class_by_id_resolves(session):
    from app.models import Class_, Cohort

    invalidate_class_cache()
    session.add(Cohort(year="2026"))
    cls = Class_(name="一班", cohort_year="2026")
    session.add(cls)
    session.commit()

    result = get_class_by_id(session, cls.id)
    assert result is not None
    assert result.name == "一班"


def test_get_class_id_by_name_unknown_returns_none(session):
    invalidate_class_cache()
    assert get_class_id_by_name(session, "不存在的班") is None


def test_invalidate_class_cache(session):
    """invalidate 后重新查 DB（改名后解析新班）"""
    from app.models import Class_, Cohort
    from sqlmodel import update

    invalidate_class_cache()
    session.add(Cohort(year="2026"))
    cls = Class_(name="一班", cohort_year="2026")
    session.add(cls)
    session.commit()

    assert get_class_id_by_name(session, "一班") == cls.id

    # 改名后缓存仍返回旧映射（DB 已无"一班"）；invalidate 后按新名字解析
    session.execute(update(Class_).where(Class_.id == cls.id).values(name="二班"))
    session.commit()

    assert get_class_id_by_name(session, "一班") == cls.id  # 缓存命中旧映射
    invalidate_class_cache()
    assert get_class_id_by_name(session, "一班") is None    # 失效后查 DB：一班不存在
    assert get_class_id_by_name(session, "二班") == cls.id  # 新名字解析
