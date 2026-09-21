"""db_cleanup 清表语义测试

清表是所有测试隔离的地基，改动它必须钉住三件事：
1. 删干净（含父子表组合，不能因外键顺序报错）
2. identity 序列复位（部分测试硬编码 `teacher_id=1` 等）
3. 空库时是 no-op（不产生多余往返）
"""
from datetime import date

from sqlmodel import Session

from tests.db_cleanup import (
    clear_all_tables, deletion_order, fk_closure, nonempty_tables,
)


def test_deletion_order_puts_children_before_parents():
    """子表必须排在父表之前，否则 DELETE 违反外键"""
    order = deletion_order(["classes", "students"])
    assert order is not None
    assert order.index("students") < order.index("classes")


def test_deletion_order_handles_multiple_levels():
    """多级依赖（孙子 → 子 → 父）也要排对"""
    order = deletion_order(["classes", "students", "checkin_records"])
    assert order is not None
    assert order.index("checkin_records") < order.index("classes")
    assert order.index("students") < order.index("classes")


def test_fk_closure_includes_dependents():
    """外键闭包要包含引用了给定表的表（对齐 CASCADE 的序列复位范围）"""
    closure = fk_closure(["classes"])
    assert "classes" in closure
    assert "students" in closure, "students 引用了 classes，应在闭包内"
    assert len(closure) > 1


def test_clear_all_tables_noop_on_empty_db(engine):
    """空库时是 no-op"""
    clear_all_tables(engine)
    with Session(engine) as s:
        assert nonempty_tables(s) == []


def test_clear_all_tables_cleans_parent_and_child(engine, session):
    """父子表都有数据时一并清掉，且不因外键顺序报错"""
    from app.models import Class_, Semester, Student

    cls = Class_(name="清理测试班", cohort_year="2099")
    session.add(cls)
    session.commit()
    session.refresh(cls)
    session.add(Semester(label="2099-cleanup", start_date=date(2099, 1, 1),
                         total_weeks=1, is_current=False))
    session.add(Student(student_id="CLN001", name="清理学生", class_id=cls.id))
    session.commit()

    with Session(engine) as s:
        assert set(nonempty_tables(s)) >= {"classes", "students", "semesters"}

    clear_all_tables(engine)

    with Session(engine) as s:
        assert nonempty_tables(s) == []


def test_clear_all_tables_resets_identity(engine, session):
    """identity 复位：清表后新插入的 id 从 1 开始（对齐 RESTART IDENTITY）"""
    from app.models import Class_

    session.add(Class_(name="复位前", cohort_year="2099"))
    session.add(Class_(name="复位前2", cohort_year="2099"))
    session.commit()

    clear_all_tables(engine)

    with Session(engine) as s:
        fresh = Class_(name="复位后", cohort_year="2099")
        s.add(fresh)
        s.commit()
        s.refresh(fresh)
        assert fresh.id == 1, f"identity 未复位，新记录 id={fresh.id}"
