"""按需清表 —— 测试隔离的唯一实现（根 conftest 与集成 conftest 共用）

## 为什么不用 `TRUNCATE ... CASCADE`

PostgreSQL **不允许** TRUNCATE 一张「被外键引用」的表，**哪怕引用者是空表**——
所以只要 `seed_refs` 写了 `classes` / `semesters`，就必须带 `CASCADE`，
而 `CASCADE` 会遍历整张外键图，实测截断 **27/31 张表**。

在 WSL 的文件系统上每张表的 TRUNCATE 约 26ms（建新 relfilenode），合计 **~700ms/用例**，
而多数用例只写 2–5 张表。对照实验（同一个真实清表函数）：

| 方案 | 耗时 |
|---|---|
| `TRUNCATE <非空表> RESTART IDENTITY CASCADE` | 717 ms |
| 自己算 FK 闭包 + 不带 CASCADE | 710 ms（一样慢 → 瓶颈是表数量，不是遍历图） |
| **只 DELETE 非空表（逆依赖序）+ 序列复位** | **37 ms** |

`DELETE` 没有那个限制——引用者是空表就不会违反外键，所以能只碰 2 张表而不是 27 张。

## 语义对齐

`TRUNCATE ... RESTART IDENTITY CASCADE` 会复位**被截断的所有表**（含 CASCADE 带进来的从属表）
的 identity 序列。这里用同样的范围：**非空表 ∪ 其外键闭包**，保证「id 从 1 开始」的
既有假设（部分测试硬编码 `teacher_id=1`）不被破坏。

## 兜底

若外键图存在环（Kahn 拓扑排序覆盖不全），回退到 `TRUNCATE ... CASCADE`——
正确但慢，不会因此出错。
"""
from typing import Dict, Iterable, List, Set

from sqlalchemy import text
from sqlmodel import Session, SQLModel

# 必须在模块级导入全部模型：SQLModel.metadata 只登记**已导入**的模型，
# 元数据不全 → 非空表探测会漏表（脏数据残留）、外键图也会算错。
# 根 conftest 的 `import app.models` 位于 engine 夹具内部，用不到该夹具的测试拿不到完整元数据。
import app.models  # noqa: F401

# parent -> children（谁引用了它）；纯元数据推导，进程内缓存一次
_CHILDREN: Dict[str, Set[str]] = {}


def _children_map() -> Dict[str, Set[str]]:
    if _CHILDREN:
        return _CHILDREN
    tables = SQLModel.metadata.tables
    children: Dict[str, Set[str]] = {name: set() for name in tables}
    for name, table in tables.items():
        for fk in table.foreign_keys:
            parent = fk.column.table.name
            if parent != name and parent in children:
                children[parent].add(name)
    _CHILDREN.update(children)
    return _CHILDREN


def nonempty_tables(session: Session) -> List[str]:
    """一次往返探出非空表

    必须用 EXISTS **实测**而非 `pg_stat` 估算——统计有滞后，会造成跨用例脏数据残留。
    """
    tables = list(SQLModel.metadata.tables.keys())
    probe = " UNION ALL ".join(
        f"SELECT '{t}' AS t WHERE EXISTS (SELECT 1 FROM {t})" for t in tables)
    return [row[0] for row in session.execute(text(probe)).all()]


def fk_closure(names: Iterable[str]) -> Set[str]:
    """把「引用了这些表」的表递归加进来 —— 即 CASCADE 原先会一并复位序列的范围"""
    children = _children_map()
    out: Set[str] = set(names)
    stack = list(out)
    while stack:
        for child in children.get(stack.pop(), ()):
            if child not in out:
                out.add(child)
                stack.append(child)
    return out


def deletion_order(names: Iterable[str]) -> List[str]:
    """子表先删的拓扑序（Kahn）。存在环时返回 None，由调用方兜底。

    方向：一张表只有在「待删集合内已无子表引用它」时才可删 →
    叶子（无人引用）先删，父表最后删。
    """
    names = set(names)
    children = _children_map()

    # 每张表去重后的父表集合（多列指向同一父表时只算一次）
    parents_of: Dict[str, Set[str]] = {}
    for n in names:
        parents_of[n] = {
            fk.column.table.name for fk in SQLModel.metadata.tables[n].foreign_keys
            if fk.column.table.name in names and fk.column.table.name != n
        }

    # pending[n] = 待删集合内还有多少张子表引用 n
    pending: Dict[str, int] = {n: 0 for n in names}
    for n, parents in parents_of.items():
        for p in parents:
            pending[p] += 1

    queue = sorted(n for n in names if pending[n] == 0)
    order: List[str] = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        # current 被删后，它的每张父表各少一张子表
        for parent in sorted(parents_of[current]):
            pending[parent] -= 1
            if pending[parent] == 0:
                queue.append(parent)

    return order if len(order) == len(names) else None  # type: ignore[return-value]


def _reset_sequences(session: Session, tables: Iterable[str]) -> None:
    """把 identity 序列复位到 1（等价于 TRUNCATE ... RESTART IDENTITY）

    只两次往返：一次查出这些表拥有的序列，一次批量 setval。

    ⚠️ 别改回「逐列 pg_get_serial_sequence + 逐条 setval」：闭包 27 张表共 209 列，
    那是 400+ 次往返，实测 384ms（整个清表才该是这个量级），而批量版只要几毫秒。
    """
    names = sorted(set(tables))
    if not names:
        return

    sequences = [row[0] for row in session.execute(text("""
        SELECT seq.relname
        FROM pg_class seq
        JOIN pg_depend dep ON dep.objid = seq.oid AND dep.deptype IN ('a', 'i')
        JOIN pg_class tbl ON tbl.oid = dep.refobjid
        WHERE seq.relkind = 'S' AND tbl.relname = ANY(:names)
    """), {"names": names}).all()]

    if sequences:
        # CAST 而非 :x::type —— SQLAlchemy 的 text() 会把 :: 误当绑定参数
        session.execute(text(
            "SELECT setval(CAST(s AS regclass), 1, false)"
            " FROM unnest(CAST(:seqs AS text[])) AS s"
        ), {"seqs": sequences})


def clear_all_tables(engine) -> None:
    """清空测试库脏表（只清非空表；其余表本就为空）"""
    with Session(engine) as session:
        names = nonempty_tables(session)
        if not names:
            return

        order = deletion_order(names)
        if order is None:
            # 外键图有环：宁可慢也不能删错
            session.execute(text(
                "TRUNCATE %s RESTART IDENTITY CASCADE" % ", ".join(names)))
            session.commit()
            return

        for name in order:
            session.execute(text(f"DELETE FROM {name}"))

        # 复位范围对齐 TRUNCATE ... RESTART IDENTITY CASCADE（含从属表）
        _reset_sequences(session, fk_closure(names))
        session.commit()
