# 座位系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **状态：全部任务完成于 2026-09-23（feat/seat-system 分支）**

**Goal:** 学生在教室座位图上点座「坐下」+ 输验证码完成签到；教师端实时座位图（含故障标记与临时调座）。

**Architecture:** 后端新增教室/座位/座位分配/会话覆盖四张表，签到接口扩展 `seat_id`；前端新增 `src/components/seats/` 组件族（深色局部作用域），学生签到页按「该课堂教室是否有座位图」分流。无座位图的教室走原有纯验证码流程，完全不变。

**Tech Stack:** FastAPI + SQLModel + Alembic（PostgreSQL）；Vue 3.5 + TS + TanStack Query + Tailwind v4（座位图部分用组件内 scoped 自定义属性，不动全局令牌）。

**Spec:** `docs/superpowers/specs/2026-09-18-seat-system-design.md`

**分支:** `feat/seat-system`（从 main 切出；本计划文档就在这个分支上）

## Global Constraints

- 迁移 `down_revision` 必须是 `"20260921_fix_lost_found_actor_fk"`（当前链 head，**不是** 20260916）
- 迁移必须幂等：建表用 `to_regclass` 守卫、加列用 `information_schema.columns` 守卫（模板：`backend/alembic/versions/20260916_add_visibility_classes.py`）
- 学生主键是 `students.student_id`（**str 学号**）；JWT `sub` 学生=学号 str、教师=users.id 的 str，比较前必须 `int()`/`str()` 转换
- 认证走 HttpOnly Cookie（`get_current_user`，无 Authorization header）；权限复用 `require_admin_or_teacher` / `verify_teacher_class_access`
- CRUD 层 = 模块级裸函数，第一参数 `session: Session`，自己 commit/refresh，`IntegrityError` → rollback + 业务异常
- 座位编号规则：`P{row}{col}`（row/col 从 1 起）——如 P23 = 第 2 排第 3 列
- 状态语义：座位四态 `empty | assigned | occupied | mine`；故障座位**不可选**（任何角色）
- 前端：API 一律走 `src/lib/api.ts` 的 ofetch helper（已自动 unwrap `ApiResponse.data`）；新增类型放 `src/types/seats.ts` 并从 `src/types/index.ts` 导出
- 前端测试：文件头 `/** @vitest-environment jsdom */`，composable 用 `vi.mock` 整体替换，UI 组件用 inline template stub（参照 `frontend-v3/test/views/StudentCheckin.spec.ts`）
- 后端测试：集成测试用 `tests/integration/conftest.py` 的 `client`/`test_engine`/`seed_refs`，登录态用 `client.post("/api/v1/login", ...)` 拿 cookie
- 不动全局设计系统；深色主题只活在座位图组件的 scoped 样式里
- 每任务结束跑对应测试并 commit；完成后跑一次全量（后端 `pytest tests/ -q`，前端 `pnpm test:run`）

---

### Task 1: 数据迁移——四张新表 + checkin_records.seat_id

**Files:**
- Create: `backend/alembic/versions/20260922_add_seat_system.py`
- Test: `tests/unit/test_migration_seat_system.py`

**Interfaces:**
- Consumes: 迁移链 head `20260921_fix_lost_found_actor_fk`
- Produces: 表 `classrooms` / `seats` / `seat_assignments` / `seat_session_overrides`；列 `checkin_records.seat_id`

**设计说明（相对 spec 的两处补全）：**
1. `seat_assignments` 增加冗余列 `classroom_id`——spec 的唯一约束 `(student_id, semester_id, classroom)` 必须能落在单行上，而 seat→classroom 是 join，不加冗余列无法用数据库约束表达。
2. 新增 `seat_session_overrides`（spec §6.2 教师调座"这节课有效"但学生可能还没签到，`checkin_records.seat_id` 记的是"实际坐哪"，无法表达"这节课该坐哪"）。下课即失效 = 记录按 `session_id` 生命周期隔离，无需清理任务。

- [ ] **Step 1: 写失败的迁移测试**

```python
# tests/unit/test_migration_seat_system.py
"""座位系统迁移测试：建表幂等 + 列幂等。"""
import pytest
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
import os


def _alembic_cfg(db_url: str) -> Config:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cfg = Config(os.path.join(root, "backend", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(root, "backend", "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


@pytest.fixture()
def scratch_db():
    """独占迁移测试库分片（PYTEST_XDIST_WORKER 决定库名）。"""
    worker = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
    suffix = worker[2:] if worker.startswith("gw") else "0"
    url = f"postgresql+psycopg2://classhub:classhub_dev@localhost:5432/classhub_migration_test_{suffix}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
    yield url
    engine.dispose()


def _table_exists(url, table):
    engine = create_engine(url)
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT to_regclass(:t) IS NOT NULL"), {"t": f"public.{table}"}
        ).scalar()


def _column_exists(url, table, column):
    engine = create_engine(url)
    with engine.connect() as conn:
        return conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name=:t AND column_name=:c)"
            ),
            {"t": table, "c": column},
        ).scalar()


class TestSeatSystemMigration:
    def test_upgrade_creates_seat_tables(self, scratch_db):
        command.upgrade(_alembic_cfg(scratch_db), "head")
        for table in ("classrooms", "seats", "seat_assignments", "seat_session_overrides"):
            assert _table_exists(scratch_db, table), f"缺表 {table}"
        assert _column_exists(scratch_db, "checkin_records", "seat_id")

    def test_upgrade_is_idempotent(self, scratch_db):
        command.upgrade(_alembic_cfg(scratch_db), "head")
        command.upgrade(_alembic_cfg(scratch_db), "head")  # 第二次不得报错
```

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage python -m pytest tests/unit/test_migration_seat_system.py -v -n 0`
Expected: FAIL（`20260922_add_seat_system` 不存在，upgrade 找不到 revision）

- [ ] **Step 3: 写迁移**

```python
# backend/alembic/versions/20260922_add_seat_system.py
"""add seat system: classrooms / seats / seat_assignments / seat_session_overrides + checkin_records.seat_id

Revision ID: 20260922_add_seat_system
Revises: 20260921_fix_lost_found_actor_fk
"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_add_seat_system"
down_revision: Union[str, Sequence[str], None] = "20260921_fix_lost_found_actor_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, table: str) -> bool:
    return bind.execute(
        sa.text("SELECT to_regclass(:t) IS NOT NULL"), {"t": f"public.{table}"}
    ).scalar()


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "classrooms"):
        op.create_table(
            "classrooms",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(50), nullable=False),
            sa.Column("rows", sa.Integer(), nullable=False),
            sa.Column("cols", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
            sa.UniqueConstraint("name", name="uq_classrooms_name"),
        )

    if not _table_exists(bind, "seats"):
        op.create_table(
            "seats",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("classroom_id", sa.Integer(), nullable=False),
            sa.Column("seat_no", sa.String(10), nullable=False),
            sa.Column("row", sa.Integer(), nullable=False),
            sa.Column("col", sa.Integer(), nullable=False),
            sa.Column("is_broken", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("classroom_id", "seat_no", name="uix_seat_no_per_classroom"),
            sa.UniqueConstraint("classroom_id", "row", "col", name="uix_seat_pos_per_classroom"),
        )
        op.create_index("ix_seats_classroom_id", "seats", ["classroom_id"])

    if not _table_exists(bind, "seat_assignments"):
        op.create_table(
            "seat_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("seat_id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.String(20), nullable=False),
            sa.Column("classroom_id", sa.Integer(), nullable=False),  # 冗余：唯一约束需要
            sa.Column("semester_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["student_id"], ["students.student_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["semester_id"], ["semesters.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("seat_id", "semester_id", name="uix_seat_semester"),
            sa.UniqueConstraint(
                "student_id", "semester_id", "classroom_id",
                name="uix_student_semester_classroom",
            ),
        )
        op.create_index("ix_seat_assignments_student", "seat_assignments",
                        ["student_id", "semester_id"])

    if not _table_exists(bind, "seat_session_overrides"):
        op.create_table(
            "seat_session_overrides",
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("student_id", sa.String(20), nullable=False),
            sa.Column("seat_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["session_id"], ["course_sessions.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["student_id"], ["students.student_id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("session_id", "student_id"),
        )

    # checkin_records.seat_id（可空：旧数据/无座位图课堂）
    col_exists = bind.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name='checkin_records' AND column_name='seat_id')"
    )).scalar()
    if not col_exists:
        op.add_column("checkin_records", sa.Column("seat_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_checkin_records_seat_id", "checkin_records", "seats",
            ["seat_id"], ["id"], ondelete="SET NULL",
        )


def downgrade() -> None:
    raise NotImplementedError("座位系统迁移不支持 downgrade（与 20260916 一致）")
```

- [ ] **Step 4: 运行确认通过**

Run: `conda run -n student-manage python -m pytest tests/unit/test_migration_seat_system.py -v -n 0`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/20260922_add_seat_system.py tests/unit/test_migration_seat_system.py
git commit -m "feat(seat): 迁移——classrooms/seats/seat_assignments/seat_session_overrides + checkin_records.seat_id"
```

---

### Task 2: 模型层 + 座位编号纯函数

**Files:**
- Create: `backend/app/models/seat.py`
- Create: `backend/app/core/seat_layout.py`
- Modify: `backend/app/models/checkin.py`（加 `seat_id` 字段）
- Modify: `backend/app/models/__init__.py`（导出新模型）
- Test: `tests/unit/test_seat_layout.py`

**Interfaces:**
- Consumes: Task 1 的表结构
- Produces: `Classroom` / `Seat` / `SeatAssignment` / `SeatSessionOverride` 模型；`generate_seat_no(row: int, col: int) -> str`；`build_seat_rows(classroom_id: int, rows: int, cols: int) -> list[dict]`（每项 `{seat_no, row, col}`）；`CheckinRecord.seat_id`

- [ ] **Step 1: 写失败的单测（纯函数）**

```python
# tests/unit/test_seat_layout.py
from app.core.seat_layout import build_seat_rows, generate_seat_no


class TestGenerateSeatNo:
    def test_format(self):
        assert generate_seat_no(2, 3) == "P23"

    def test_row_col_start_at_1(self):
        assert generate_seat_no(1, 1) == "P11"

    def test_two_digit(self):
        assert generate_seat_no(10, 12) == "P1012"


class TestBuildSeatRows:
    def test_count(self):
        seats = build_seat_rows(classroom_id=1, rows=4, cols=6)
        assert len(seats) == 24

    def test_first_and_last(self):
        seats = build_seat_rows(classroom_id=1, rows=2, cols=3)
        assert seats[0] == {"seat_no": "P11", "row": 1, "col": 1}
        assert seats[-1] == {"seat_no": "P23", "row": 2, "col": 3}

    def test_unique_positions(self):
        seats = build_seat_rows(classroom_id=1, rows=5, cols=5)
        assert len({(s["row"], s["col"]) for s in seats}) == 25
```

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage python -m pytest tests/unit/test_seat_layout.py -v -n 0`
Expected: FAIL（`app.core.seat_layout` 不存在）

- [ ] **Step 3: 实现**

```python
# backend/app/core/seat_layout.py
"""座位编号与布局生成（纯函数，不碰数据库）。"""


def generate_seat_no(row: int, col: int) -> str:
    """P{row}{col}：P23 = 第 2 排第 3 列。row/col 均从 1 起。"""
    return f"P{row}{col}"


def build_seat_rows(classroom_id: int, rows: int, cols: int) -> list[dict]:
    """按 rows×cols 生成整间教室的座位行数据（row 主序）。"""
    return [
        {
            "classroom_id": classroom_id,
            "seat_no": generate_seat_no(r, c),
            "row": r,
            "col": c,
        }
        for r in range(1, rows + 1)
        for c in range(1, cols + 1)
    ]
```

```python
# backend/app/models/seat.py
"""座位系统模型：教室 / 座位 / 座位分配 / 会话级临时调座。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Classroom(SQLModel, table=True):
    __tablename__ = "classrooms"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    rows: int = Field(ge=1, le=50)
    cols: int = Field(ge=1, le=50)
    status: str = Field(default="active", max_length=20)  # active | archived
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Seat(SQLModel, table=True):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("classroom_id", "seat_no", name="uix_seat_no_per_classroom"),
        UniqueConstraint("classroom_id", "row", "col", name="uix_seat_pos_per_classroom"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    classroom_id: int = Field(foreign_key="classrooms.id", index=True)
    seat_no: str = Field(max_length=10)
    row: int = Field(ge=1)
    col: int = Field(ge=1)
    is_broken: bool = Field(default=False)


class SeatAssignment(SQLModel, table=True):
    """固定座位分配（每学期一份）。classroom_id 冗余自 seat.classroom_id，唯一约束需要。"""

    __tablename__ = "seat_assignments"
    __table_args__ = (
        UniqueConstraint("seat_id", "semester_id", name="uix_seat_semester"),
        UniqueConstraint("student_id", "semester_id", "classroom_id",
                         name="uix_student_semester_classroom"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    seat_id: int = Field(foreign_key="seats.id")
    student_id: str = Field(foreign_key="students.student_id", max_length=20, index=True)
    classroom_id: int = Field(foreign_key="classrooms.id")
    semester_id: int = Field(foreign_key="semesters.id")
    created_at: Optional[datetime] = None


class SeatSessionOverride(SQLModel, table=True):
    """教师临时调座：这节课有效，随 session 生命周期失效，不动固定分配。"""

    __tablename__ = "seat_session_overrides"

    session_id: int = Field(foreign_key="course_sessions.id", primary_key=True)
    student_id: str = Field(foreign_key="students.student_id", max_length=20, primary_key=True)
    seat_id: int = Field(foreign_key="seats.id")
    created_at: Optional[datetime] = None
```

`backend/app/models/checkin.py`：在 `CheckinRecord` 的 `device_bound` 字段后加：

```python
    seat_id: Optional[int] = Field(default=None, foreign_key="seats.id")  # 本次实际坐的座位
```

`backend/app/models/__init__.py`：追加导入（照现有模式）：

```python
from app.models.seat import Classroom, Seat, SeatAssignment, SeatSessionOverride  # noqa: F401
```

- [ ] **Step 4: 运行确认通过**

Run: `conda run -n student-manage python -m pytest tests/unit/test_seat_layout.py -v -n 0`
Expected: 5 passed

- [ ] **Step 5: 确认模型能被整体导入（metadata 完整）**

Run: `conda run -n student-manage python -c "import sys; sys.path.insert(0, 'backend'); import app.models; print('tables:', len(app.models.SQLModel.metadata.tables))"`
Expected: 正常打印，表数比改动前多 4

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/seat.py backend/app/core/seat_layout.py backend/app/models/checkin.py backend/app/models/__init__.py tests/unit/test_seat_layout.py
git commit -m "feat(seat): 模型层——四张新表模型 + CheckinRecord.seat_id + 座位编号纯函数"
```

---

### Task 3: CRUD——教室管理与布局重建

**Files:**
- Create: `backend/app/crud/seat.py`（本任务只放教室部分；Task 4/5 继续往这个文件加）
- Test: `tests/unit/crud/test_seat_classroom.py`

**Interfaces:**
- Consumes: Task 2 模型 + `build_seat_rows`
- Produces（Task 5/6 依赖这些名字）:
  - `create_classroom(session, *, name: str, rows: int, cols: int) -> Classroom`（重名 → `ClassroomNameConflictError`）
  - `get_classroom(session, classroom_id: int) -> Optional[Classroom]`
  - `get_classroom_by_name(session, name: str) -> Optional[Classroom]`
  - `list_classrooms(session, *, include_archived: bool = False) -> list[Classroom]`
  - `update_classroom_layout(session, classroom_id: int, *, rows: int, cols: int) -> Classroom`（缩布局会删掉**已有分配或故障标记**的座位 → `SeatLayoutConflictError(removed_seat_nos: list[str])`）
  - `set_classroom_status(session, classroom_id: int, status: str) -> Classroom`
  - 异常类（放 `backend/app/crud/seat.py` 顶部）：`ClassroomNameConflictError` / `ClassroomNotFoundError` / `SeatLayoutConflictError`

- [ ] **Step 1: 写失败的单测**

```python
# tests/unit/crud/test_seat_classroom.py
"""教室 CRUD 单测：建教室自动生成座位、布局重建保护已分配座位。"""
import pytest
from sqlmodel import select

from app.crud.seat import (
    ClassroomNameConflictError,
    SeatLayoutConflictError,
    create_classroom,
    get_classroom,
    list_classrooms,
    set_classroom_status,
    update_classroom_layout,
)
from app.models.seat import Seat, SeatAssignment


class TestCreateClassroom:
    def test_creates_seats(self, session):
        room = create_classroom(session, name="机房302", rows=3, cols=4)
        seats = session.exec(select(Seat).where(Seat.classroom_id == room.id)).all()
        assert len(seats) == 12
        assert {s.seat_no for s in seats} == {f"P{r}{c}" for r in (1, 2, 3) for c in (1, 2, 3, 4)}

    def test_duplicate_name_raises(self, session):
        create_classroom(session, name="机房302", rows=2, cols=2)
        with pytest.raises(ClassroomNameConflictError):
            create_classroom(session, name="机房302", rows=2, cols=2)


class TestUpdateLayout:
    def test_grow_adds_seats(self, session):
        room = create_classroom(session, name="机房303", rows=2, cols=2)
        update_classroom_layout(session, room.id, rows=2, cols=4)
        seats = session.exec(select(Seat).where(Seat.classroom_id == room.id)).all()
        assert len(seats) == 8

    def test_shrink_with_assignment_refused(self, session, seed_refs):
        room = create_classroom(session, name="机房304", rows=2, cols=2)
        seat = session.exec(
            select(Seat).where(Seat.classroom_id == room.id, Seat.seat_no == "P22")
        ).one()
        session.add(SeatAssignment(
            seat_id=seat.id, student_id="S001", classroom_id=room.id,
            semester_id=seed_refs["semester_id"],
        ))
        session.commit()
        with pytest.raises(SeatLayoutConflictError) as exc:
            update_classroom_layout(session, room.id, rows=1, cols=1)  # P12/P21/P22 都会被删
        assert "P22" in exc.value.removed_seat_nos

    def test_shrink_without_assignment_ok(self, session):
        room = create_classroom(session, name="机房305", rows=2, cols=2)
        update_classroom_layout(session, room.id, rows=1, cols=2)
        seats = session.exec(select(Seat).where(Seat.classroom_id == room.id)).all()
        assert {s.seat_no for s in seats} == {"P11", "P12"}


class TestStatus:
    def test_archive_hides_from_default_list(self, session):
        room = create_classroom(session, name="机房306", rows=1, cols=1)
        set_classroom_status(session, room.id, "archived")
        assert room.id not in [c.id for c in list_classrooms(session)]
        assert room.id in [c.id for c in list_classrooms(session, include_archived=True)]
```

注意：`seed_refs` fixture 在 `tests/conftest.py` 已存在（造 3 个班 + 当前学期）；`session` fixture 同文件。

**测试数据铁律（Task 3 实践踩出）**：凡插入 `SeatAssignment`（或任何 FK→`students.student_id` 的表），必须先在同一个 session 里建对应学生行——`session.add(Student(student_id="S001", name="张三")); session.commit()`。`Student` 只有 `student_id`/`name` 两列必填。本计划 Task 4/5 的测试代码同理。

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage python -m pytest tests/unit/crud/test_seat_classroom.py -v -n 0`
Expected: FAIL（`app.crud.seat` 不存在）

- [ ] **Step 3: 实现**

```python
# backend/app/crud/seat.py（本任务部分）
"""座位系统 CRUD。惯例：模块级裸函数，第一参数 session，自行 commit/refresh。"""
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.seat_layout import build_seat_rows
from app.models.seat import Classroom, Seat, SeatAssignment


class ClassroomNameConflictError(Exception):
    pass


class ClassroomNotFoundError(Exception):
    pass


class SeatLayoutConflictError(Exception):
    """缩布局会删掉已有分配/故障标记的座位。removed_seat_nos 供前端提示。"""

    def __init__(self, removed_seat_nos: list[str]):
        super().__init__(f"布局变更将删除已有占用的座位: {', '.join(removed_seat_nos)}")
        self.removed_seat_nos = removed_seat_nos


def create_classroom(session: Session, *, name: str, rows: int, cols: int) -> Classroom:
    room = Classroom(name=name, rows=rows, cols=cols,
                     created_at=datetime.now(), updated_at=datetime.now())
    session.add(room)
    try:
        session.flush()  # 拿 id，先不 commit，座位与教室同一事务
    except IntegrityError:
        session.rollback()
        raise ClassroomNameConflictError(name)
    for row in build_seat_rows(room.id, rows, cols):
        session.add(Seat(**row))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ClassroomNameConflictError(name)
    session.refresh(room)
    return room


def get_classroom(session: Session, classroom_id: int) -> Optional[Classroom]:
    return session.get(Classroom, classroom_id)


def get_classroom_by_name(session: Session, name: str) -> Optional[Classroom]:
    return session.exec(select(Classroom).where(Classroom.name == name)).first()


def list_classrooms(session: Session, *, include_archived: bool = False) -> list[Classroom]:
    q = select(Classroom)
    if not include_archived:
        q = q.where(Classroom.status == "active")
    return list(session.exec(q.order_by(Classroom.name)).all())


def set_classroom_status(session: Session, classroom_id: int, status: str) -> Classroom:
    room = session.get(Classroom, classroom_id)
    if room is None:
        raise ClassroomNotFoundError(classroom_id)
    room.status = status
    room.updated_at = datetime.now()
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


def update_classroom_layout(session: Session, classroom_id: int, *,
                            rows: int, cols: int) -> Classroom:
    """重建座位网格。保留仍在新网格内的座位（含其分配/故障标记）；新增差量座位；
    会被删掉的座位若带有分配或故障标记 → 拒绝，由调用方提示。"""
    room = session.get(Classroom, classroom_id)
    if room is None:
        raise ClassroomNotFoundError(classroom_id)

    existing = session.exec(select(Seat).where(Seat.classroom_id == classroom_id)).all()
    keep_positions = {(r, c) for r in range(1, rows + 1) for c in range(1, cols + 1)}
    to_delete = [s for s in existing if (s.row, s.col) not in keep_positions]

    if to_delete:
        delete_ids = [s.id for s in to_delete]
        assigned = session.exec(
            select(SeatAssignment).where(SeatAssignment.seat_id.in_(delete_ids))
        ).all()
        blocked = {s.seat_no for s in to_delete if s.is_broken}
        blocked |= {s.seat_no for s in to_delete
                    if s.id in {a.seat_id for a in assigned}}
        if blocked:
            raise SeatLayoutConflictError(sorted(blocked))
        for seat in to_delete:
            session.delete(seat)

    existing_positions = {(s.row, s.col) for s in existing if (s.row, s.col) in keep_positions}
    for row in build_seat_rows(classroom_id, rows, cols):
        if (row["row"], row["col"]) not in existing_positions:
            session.add(Seat(**row))

    room.rows = rows
    room.cols = cols
    room.updated_at = datetime.now()
    session.add(room)
    session.commit()
    session.refresh(room)
    return room
```

- [ ] **Step 4: 运行确认通过**

Run: `conda run -n student-manage python -m pytest tests/unit/crud/test_seat_classroom.py -v -n 0`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/crud/seat.py tests/unit/crud/test_seat_classroom.py
git commit -m "feat(seat): 教室 CRUD——创建自动生成座位，缩布局保护已分配座位"
```

---

### Task 4: CRUD——座位图查询与「我的座位」

**Files:**
- Modify: `backend/app/crud/seat.py`（追加查询函数）
- Test: `tests/unit/crud/test_seat_map.py`

**Interfaces:**
- Consumes: Task 2/3 的模型与教室 CRUD；`get_current_semester_id`（`app.core.term`）；`CheckinRecord`
- Produces:
  - `get_seat_map(session, classroom_id: int, *, semester_id: int, session_id: Optional[int] = None, viewer_student_id: Optional[str] = None) -> list[dict]`
    每格 dict：`{seat_id, seat_no, row, col, is_broken, state, student_id, student_name}`，state ∈ `"empty" | "assigned" | "occupied" | "mine"`
  - `get_my_seat_assignments(session, student_id: str, semester_id: int) -> list[dict]`
    每项：`{classroom_id, classroom_name, seat_id, seat_no, is_broken}`

**状态判定规则（写死在 docstring 里，前后端共用这套语义）：**
- `mine`：本学期固定分配给 viewer，或本课堂 override 指向 viewer
- `occupied`：本课堂（session_id 传入时）已有他人签到记录占用，或 override 指向他人
- `assigned`：本学期已分配给他人、但本课堂尚未占用
- `empty`：以上都不是

- [ ] **Step 1: 写失败的单测**

```python
# tests/unit/crud/test_seat_map.py
"""座位图查询：四态判定 + 我的座位列表。"""
from app.crud.seat import create_classroom, get_my_seat_assignments, get_seat_map
from app.models.checkin import CheckinRecord
from app.models.seat import SeatAssignment, SeatSessionOverride
from sqlmodel import select
from app.models.seat import Seat


def _seat(session, classroom_id, seat_no):
    return session.exec(
        select(Seat).where(Seat.classroom_id == classroom_id, Seat.seat_no == seat_no)
    ).one()


class TestSeatMap:
    def test_all_empty_initially(self, session, seed_refs):
        room = create_classroom(session, name="机房401", rows=2, cols=2)
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"])
        assert all(c["state"] == "empty" for c in cells)
        assert [c["seat_no"] for c in cells] == ["P11", "P12", "P21", "P22"]

    def test_assigned_state(self, session, seed_refs):
        room = create_classroom(session, name="机房402", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        session.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                   classroom_id=room.id,
                                   semester_id=seed_refs["semester_id"]))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"])
        assert cells[0]["state"] == "assigned"
        assert cells[0]["student_id"] == "S001"

    def test_mine_beats_assigned(self, session, seed_refs):
        room = create_classroom(session, name="机房403", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        session.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                   classroom_id=room.id,
                                   semester_id=seed_refs["semester_id"]))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                             viewer_student_id="S001")
        assert cells[0]["state"] == "mine"

    def test_occupied_in_session(self, session, seed_refs):
        room = create_classroom(session, name="机房404", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        session.add(CheckinRecord(session_id=9001, student_id="S002",
                                  student_name="李四", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat.id))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                             session_id=9001)
        assert cells[0]["state"] == "occupied"

    def test_override_marks_mine(self, session, seed_refs):
        room = create_classroom(session, name="机房405", rows=1, cols=2)
        seat = _seat(session, room.id, "P12")
        session.add(SeatSessionOverride(session_id=9002, student_id="S001",
                                        seat_id=seat.id))
        session.commit()
        cells = get_seat_map(session, room.id, semester_id=seed_refs["semester_id"],
                             session_id=9002, viewer_student_id="S001")
        assert cells[1]["state"] == "mine"


class TestMyAssignments:
    def test_lists_by_classroom(self, session, seed_refs):
        room = create_classroom(session, name="机房406", rows=1, cols=2)
        seat = _seat(session, room.id, "P11")
        session.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                   classroom_id=room.id,
                                   semester_id=seed_refs["semester_id"]))
        session.commit()
        mine = get_my_seat_assignments(session, "S001", seed_refs["semester_id"])
        assert mine == [{
            "classroom_id": room.id, "classroom_name": "机房406",
            "seat_id": seat.id, "seat_no": "P11", "is_broken": False,
        }]

    def test_empty_for_other_semester(self, session, seed_refs):
        assert get_my_seat_assignments(session, "S001", 999999) == []
```

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage python -m pytest tests/unit/crud/test_seat_map.py -v -n 0`
Expected: FAIL（`get_seat_map` / `get_my_seat_assignments` 不存在）

- [ ] **Step 3: 实现（追加到 backend/app/crud/seat.py）**

```python
from app.models.checkin import CheckinRecord
from app.models.seat import SeatSessionOverride


def get_seat_map(session: Session, classroom_id: int, *, semester_id: int,
                 session_id: Optional[int] = None,
                 viewer_student_id: Optional[str] = None) -> list[dict]:
    """座位图：四态 empty/assigned/occupied/mine。

    mine      = 本学期分配给 viewer，或本课堂 override 指向 viewer
    occupied  = 本课堂已有他人签到占用，或 override 指向他人（需传 session_id）
    assigned  = 本学期分配给他人且本课堂未占用
    empty     = 其余
    """
    seats = session.exec(
        select(Seat).where(Seat.classroom_id == classroom_id)
        .order_by(Seat.row, Seat.col)
    ).all()
    seat_ids = [s.id for s in seats]

    assignments = session.exec(
        select(SeatAssignment).where(
            SeatAssignment.seat_id.in_(seat_ids),
            SeatAssignment.semester_id == semester_id,
        )
    ).all() if seat_ids else []
    assigned_by_seat = {a.seat_id: a for a in assignments}

    occupied_by_seat: dict[int, str] = {}
    override_by_seat: dict[int, str] = {}
    override_by_student: dict[str, int] = {}
    if session_id is not None and seat_ids:
        records = session.exec(
            select(CheckinRecord).where(
                CheckinRecord.session_id == session_id,
                CheckinRecord.seat_id.in_(seat_ids),
            )
        ).all()
        occupied_by_seat = {r.seat_id: r.student_id for r in records if r.seat_id}
        overrides = session.exec(
            select(SeatSessionOverride).where(
                SeatSessionOverride.session_id == session_id,
                SeatSessionOverride.seat_id.in_(seat_ids),
            )
        ).all()
        override_by_seat = {o.seat_id: o.student_id for o in overrides}
        override_by_student = {o.student_id: o.seat_id for o in overrides}

    cells = []
    for s in seats:
        occupier = occupied_by_seat.get(s.id) or override_by_seat.get(s.id)
        fixed = assigned_by_seat.get(s.id)
        student_id = occupier or (fixed.student_id if fixed else None)
        if viewer_student_id and (
            student_id == viewer_student_id
            or override_by_student.get(viewer_student_id) == s.id
        ):
            state = "mine"
        elif occupier:
            state = "occupied"
        elif fixed:
            state = "assigned"
        else:
            state = "empty"
        cells.append({
            "seat_id": s.id, "seat_no": s.seat_no, "row": s.row, "col": s.col,
            "is_broken": s.is_broken, "state": state,
            "student_id": student_id, "student_name": None,
        })
    return cells


def get_my_seat_assignments(session: Session, student_id: str,
                            semester_id: int) -> list[dict]:
    rows = session.exec(
        select(SeatAssignment, Seat, Classroom)
        .join(Seat, SeatAssignment.seat_id == Seat.id)
        .join(Classroom, SeatAssignment.classroom_id == Classroom.id)
        .where(SeatAssignment.student_id == student_id,
               SeatAssignment.semester_id == semester_id)
    ).all()
    return [
        {
            "classroom_id": room.id, "classroom_name": room.name,
            "seat_id": seat.id, "seat_no": seat.seat_no, "is_broken": seat.is_broken,
        }
        for assignment, seat, room in rows
    ]
```

- [ ] **Step 4: 运行确认通过**

Run: `conda run -n student-manage python -m pytest tests/unit/crud/test_seat_map.py -v -n 0`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/crud/seat.py tests/unit/crud/test_seat_map.py
git commit -m "feat(seat): 座位图查询（四态）+ 我的座位列表"
```

---

### Task 5: CRUD——占座规则、故障标记、教师调座

**Files:**
- Modify: `backend/app/crud/seat.py`（追加）
- Test: `tests/unit/crud/test_seat_occupy.py`

**Interfaces:**
- Consumes: Task 3/4 全部；`CourseSession`
- Produces（Task 6 的 checkin 扩展直接用）:
  - `occupy_seat(session, *, student_id: str, seat_id: int, course_session_id: int, semester_id: int) -> dict`——返回 `{"seat_id", "seat_no", "created_fixed": bool, "temporary": bool}`
  - `set_seat_broken(session, seat_id: int, is_broken: bool) -> Seat`
  - `set_seat_override(session, *, session_id: int, student_id: str, seat_id: int) -> SeatSessionOverride`
  - `clear_seat_override(session, session_id: int, student_id: str) -> None`
  - 异常：`SeatNotFoundError` / `SeatBrokenError` / `SeatOccupiedError` / `NotMySeatError` / `SeatClassroomMismatchError`

**occupy_seat 规则（顺序敏感，写死）：**
1. 座位存在；其教室名 == 该课堂 `classroom` 字符串 → 否则 `SeatClassroomMismatchError`
2. 座位故障 → `SeatBrokenError`（任何情况不可坐）
3. 本课堂已被他人占用（checkin_records 或 override）→ `SeatOccupiedError`
4. 有本课堂 override 指向我 → 坐 override 的座位， mismatch 则 `NotMySeatError`；`temporary=True`
5. **座位本学期已固定分配给他人 → `SeatOccupiedError`**（评审裁决补入：否则撞 `uix_seat_semester` 变 500；与前端「assigned 不可选」语义一致）
6. 无固定分配（本学期本教室）→ 创建固定分配，`created_fixed=True`
7. 固定分配就是这个座位 → 通过
8. 固定分配故障 → 允许临时坐任意空位，`temporary=True`
9. 其余 → `NotMySeatError`

**评审裁决补入（Task 5 修复轮 1）：**
- DB 并发兜底：`checkin_records` 部分唯一索引 `(session_id, seat_id) WHERE seat_id IS NOT NULL`；`seat_session_overrides` 唯一约束 `(session_id, seat_id)`（写在 Task 1 迁移里，模型层同步）
- `set_seat_override` 后若该生本课堂已有 checkin 且座位不同 → 同步更正记录的 `seat_id`（记录语义 = 本课堂实际座位）

- [ ] **Step 1: 写失败的单测**

```python
# tests/unit/crud/test_seat_occupy.py
"""占座规则：首次固定 / 本人固定座 / 故障临坐 / 冲突拒绝。"""
import pytest
from sqlmodel import select

from app.crud.course_session import start_course_session
from app.crud.seat import (
    NotMySeatError, SeatBrokenError, SeatOccupiedError,
    clear_seat_override, create_classroom, occupy_seat,
    set_seat_broken, set_seat_override,
)
from app.models.seat import Seat, SeatAssignment


@pytest.fixture()
def room(session):
    return create_classroom(session, name="机房501", rows=2, cols=2)


def _seat(session, room, no):
    return session.exec(
        select(Seat).where(Seat.classroom_id == room.id, Seat.seat_no == no)
    ).one()


@pytest.fixture()
def course_session(session, seed_refs, room):
    return start_course_session(
        session, class_id=seed_refs["一班"], teacher_id=1,
        teacher_name="王老师", classroom=room.name,
    )


class TestOccupy:
    def test_first_choice_creates_fixed(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        result = occupy_seat(session, student_id="S001", seat_id=seat.id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"])
        assert result["created_fixed"] is True
        assert result["temporary"] is False
        fixed = session.exec(
            select(SeatAssignment).where(SeatAssignment.student_id == "S001")
        ).one()
        assert fixed.seat_id == seat.id

    def test_own_fixed_seat_ok(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=seat.id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        again = occupy_seat(session, student_id="S001", seat_id=seat.id,
                            course_session_id=course_session.id,
                            semester_id=seed_refs["semester_id"])
        assert again["created_fixed"] is False

    def test_other_seat_refused(self, session, seed_refs, room, course_session):
        occupy_seat(session, student_id="S001", seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        with pytest.raises(NotMySeatError):
            occupy_seat(session, student_id="S001",
                        seat_id=_seat(session, room, "P12").id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"])

    def test_broken_seat_refused(self, session, seed_refs, room, course_session):
        seat = set_seat_broken(session, _seat(session, room, "P21").id, True)
        with pytest.raises(SeatBrokenError):
            occupy_seat(session, student_id="S001", seat_id=seat.id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"])

    def test_fixed_broken_allows_temporary(self, session, seed_refs, room, course_session):
        fixed_seat = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=fixed_seat.id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        set_seat_broken(session, fixed_seat.id, True)
        result = occupy_seat(session, student_id="S001",
                             seat_id=_seat(session, room, "P22").id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"])
        assert result["temporary"] is True
        # 固定分配不变
        fixed = session.exec(
            select(SeatAssignment).where(SeatAssignment.student_id == "S001")
        ).one()
        assert fixed.seat_id == fixed_seat.id

    def test_occupied_by_other_refused(self, session, seed_refs, room, course_session):
        seat = _seat(session, room, "P11")
        occupy_seat(session, student_id="S001", seat_id=seat.id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        from app.models.checkin import CheckinRecord
        session.add(CheckinRecord(session_id=course_session.id, student_id="S001",
                                  student_name="张三", class_id=seed_refs["一班"],
                                  semester_id=seed_refs["semester_id"],
                                  checkin_type="code", seat_id=seat.id))
        session.commit()
        with pytest.raises(SeatOccupiedError):
            occupy_seat(session, student_id="S002", seat_id=seat.id,
                        course_session_id=course_session.id,
                        semester_id=seed_refs["semester_id"])


class TestOverride:
    def test_override_allows_other_seat(self, session, seed_refs, room, course_session):
        occupy_seat(session, student_id="S001",
                    seat_id=_seat(session, room, "P11").id,
                    course_session_id=course_session.id,
                    semester_id=seed_refs["semester_id"])
        target = _seat(session, room, "P22")
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=target.id)
        result = occupy_seat(session, student_id="S001", seat_id=target.id,
                             course_session_id=course_session.id,
                             semester_id=seed_refs["semester_id"])
        assert result["temporary"] is True

    def test_clear_override(self, session, seed_refs, room, course_session):
        set_seat_override(session, session_id=course_session.id,
                          student_id="S001", seat_id=_seat(session, room, "P22").id)
        clear_seat_override(session, course_session.id, "S001")
        from app.models.seat import SeatSessionOverride
        assert session.exec(
            select(SeatSessionOverride).where(
                SeatSessionOverride.session_id == course_session.id)
        ).first() is None

    def test_override_to_broken_refused(self, session, seed_refs, room, course_session):
        broken = set_seat_broken(session, _seat(session, room, "P12").id, True)
        with pytest.raises(SeatBrokenError):
            set_seat_override(session, session_id=course_session.id,
                              student_id="S001", seat_id=broken.id)
```

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage python -m pytest tests/unit/crud/test_seat_occupy.py -v -n 0`
Expected: FAIL（`occupy_seat` 等不存在）

- [ ] **Step 3: 实现（追加到 backend/app/crud/seat.py）**

```python
from app.models.course_session import CourseSession


class SeatNotFoundError(Exception):
    pass


class SeatBrokenError(Exception):
    pass


class SeatOccupiedError(Exception):
    pass


class NotMySeatError(Exception):
    pass


class SeatClassroomMismatchError(Exception):
    pass


def set_seat_broken(session: Session, seat_id: int, is_broken: bool) -> Seat:
    seat = session.get(Seat, seat_id)
    if seat is None:
        raise SeatNotFoundError(seat_id)
    seat.is_broken = is_broken
    session.add(seat)
    session.commit()
    session.refresh(seat)
    return seat


def _session_occupiers(session: Session, course_session_id: int) -> tuple[set, dict]:
    """本课堂占用情况：checkin_records + overrides。返回 (被占 seat_id 集合, seat_id→student_id)。"""
    records = session.exec(
        select(CheckinRecord).where(
            CheckinRecord.session_id == course_session_id,
            CheckinRecord.seat_id.is_not(None),
        )
    ).all()
    overrides = session.exec(
        select(SeatSessionOverride).where(
            SeatSessionOverride.session_id == course_session_id)
    ).all()
    by_seat = {r.seat_id: r.student_id for r in records}
    for o in overrides:
        by_seat.setdefault(o.seat_id, o.student_id)
    return set(by_seat), by_seat


def occupy_seat(session: Session, *, student_id: str, seat_id: int,
                course_session_id: int, semester_id: int) -> dict:
    """校验并占座。规则顺序见计划 Task 5。"""
    seat = session.get(Seat, seat_id)
    if seat is None:
        raise SeatNotFoundError(seat_id)

    cs = session.get(CourseSession, course_session_id)
    room = session.get(Classroom, seat.classroom_id)
    if cs is None or room is None or cs.classroom != room.name:
        raise SeatClassroomMismatchError(seat_id)

    if seat.is_broken:
        raise SeatBrokenError(seat.seat_no)

    occupied_ids, occupier_by_seat = _session_occupiers(session, course_session_id)
    if seat_id in occupied_ids and occupier_by_seat[seat_id] != student_id:
        raise SeatOccupiedError(seat.seat_no)

    override = session.get(SeatSessionOverride, (course_session_id, student_id))
    if override is not None:
        if override.seat_id != seat_id:
            raise NotMySeatError("教师已将你调到其他座位")
        return {"seat_id": seat_id, "seat_no": seat.seat_no,
                "created_fixed": False, "temporary": True}

    fixed = session.exec(
        select(SeatAssignment).where(
            SeatAssignment.student_id == student_id,
            SeatAssignment.semester_id == semester_id,
            SeatAssignment.classroom_id == seat.classroom_id,
        )
    ).first()

    if fixed is None:
        assignment = SeatAssignment(
            seat_id=seat_id, student_id=student_id,
            classroom_id=seat.classroom_id, semester_id=semester_id,
            created_at=datetime.now(),
        )
        session.add(assignment)
        session.commit()
        return {"seat_id": seat_id, "seat_no": seat.seat_no,
                "created_fixed": True, "temporary": False}

    if fixed.seat_id == seat_id:
        return {"seat_id": seat_id, "seat_no": seat.seat_no,
                "created_fixed": False, "temporary": False}

    fixed_seat = session.get(Seat, fixed.seat_id)
    if fixed_seat is not None and fixed_seat.is_broken:
        return {"seat_id": seat_id, "seat_no": seat.seat_no,
                "created_fixed": False, "temporary": True}

    raise NotMySeatError(f"你的固定座位是 {fixed_seat.seat_no if fixed_seat else fixed.seat_id}")


def set_seat_override(session: Session, *, session_id: int, student_id: str,
                      seat_id: int) -> SeatSessionOverride:
    """教师临时调座：本课堂有效。目标座位必须存在、未故障、本课堂未被他人占用。"""
    seat = session.get(Seat, seat_id)
    if seat is None:
        raise SeatNotFoundError(seat_id)
    if seat.is_broken:
        raise SeatBrokenError(seat.seat_no)
    occupied_ids, occupier_by_seat = _session_occupiers(session, session_id)
    if seat_id in occupied_ids and occupier_by_seat[seat_id] != student_id:
        raise SeatOccupiedError(seat.seat_no)

    override = session.get(SeatSessionOverride, (session_id, student_id))
    if override is None:
        override = SeatSessionOverride(session_id=session_id, student_id=student_id,
                                       seat_id=seat_id, created_at=datetime.now())
    else:
        override.seat_id = seat_id
    session.add(override)
    session.commit()
    session.refresh(override)
    return override


def clear_seat_override(session: Session, session_id: int, student_id: str) -> None:
    override = session.get(SeatSessionOverride, (session_id, student_id))
    if override is not None:
        session.delete(override)
        session.commit()
```

- [ ] **Step 4: 运行确认通过**

Run: `conda run -n student-manage python -m pytest tests/unit/crud/test_seat_occupy.py -v -n 0`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/crud/seat.py tests/unit/crud/test_seat_occupy.py
git commit -m "feat(seat): 占座规则（首次固定/故障临坐/冲突拒绝）+ 故障标记 + 教师调座 override"
```

---

### Task 6: API——教室/座位图/我的座位/故障/调座

**Files:**
- Create: `backend/app/api/routes/classrooms.py`
- Modify: `backend/app/api/routes/__init__.py`（导出 `classrooms_router`）
- Modify: `backend/main.py`（`app.include_router(classrooms_router, prefix="/api/v1")`，照现有模式）
- Modify: `backend/app/api/routes/checkin.py`（学生课堂查询在**这个文件**里：`get_course_session_for_student`，约第 417 行。在 `StudentSessionData`（第 83 行）加 `seat_classroom_id: Optional[int] = None`，并在 handler 返回的 data 里填充：`get_classroom_by_name(session, cs.classroom)` 命中且 status=active 时给 id，否则 None）
- Test: `tests/integration/test_seat_api.py`

**Interfaces:**
- Consumes: Task 3/4/5 的 CRUD；`require_admin_or_teacher`；`get_current_user`；`get_session`；`get_current_semester_id`
- Produces（前端 Task 8 按此契约）:
  - `GET /api/v1/classrooms` → `{success, data: [{id, name, rows, cols, status, seat_count}]}`
  - `POST /api/v1/classrooms` `{name, rows, cols}` → 201 `{success, data: {id, ...}}`；重名 409
  - `PUT /api/v1/classrooms/{id}` `{rows?, cols?, status?, name?}` → 200；布局冲突 409 + `data: {removed_seat_nos: [...]}`
  - `GET /api/v1/classrooms/{id}/seats?session_id=` → `{success, data: {classroom: {id,name,rows,cols}, seats: [{seat_id, seat_no, row, col, is_broken, state, student_id, student_name}]}}`
  - `GET /api/v1/seat-assignments/mine` → `{success, data: [{classroom_id, classroom_name, seat_id, seat_no, is_broken}]}`
  - `POST /api/v1/seats/{id}/broken` `{is_broken: bool}` → 200 `{success, data: {id, is_broken}}`
  - `POST /api/v1/sessions/{session_id}/seat-overrides` `{student_id, seat_id}` → 200
  - `DELETE /api/v1/sessions/{session_id}/seat-overrides/{student_id}` → 200
- 权限：classrooms 写操作 = admin/teacher；seats 图 = 学生（仅限自己班级活跃课堂所在教室）或教师/admin（传 session_id 时校验 `cs.teacher_id == int(user["sub"])` 或 admin）；overrides = 课堂所属教师或 admin；mine = 学生本人

- [ ] **Step 1: 写失败的集成测试**

```python
# tests/integration/test_seat_api.py
"""座位 API 集成测试。"""
import pytest


def _login(client, username, password, role):
    resp = client.post("/api/v1/login",
                       json={"username": username, "password": password, "role": role})
    assert resp.status_code == 200, resp.text


@pytest.fixture()
def classroom(client, admin_client):
    resp = admin_client.post("/api/v1/classrooms",
                             json={"name": "机房601", "rows": 2, "cols": 3})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


class TestClassroomCrud:
    def test_create_and_list(self, admin_client, classroom):
        resp = admin_client.get("/api/v1/classrooms")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()["data"]]
        assert "机房601" in names
        item = [c for c in resp.json()["data"] if c["name"] == "机房601"][0]
        assert item["seat_count"] == 6

    def test_create_duplicate_409(self, admin_client, classroom):
        resp = admin_client.post("/api/v1/classrooms",
                                 json={"name": "机房601", "rows": 1, "cols": 1})
        assert resp.status_code == 409

    def test_student_forbidden(self, student_client):
        resp = student_client.post("/api/v1/classrooms",
                                   json={"name": "机房X", "rows": 1, "cols": 1})
        assert resp.status_code == 403

    def test_layout_conflict_409(self, admin_client, client, test_engine,
                                 seed_refs, classroom):
        from sqlmodel import Session, select
        from app.models.seat import Seat, SeatAssignment
        with Session(test_engine) as s:
            seat = s.exec(select(Seat).where(
                Seat.classroom_id == classroom["id"], Seat.seat_no == "P23")).one()
            s.add(SeatAssignment(seat_id=seat.id, student_id="S001",
                                 classroom_id=classroom["id"],
                                 semester_id=seed_refs["semester_id"]))
            s.commit()
        resp = admin_client.put(f"/api/v1/classrooms/{classroom['id']}",
                                json={"rows": 1, "cols": 1})
        assert resp.status_code == 409
        assert "P23" in resp.json()["data"]["removed_seat_nos"]


class TestSeatMap:
    def test_student_reads_own_classroom_map(self, student_client, classroom):
        resp = student_client.get(f"/api/v1/classrooms/{classroom['id']}/seats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["classroom"]["rows"] == 2
        assert len(data["seats"]) == 6
        assert all(s["state"] == "empty" for s in data["seats"])

    def test_unauthenticated_401(self, client, classroom):
        resp = client.get(f"/api/v1/classrooms/{classroom['id']}/seats")
        assert resp.status_code == 401


class TestBrokenAndOverride:
    def test_mark_broken(self, teacher_client, test_engine, classroom):
        from sqlmodel import Session, select
        from app.models.seat import Seat
        with Session(test_engine) as s:
            seat = s.exec(select(Seat).where(
                Seat.classroom_id == classroom["id"], Seat.seat_no == "P11")).one()
            seat_id = seat.id
        resp = teacher_client.post(f"/api/v1/seats/{seat_id}/broken",
                                   json={"is_broken": True})
        assert resp.status_code == 200
        assert resp.json()["data"]["is_broken"] is True
```

说明：`admin_client` / `teacher_client` / `student_client` fixture 在 `tests/integration/conftest.py` 已存在。

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage python -m pytest tests/integration/test_seat_api.py -v -n 0`
Expected: FAIL（404）

- [ ] **Step 3: 实现路由**

```python
# backend/app/api/routes/classrooms.py
"""教室与座位 API。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select, func

from app.api.deps import get_current_user, require_admin_or_teacher
from app.core.db import get_session
from app.core.term import get_current_semester_id
from app.crud.checkin import get_active_course_session_by_class_id
from app.crud.seat import (
    ClassroomNameConflictError, ClassroomNotFoundError, NotMySeatError,
    SeatBrokenError, SeatLayoutConflictError, SeatNotFoundError, SeatOccupiedError,
    clear_seat_override, create_classroom, get_classroom, get_classroom_by_name,
    get_my_seat_assignments, get_seat_map, list_classrooms,
    set_classroom_status, set_seat_broken, set_seat_override,
    update_classroom_layout,
)
from app.models.checkin import CheckinRecord
from app.models.constants import ApiResponseConst
from app.models.course_session import CourseSession
from app.models.seat import Classroom, Seat
from app.models.student import Student

router = APIRouter(tags=["classrooms"])


def ok(data):
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: data}


class ClassroomCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    rows: int = Field(ge=1, le=50)
    cols: int = Field(ge=1, le=50)


class ClassroomUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    rows: Optional[int] = Field(default=None, ge=1, le=50)
    cols: Optional[int] = Field(default=None, ge=1, le=50)
    status: Optional[str] = Field(default=None, pattern="^(active|archived)$")


class BrokenIn(BaseModel):
    is_broken: bool


class OverrideIn(BaseModel):
    student_id: str
    seat_id: int


def _classroom_out(session: Session, room: Classroom) -> dict:
    count = session.exec(
        select(func.count()).select_from(Seat).where(Seat.classroom_id == room.id)
    ).one()
    return {"id": room.id, "name": room.name, "rows": room.rows, "cols": room.cols,
            "status": room.status, "seat_count": count}


@router.get("/classrooms")
def list_all(session: Session = Depends(get_session),
             user=Depends(require_admin_or_teacher)):
    return ok([_classroom_out(session, c)
               for c in list_classrooms(session, include_archived=True)])


@router.post("/classrooms", status_code=201)
def create(body: ClassroomCreateIn, session: Session = Depends(get_session),
           user=Depends(require_admin_or_teacher)):
    try:
        room = create_classroom(session, name=body.name, rows=body.rows, cols=body.cols)
    except ClassroomNameConflictError:
        raise HTTPException(409, "教室名已存在")
    return ok(_classroom_out(session, room))


@router.put("/classrooms/{classroom_id}")
def update(classroom_id: int, body: ClassroomUpdateIn,
           session: Session = Depends(get_session),
           user=Depends(require_admin_or_teacher)):
    room = get_classroom(session, classroom_id)
    if room is None:
        raise HTTPException(404, "教室不存在")
    try:
        if body.rows is not None or body.cols is not None:
            room = update_classroom_layout(
                session, classroom_id,
                rows=body.rows if body.rows is not None else room.rows,
                cols=body.cols if body.cols is not None else room.cols,
            )
        if body.status is not None:
            room = set_classroom_status(session, classroom_id, body.status)
        if body.name is not None and body.name != room.name:
            room.name = body.name
            session.add(room)
            session.commit()
            session.refresh(room)
    except SeatLayoutConflictError as e:
        raise HTTPException(409, detail=str(e))
    return ok(_classroom_out(session, room))
```

（409 的 `removed_seat_nos` 需要进 `data`：FastAPI 的 `HTTPException.detail` 落到 `message` 字段——本项目响应包装以 `ApiResponseConst` 为准；实现时在 exception handler 或直接 `return JSONResponse(status_code=409, content={success: False, data: {"removed_seat_nos": ...}, message: str(e)})`。）

座位图/我的座位/故障/调座端点：

```python
@router.get("/classrooms/{classroom_id}/seats")
def seat_map(classroom_id: int,
             session_id: Optional[int] = Query(default=None),
             session: Session = Depends(get_session),
             user=Depends(get_current_user)):
    room = get_classroom(session, classroom_id)
    if room is None or room.status != "active":
        raise HTTPException(404, "教室不存在")

    role = user.get("role")
    viewer_student_id: Optional[str] = None
    if role == "student":
        viewer_student_id = str(user["sub"])
        student = session.get(Student, viewer_student_id)
        cs = (get_active_course_session_by_class_id(session, student.class_id)
              if student and student.class_id else None)
        # 学生只能看自己班级活跃课堂所在教室的座位图
        if cs is None or cs.classroom != room.name:
            raise HTTPException(403, "当前没有可用的座位图")
        session_id = cs.id
    else:
        if session_id is not None:
            cs = session.get(CourseSession, session_id)
            if cs is None:
                raise HTTPException(404, "课堂不存在")
            if role != "admin" and cs.teacher_id != int(user["sub"]):
                raise HTTPException(403, "只能查看自己课堂的座位图")

    cells = get_seat_map(session, classroom_id,
                         semester_id=get_current_semester_id(session),
                         session_id=session_id,
                         viewer_student_id=viewer_student_id)
    # 补学生姓名（assigned/occupied/mine 需要显示名）
    ids = [c["student_id"] for c in cells if c["student_id"]]
    if ids:
        names = {s.student_id: s.name for s in session.exec(
            select(Student).where(Student.student_id.in_(ids))).all()}
        for c in cells:
            c["student_name"] = names.get(c["student_id"])
    return ok({"classroom": _classroom_out(session, room), "seats": cells})


@router.get("/seat-assignments/mine")
def mine(session: Session = Depends(get_session), user=Depends(get_current_user)):
    if user.get("role") != "student":
        raise HTTPException(403, "仅学生可用")
    return ok(get_my_seat_assignments(
        session, str(user["sub"]), get_current_semester_id(session)))


@router.post("/seats/{seat_id}/broken")
def mark_broken(seat_id: int, body: BrokenIn,
                session: Session = Depends(get_session),
                user=Depends(require_admin_or_teacher)):
    try:
        seat = set_seat_broken(session, seat_id, body.is_broken)
    except SeatNotFoundError:
        raise HTTPException(404, "座位不存在")
    return ok({"id": seat.id, "is_broken": seat.is_broken})


@router.post("/sessions/{session_id}/seat-overrides")
def set_override(session_id: int, body: OverrideIn,
                 session: Session = Depends(get_session),
                 user=Depends(get_current_user)):
    cs = session.get(CourseSession, session_id)
    if cs is None:
        raise HTTPException(404, "课堂不存在")
    if user.get("role") != "admin" and cs.teacher_id != int(user["sub"]):
        raise HTTPException(403, "只能调整自己课堂的座位")
    try:
        override = set_seat_override(session, session_id=session_id,
                                     student_id=body.student_id, seat_id=body.seat_id)
    except SeatNotFoundError:
        raise HTTPException(404, "座位不存在")
    except SeatBrokenError:
        raise HTTPException(409, "该座位电脑故障，不可调座")
    except SeatOccupiedError:
        raise HTTPException(409, "该座位本课堂已被占用")
    return ok({"session_id": override.session_id,
               "student_id": override.student_id, "seat_id": override.seat_id})


@router.delete("/sessions/{session_id}/seat-overrides/{student_id}")
def delete_override(session_id: int, student_id: str,
                    session: Session = Depends(get_session),
                    user=Depends(get_current_user)):
    cs = session.get(CourseSession, session_id)
    if cs is None:
        raise HTTPException(404, "课堂不存在")
    if user.get("role") != "admin" and cs.teacher_id != int(user["sub"]):
        raise HTTPException(403, "只能调整自己课堂的座位")
    clear_seat_override(session, session_id, student_id)
    return ok({"cleared": True})
```

注册（两处，照现有模式）：
- `backend/app/api/routes/__init__.py`：`from app.api.routes.classrooms import router as classrooms_router` 并加进 `__all__`
- `backend/main.py`：`from app.api.routes import classrooms_router` + `app.include_router(classrooms_router, prefix="/api/v1")`

checkin.py 的 `get_course_session_for_student` handler 扩展：返回 data 里加——

```python
seat_room = get_classroom_by_name(session, cs.classroom) if cs.classroom else None
data["seat_classroom_id"] = (
    seat_room.id if seat_room and seat_room.status == "active" else None
)
```

- [ ] **Step 4: 运行确认通过**

Run: `conda run -n student-manage python -m pytest tests/integration/test_seat_api.py -v -n 0`
Expected: 8 passed（含 Step 1 全部 + 补的 broken/override 用例）

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/classrooms.py backend/app/api/routes/__init__.py backend/main.py backend/app/api/routes/checkin.py tests/integration/test_seat_api.py
git commit -m "feat(seat): API——教室 CRUD/座位图/我的座位/故障标记/临时调座"
```

---

### Task 7: API——签到扩展 seat_id

**Files:**
- Modify: `backend/app/api/routes/checkin.py`（`CheckinRequest` 加 `seat_id: Optional[int]`；学生分支接入占座；重复签到幂等）
- Modify: `backend/app/crud/checkin.py`（`create_checkin` 加 `seat_id: Optional[int] = None` 参数，写入记录）
- Test: `tests/integration/test_seat_checkin_api.py`

**Interfaces:**
- Consumes: Task 5 `occupy_seat`；Task 2 `CheckinRecord.seat_id`
- Produces: `POST /api/v1/checkin` 学生分支接受可选 `seat_id`；课堂所在教室有座位图时 `seat_id` **必填**（缺省 422）

**学生分支插入点**（`verify_verification_code` 通过之后、`create_checkin` 之前）：

```
cs = get_active_course_session_by_class_id(...)  # 已有
验证码校验通过  # 已有
seat_info = None
room = get_classroom_by_name(db_session, cs.classroom) if cs.classroom else None
has_seat_map = room is not None and room.status == "active"
if has_seat_map and data.seat_id is None:
    → 422 "该课堂需要先选择座位"
if data.seat_id is not None:
    if not has_seat_map: → 422 "该课堂未启用座位图"
    seat_info = occupy_seat(...)  # 各异常 → 409，message 用异常文案
```

**重复签到幂等**：`create_checkin` 抛 `DuplicateCheckinError` 时，查已有记录：
- `existing.seat_id == data.seat_id`（或都为 None）→ 返回 200 原数据（幂等成功）
- `existing.seat_id is None and data.seat_id` → 更新该记录 `seat_id`，返回 200
- 其余 → 409（原行为）

- [ ] **Step 1: 写失败的集成测试**

```python
# tests/integration/test_seat_checkin_api.py
"""带座位的签到全流程。"""
import pytest
from sqlmodel import Session, select

from app.core.qr_signature import generate_verification_code
from app.crud.course_session import start_course_session
from app.models.checkin import CheckinRecord
from app.models.seat import Seat, SeatAssignment


@pytest.fixture()
def seat_classroom(test_engine, seed_refs):
    """造 2x2 教室 + 一班活跃课堂（classroom=机房701）。"""
    from app.crud.seat import create_classroom
    with Session(test_engine) as s:
        room = create_classroom(s, name="机房701", rows=2, cols=2)
        cs = start_course_session(s, class_id=seed_refs["一班"], teacher_id=1,
                                  teacher_name="王老师", classroom="机房701")
        return {"room_id": room.id, "session_code": cs.session_code,
                "session_id": cs.id}


def _seat_id(test_engine, room_id, no):
    with Session(test_engine) as s:
        return s.exec(select(Seat).where(
            Seat.classroom_id == room_id, Seat.seat_no == no)).one().id


def _code(session_code):
    return generate_verification_code(session_code)["code"]


def _checkin(client, student, session_code, seat_id=None):
    payload = {
        "student_id": student.student_id,
        "student_name": student.name,
        "verification_code": _code(session_code),
    }
    if seat_id is not None:
        payload["seat_id"] = seat_id
    return client.post("/api/v1/checkin", json=payload)


class TestSeatCheckin:
    def test_first_checkin_picks_and_fixes_seat(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P12")
        resp = _checkin(student_client, student,
                        seat_classroom["session_code"], seat_id)
        assert resp.status_code == 200, resp.text
        with Session(test_engine) as s:
            record = s.exec(select(CheckinRecord).where(
                CheckinRecord.student_id == student.student_id)).one()
            assert record.seat_id == seat_id
            fixed = s.exec(select(SeatAssignment).where(
                SeatAssignment.student_id == student.student_id)).one()
            assert fixed.seat_id == seat_id  # 首次自选 → 固定

    def test_wrong_code_occupies_nothing(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P11")
        resp = student_client.post("/api/v1/checkin", json={
            "student_id": student.student_id, "student_name": student.name,
            "verification_code": "000000", "seat_id": seat_id,
        })
        assert resp.status_code in (400, 401, 403)
        with Session(test_engine) as s:
            assert s.exec(select(CheckinRecord).where(
                CheckinRecord.student_id == student.student_id)).first() is None
            assert s.exec(select(SeatAssignment).where(
                SeatAssignment.student_id == student.student_id)).first() is None

    def test_same_seat_recheckin_idempotent(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P21")
        r1 = _checkin(student_client, student, seat_classroom["session_code"], seat_id)
        r2 = _checkin(student_client, student, seat_classroom["session_code"], seat_id)
        assert r1.status_code == 200 and r2.status_code == 200
        with Session(test_engine) as s:
            assert len(s.exec(select(CheckinRecord).where(
                CheckinRecord.student_id == student.student_id)).all()) == 1

    def test_other_seat_recheckin_409(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        first = _seat_id(test_engine, seat_classroom["room_id"], "P11")
        second = _seat_id(test_engine, seat_classroom["room_id"], "P22")
        assert _checkin(student_client, student,
                        seat_classroom["session_code"], first).status_code == 200
        resp = _checkin(student_client, student,
                        seat_classroom["session_code"], second)
        assert resp.status_code == 409

    def test_missing_seat_when_map_enabled_422(
            self, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        student = sample_students[0]
        resp = _checkin(student_client, student, seat_classroom["session_code"])
        assert resp.status_code == 422

    def test_broken_seat_409(
            self, admin_client, student_client, sample_students, test_engine,
            seed_refs, seat_classroom):
        seat_id = _seat_id(test_engine, seat_classroom["room_id"], "P11")
        admin_client.post(f"/api/v1/seats/{seat_id}/broken", json={"is_broken": True})
        student = sample_students[0]
        resp = _checkin(student_client, student,
                        seat_classroom["session_code"], seat_id)
        assert resp.status_code == 409
```

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage python -m pytest tests/integration/test_seat_checkin_api.py -v -n 0`
Expected: FAIL（`seat_id` 被忽略 → test_missing_seat_when_map_enabled_422 等失败）

- [ ] **Step 3: 实现**

`backend/app/api/routes/checkin.py`：
- `CheckinRequest` 加 `seat_id: Optional[int] = None`
- 学生分支在验证码校验通过后插入「插入点」里的逻辑；`occupy_seat` 的异常映射：
  - `SeatNotFoundError` → 404
  - `SeatClassroomMismatchError` → 422 "座位不属于本课堂教室"
  - `SeatBrokenError` → 409 "该座位电脑故障，请选择其他座位"
  - `SeatOccupiedError` → 409 "该座位已被占用"
  - `NotMySeatError` → 409（文案用异常 message）
- `create_checkin(..., seat_id=seat_info["seat_id"] if seat_info else None)`
- `DuplicateCheckinError` 分支按上面的幂等规则处理

`backend/app/crud/checkin.py`：`create_checkin` 加参数 `seat_id: Optional[int] = None`，构造 `CheckinRecord` 时带上。

- [ ] **Step 4: 运行确认通过**

Run: `conda run -n student-manage python -m pytest tests/integration/test_seat_checkin_api.py tests/integration/test_qr_checkin_api.py -v -n 0`
Expected: 新测试全过 + 旧签到测试不回退

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/routes/checkin.py backend/app/crud/checkin.py tests/integration/test_seat_checkin_api.py
git commit -m "feat(seat): 签到接入座位——seat_id 校验/占座/幂等，验证码错不占座"
```

---

### Task 8: 前端——类型、API 客户端、composables

**Files:**
- Create: `frontend-v3/src/types/seats.ts`
- Modify: `frontend-v3/src/types/index.ts`（`export * from './seats'`）
- Create: `frontend-v3/src/api/seats.ts`
- Modify: `frontend-v3/src/api/checkin.ts`（请求类型加 `seat_id?: number`；课堂查询响应类型加 `seat_classroom_id: number | null`）
- Create: `frontend-v3/src/composables/useSeatMap.ts`
- Modify: `frontend-v3/src/composables/useStudentCheckin.ts`（`useStudentSelfCheckin` 的 mutation 载荷加 `seat_id`）
- Test: `frontend-v3/test/composables/useSeatMap.spec.ts`

**Interfaces:**
- Produces（Task 9/10/11 依赖）:
  - 类型：`SeatState = 'empty' | 'assigned' | 'occupied' | 'mine'`；`SeatCell { seat_id, seat_no, row, col, is_broken, state, student_id, student_name }`；`SeatMapData { classroom: ClassroomInfo, seats: SeatCell[] }`；`ClassroomInfo { id, name, rows, cols, status, seat_count }`；`MySeatAssignment { classroom_id, classroom_name, seat_id, seat_no, is_broken }`
  - API：`classroomsApi.{list, create, update, getSeats(id, sessionId?)}`；`seatsApi.setBroken(seatId, isBroken)`；`seatAssignmentsApi.mine()`；`seatOverridesApi.{set(sessionId, studentId, seatId), clear(sessionId, studentId)}`
  - Composable：`useSeatMap(classroomId: Ref<number|null>, sessionId: Ref<number|null>)`（queryKey `['seat-map', classroomId, sessionId]`，两者都有值才 enabled，10s 轮询——与 `useStudentCourseSession` 一致）

- [ ] **Step 1: 写失败的前端测试**

```ts
// frontend-v3/test/composables/useSeatMap.spec.ts
/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { mount } from '@vue/test-utils'
import { useSeatMap } from '@/composables/useSeatMap'

vi.mock('@/api/seats', () => ({
  classroomsApi: { getSeats: vi.fn() },
  seatsApi: { setBroken: vi.fn() },
  seatAssignmentsApi: { mine: vi.fn() },
  seatOverridesApi: { set: vi.fn(), clear: vi.fn() },
}))

import { classroomsApi } from '@/api/seats'
const mockedGetSeats = vi.mocked(classroomsApi.getSeats)

function mountComposable(classroomId: number | null, sessionId: number | null) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  let result: ReturnType<typeof useSeatMap> | undefined
  mount({
    setup() {
      result = useSeatMap(ref(classroomId), ref(sessionId))
      return () => null
    },
  }, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } })
  return result!
}

describe('useSeatMap', () => {
  beforeEach(() => mockedGetSeats.mockReset())

  it('classroomId 为空时不发起请求', () => {
    mountComposable(null, 1)
    expect(mockedGetSeats).not.toHaveBeenCalled()
  })

  it('classroomId + sessionId 都有值时请求座位图', async () => {
    mockedGetSeats.mockResolvedValue({
      classroom: { id: 1, name: '机房302', rows: 2, cols: 2, status: 'active', seat_count: 4 },
      seats: [],
    })
    const { isSuccess } = mountComposable(1, 10)
    await vi.waitFor(() => expect(isSuccess.value).toBe(true))
    expect(mockedGetSeats).toHaveBeenCalledWith(1, 10)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend-v3 && pnpm test:run test/composables/useSeatMap.spec.ts`
Expected: FAIL（模块不存在）

- [ ] **Step 3: 实现**

```ts
// frontend-v3/src/types/seats.ts
/** 座位系统类型（与 backend/app/api/routes/classrooms.py 响应一致） */

export type SeatState = 'empty' | 'assigned' | 'occupied' | 'mine'

export interface SeatCell {
  seat_id: number
  seat_no: string
  row: number
  col: number
  is_broken: boolean
  state: SeatState
  student_id: string | null
  student_name: string | null
}

export interface ClassroomInfo {
  id: number
  name: string
  rows: number
  cols: number
  status: string
  seat_count: number
}

export interface SeatMapData {
  classroom: ClassroomInfo
  seats: SeatCell[]
}

export interface MySeatAssignment {
  classroom_id: number
  classroom_name: string
  seat_id: number
  seat_no: string
  is_broken: boolean
}
```

```ts
// frontend-v3/src/api/seats.ts
// get 的签名是 get<T>(url, params?, options?) —— params 是第二个位置参数，不是 { params }
import { get, post, put, del } from '@/lib/api'
import type { ClassroomInfo, MySeatAssignment, SeatMapData } from '@/types/seats'

export const classroomsApi = {
  list: () => get<ClassroomInfo[]>('/classrooms'),
  create: (data: { name: string; rows: number; cols: number }) =>
    post<ClassroomInfo>('/classrooms', data),
  update: (id: number, data: { name?: string; rows?: number; cols?: number; status?: string }) =>
    put<ClassroomInfo>(`/classrooms/${id}`, data),
  getSeats: (id: number, sessionId?: number | null) =>
    get<SeatMapData>(
      `/classrooms/${id}/seats`,
      sessionId != null ? { session_id: sessionId } : undefined,
    ),
}

export const seatsApi = {
  setBroken: (seatId: number, isBroken: boolean) =>
    post<{ id: number; is_broken: boolean }>(`/seats/${seatId}/broken`, { is_broken: isBroken }),
}

export const seatAssignmentsApi = {
  mine: () => get<MySeatAssignment[]>('/seat-assignments/mine'),
}

export const seatOverridesApi = {
  set: (sessionId: number, studentId: string, seatId: number) =>
    post(`/sessions/${sessionId}/seat-overrides`, { student_id: studentId, seat_id: seatId }),
  clear: (sessionId: number, studentId: string) =>
    del(`/sessions/${sessionId}/seat-overrides/${studentId}`),
}
```

（`@/lib/api` 导出已核实：`get/post/put/del/patch`，其中 `get(url, params?)` 的 params 是第二个位置参数。）

```ts
// frontend-v3/src/composables/useSeatMap.ts
import { computed, type Ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { classroomsApi } from '@/api/seats'

/** 座位图查询：classroomId 与 sessionId 都有值才拉取，10s 轮询。 */
export function useSeatMap(classroomId: Ref<number | null>, sessionId: Ref<number | null>) {
  const enabled = computed(() => classroomId.value != null && sessionId.value != null)
  return useQuery({
    queryKey: computed(() => ['seat-map', classroomId.value, sessionId.value]),
    queryFn: () => classroomsApi.getSeats(classroomId.value!, sessionId.value),
    enabled,
    refetchInterval: 10_000,
  })
}
```

`useStudentCheckin.ts` 的 `useStudentSelfCheckin`：mutation 函数签名改为接受 `{ seatId?: number }`（或扩展原参数对象），载荷加 `seat_id`；`onSuccess` 的 invalidate 列表追加 `'seat-map'`。**改完检查所有 invalidateQueries 与 queryKey 的跨文件一致**（全局约束）。

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend-v3 && pnpm test:run test/composables/useSeatMap.spec.ts test/composables/useStudentCheckin.spec.ts`
Expected: 全过（含既有 useStudentCheckin 测试不回退）

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/types/seats.ts frontend-v3/src/types/index.ts frontend-v3/src/api/seats.ts frontend-v3/src/api/checkin.ts frontend-v3/src/composables/useSeatMap.ts frontend-v3/src/composables/useStudentCheckin.ts frontend-v3/test/composables/useSeatMap.spec.ts
git commit -m "feat(seat): 前端类型/API 客户端/useSeatMap composable"
```

---

### Task 9: 前端——StickFigure + SeatUnit

**Files:**
- Create: `frontend-v3/src/components/seats/StickFigure.vue`
- Create: `frontend-v3/src/components/seats/SeatUnit.vue`
- Test: `frontend-v3/test/components/seats/StickFigure.spec.ts`
- Test: `frontend-v3/test/components/seats/SeatUnit.spec.ts`

**Interfaces:**
- Consumes: Task 8 的 `SeatCell` / `SeatState`
- Produces:
  - `StickFigure.vue`——props `{ pose: 'stand' | 'walk' | 'carry' | 'sit' | 'scratch' | 'cheer' }`；纯 SVG 无交互
  - `SeatUnit.vue`——props `{ seat: SeatCell, selectable: boolean }`；emit `(click)`；data 属性 `data-state` / `data-broken` 供测试断言

- [ ] **Step 1: 写失败的测试**

```ts
// frontend-v3/test/components/seats/StickFigure.spec.ts
/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StickFigure from '@/components/seats/StickFigure.vue'

describe('StickFigure', () => {
  it('渲染 svg 且 data-pose 跟随 prop', () => {
    const wrapper = mount(StickFigure, { props: { pose: 'walk' } })
    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.attributes('data-pose')).toBe('walk')
  })

  it('六个姿势都合法', () => {
    for (const pose of ['stand', 'walk', 'carry', 'sit', 'scratch', 'cheer'] as const) {
      const wrapper = mount(StickFigure, { props: { pose } })
      expect(wrapper.find('svg').exists()).toBe(true)
    }
  })

  it('头部始终是圆形（圆头设定）', () => {
    const wrapper = mount(StickFigure, { props: { pose: 'sit' } })
    expect(wrapper.find('circle.stick-head').exists()).toBe(true)
  })
})
```

```ts
// frontend-v3/test/components/seats/SeatUnit.spec.ts
/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SeatUnit from '@/components/seats/SeatUnit.vue'
import type { SeatCell } from '@/types/seats'

const cell = (over: Partial<SeatCell> = {}): SeatCell => ({
  seat_id: 1, seat_no: 'P11', row: 1, col: 1, is_broken: false,
  state: 'empty', student_id: null, student_name: null, ...over,
})

describe('SeatUnit', () => {
  it('空位显示座位编号', () => {
    const wrapper = mount(SeatUnit, { props: { seat: cell(), selectable: true } })
    expect(wrapper.text()).toContain('P11')
    expect(wrapper.attributes('data-state')).toBe('empty')
  })

  it('已占显示姓名', () => {
    const wrapper = mount(SeatUnit, {
      props: { seat: cell({ state: 'occupied', student_name: '张三' }), selectable: false },
    })
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).not.toContain('P11')
  })

  it('故障座位不可点', async () => {
    const wrapper = mount(SeatUnit, {
      props: { seat: cell({ is_broken: true }), selectable: true },
    })
    expect(wrapper.attributes('data-broken')).toBe('true')
    expect(wrapper.attributes('aria-disabled')).toBe('true')
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
  })

  it('可点的空位触发 click', async () => {
    const wrapper = mount(SeatUnit, { props: { seat: cell(), selectable: true } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('我的座位有 mine 态', () => {
    const wrapper = mount(SeatUnit, {
      props: { seat: cell({ state: 'mine', student_name: '我' }), selectable: true },
    })
    expect(wrapper.attributes('data-state')).toBe('mine')
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend-v3 && pnpm test:run test/components/seats/`
Expected: FAIL（组件不存在）

- [ ] **Step 3: 实现**

`StickFigure.vue`：单一 `<svg viewBox="0 0 40 64">`，结构：`<circle class="stick-head">`（圆头）+ 两眼两点 + 微笑 path + 躯干/四肢 `<line>`。六姿势用每个姿势一组 transform/坐标常量（`const POSES: Record<Pose, PoseCoords>`），模板按当前 pose 取值，`<line>`/`<circle>` 加 `transition: all .3s` 让姿势切换平滑。`prefers-reduced-motion` 下关 transition。

`SeatUnit.vue`：纵向桌面（rect）+ 侧视椅子（面向桌子、椅背朝门一侧——门在右，椅背朝右）+ 编号/姓名 + 故障斜杠标记。四态颜色用 scoped CSS 自定义属性（**不引用全局令牌，深色主题在 Task 10 的 SeatMap 作用域统一定义**，SeatUnit 用 `var(--seat-*)` 并给默认浅色兜底，保证组件可独立测试）：

```vue
<script setup lang="ts">
import type { SeatCell } from '@/types/seats'

const props = defineProps<{ seat: SeatCell; selectable: boolean }>()
const emit = defineEmits<{ (e: 'click'): void }>()

function onClick() {
  if (!props.selectable || props.seat.is_broken) return
  emit('click')
}
</script>

<template>
  <button
    type="button"
    class="seat-unit"
    :data-state="seat.state"
    :data-broken="seat.is_broken || undefined"
    :aria-disabled="!selectable || seat.is_broken || undefined"
    :aria-label="`${seat.seat_no}${seat.student_name ? ' ' + seat.student_name : ''}${seat.is_broken ? ' 电脑故障' : ''}`"
    @click="onClick"
  >
    <span class="seat-desk" aria-hidden="true" />
    <span class="seat-chair" aria-hidden="true" />
    <span class="seat-label">{{ seat.student_name ?? seat.seat_no }}</span>
    <span v-if="seat.is_broken" class="seat-broken-mark" aria-hidden="true">✕</span>
  </button>
</template>
```

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend-v3 && pnpm test:run test/components/seats/`
Expected: 全过

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/components/seats/StickFigure.vue frontend-v3/src/components/seats/SeatUnit.vue frontend-v3/test/components/seats/
git commit -m "feat(seat): StickFigure（六姿势）+ SeatUnit（四态+故障）组件"
```

---

### Task 10: 前端——SeatMap（深色作用域）+ SeatCheckinAnimator

**Files:**
- Create: `frontend-v3/src/components/seats/SeatMap.vue`
- Create: `frontend-v3/src/components/seats/SeatCheckinAnimator.vue`
- Test: `frontend-v3/test/components/seats/SeatMap.spec.ts`
- Test: `frontend-v3/test/components/seats/SeatCheckinAnimator.spec.ts`

**Interfaces:**
- Consumes: Task 8 `SeatMapData`；Task 9 `SeatUnit` / `StickFigure`
- Produces:
  - `SeatMap.vue`——props `{ classroom: ClassroomInfo, seats: SeatCell[], mode: 'student' | 'teacher', selectedSeatId?: number | null }`；emit `(seat-click, seat: SeatCell)`。渲染：讲台（顶部）、座位网格（每 2 列一条走廊）、右墙门1/门2 标记
  - `SeatCheckinAnimator.vue`——props `{ state: 'idle' | 'walking' | 'sitting' | 'success' | 'fail' }`；emit `(finished)`（success/fail 动画播完后触发）
- 深色主题：`.seat-map-dark` scoped 自定义属性，四态 `--seat-empty/assigned/occupied/mine`，发光用 `box-shadow`（不动全局令牌）

- [ ] **Step 1: 写失败的测试**

```ts
// frontend-v3/test/components/seats/SeatMap.spec.ts
/** @vitest-environment jsdom */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SeatMap from '@/components/seats/SeatMap.vue'
import type { ClassroomInfo, SeatCell } from '@/types/seats'

const classroom: ClassroomInfo = {
  id: 1, name: '机房302', rows: 2, cols: 4, status: 'active', seat_count: 8,
}
const seats: SeatCell[] = Array.from({ length: 8 }, (_, i) => ({
  seat_id: i + 1, seat_no: `P${Math.floor(i / 4) + 1}${(i % 4) + 1}`,
  row: Math.floor(i / 4) + 1, col: (i % 4) + 1,
  is_broken: false, state: 'empty', student_id: null, student_name: null,
}))

describe('SeatMap', () => {
  it('按 rows×cols 渲染全部座位', () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'student' },
    })
    expect(wrapper.findAll('.seat-unit')).toHaveLength(8)
  })

  it('有讲台与两个门标记', () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'student' },
    })
    expect(wrapper.find('.seat-podium').exists()).toBe(true)
    expect(wrapper.findAll('.seat-door')).toHaveLength(2)
  })

  it('学生模式点空位发出 seat-click', async () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'student' },
    })
    await wrapper.findAll('.seat-unit')[0].trigger('click')
    expect(wrapper.emitted('seat-click')?.[0][0]).toMatchObject({ seat_no: 'P11' })
  })

  it('深色作用域类存在', () => {
    const wrapper = mount(SeatMap, {
      props: { classroom, seats, mode: 'teacher' },
    })
    expect(wrapper.find('.seat-map-dark').exists()).toBe(true)
  })
})
```

```ts
// frontend-v3/test/components/seats/SeatCheckinAnimator.spec.ts
/** @vitest-environment jsdom */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SeatCheckinAnimator from '@/components/seats/SeatCheckinAnimator.vue'

describe('SeatCheckinAnimator', () => {
  it('idle 时不渲染火柴人', () => {
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'idle' } })
    expect(wrapper.find('[data-pose]').exists()).toBe(false)
  })

  it('walking → 火柴人进入', () => {
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'walking' } })
    expect(wrapper.find('[data-pose="walk"]').exists()).toBe(true)
  })

  it('success 动画播完发出 finished', async () => {
    vi.useFakeTimers()
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'success' } })
    await vi.runAllTimersAsync()
    expect(wrapper.emitted('finished')).toHaveLength(1)
    vi.useRealTimers()
  })

  it('fail 播挠头姿势', () => {
    const wrapper = mount(SeatCheckinAnimator, { props: { state: 'fail' } })
    expect(wrapper.find('[data-pose="scratch"]').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend-v3 && pnpm test:run test/components/seats/SeatMap.spec.ts test/components/seats/SeatCheckinAnimator.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现**

`SeatMap.vue` 骨架：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import SeatUnit from './SeatUnit.vue'
import type { ClassroomInfo, SeatCell } from '@/types/seats'

const props = defineProps<{
  classroom: ClassroomInfo
  seats: SeatCell[]
  mode: 'student' | 'teacher'
  selectedSeatId?: number | null
}>()
const emit = defineEmits<{ (e: 'seat-click', seat: SeatCell): void }>()

/** 网格列：座位列 + 每 2 列一条走廊（走廊是空列） */
const gridStyle = computed(() => {
  const tracks: string[] = []
  for (let c = 1; c <= props.classroom.cols; c++) {
    tracks.push('1fr')
    if (c % 2 === 0 && c < props.classroom.cols) tracks.push('0.35fr') // 走廊
  }
  return { gridTemplateColumns: tracks.join(' ') }
})

function gridPos(seat: SeatCell) {
  // 走廊占列：col 3 的网格列 = 3 + floor((3-1)/2) = 4
  return { gridRow: seat.row + 1, gridColumn: seat.col + Math.floor((seat.col - 1) / 2) }
}

function selectable(seat: SeatCell) {
  if (seat.is_broken) return false
  if (props.mode === 'teacher') return true
  return seat.state === 'empty' || seat.state === 'mine'
}
</script>

<template>
  <div class="seat-map-dark">
    <div class="seat-podium">讲台</div>
    <div class="seat-grid" :style="gridStyle">
      <SeatUnit
        v-for="seat in seats"
        :key="seat.seat_id"
        :seat="seat"
        :selectable="selectable(seat)"
        :style="gridPos(seat)"
        :class="{ 'seat-selected': seat.seat_id === selectedSeatId }"
        @click="emit('seat-click', seat)"
      />
    </div>
    <div class="seat-door seat-door-1" aria-hidden="true">门1</div>
    <div class="seat-door seat-door-2" aria-hidden="true">门2</div>
  </div>
</template>

<style scoped>
.seat-map-dark {
  /* 深色科技风只活在这个作用域，不动全局令牌 */
  --seat-bg: #0b1220;
  --seat-empty: #1e293b;
  --seat-assigned: #334155;
  --seat-occupied: #f59e0b;
  --seat-mine: #22d3ee;
  --seat-broken: #ef4444;
  background: var(--seat-bg);
  position: relative;
  border-radius: 12px;
  padding: 16px 56px 16px 16px; /* 右侧留门的位置 */
}
/* 四态发光、走廊、门标记、讲台样式在此补全 */
</style>
```

`SeatCheckinAnimator.vue`：状态机——`walking`（walk 姿势从左侧 translate 进入）→ `success`（carry → sit → cheer，约 1.6s，播完 emit finished）→ `fail`（scratch 0.8s → walk 退回，播完 emit finished）。用 `setTimeout` 串联，`onUnmounted` 清理；`prefers-reduced-motion` 时直接 emit finished。

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend-v3 && pnpm test:run test/components/seats/`
Expected: 全过

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/components/seats/SeatMap.vue frontend-v3/src/components/seats/SeatCheckinAnimator.vue frontend-v3/test/components/seats/
git commit -m "feat(seat): SeatMap（深色作用域+走廊+门+讲台）+ 入座动画状态机"
```

---

### Task 11: 学生签到页接入

**Files:**
- Modify: `frontend-v3/src/views/student/Checkin.vue`
- Test: `frontend-v3/test/views/StudentCheckin.spec.ts`（追加用例）或新建 `frontend-v3/test/views/StudentSeatCheckin.spec.ts`

**Interfaces:**
- Consumes: Task 8/9/10 全部；现有 `useStudentCourseSession`（响应已含 `seat_classroom_id`，Task 6）
- Produces: 学生签到页两分支——`seat_classroom_id` 有值 → 座位图流程（选座 → 输验证码 → 动画 → 成功）；否则原流程不动

**交互顺序**（对应 spec §5）：
1. `activeSession.seat_classroom_id == null` → 渲染现有验证码卡片，零改动
2. 有值 → 渲染 `SeatMap`（`useSeatMap(seat_classroom_id, sessionId)`）+ 验证码 `Input`
3. 点座位（空位或我的）→ 选中态高亮 → 输 6 位验证码 → 提交 `{...原载荷, seat_id}`
4. 成功 → animator `success` 序列 → finished 后 `showToast('签到成功')` + invalidate（含 `'seat-map'`）
5. 失败（409/验证码错）→ animator `fail` → 清验证码保留选中，提示重输；409 文案直接展示后端 message
6. 我的固定座位故障（`mine` 格 `is_broken`）→ 顶部提示「你的座位电脑故障，请挑一个空位」

- [ ] **Step 1: 写失败的测试（新建 StudentSeatCheckin.spec.ts）**

```ts
/** @vitest-environment jsdom */
// mock useStudentCourseSession 返回 seat_classroom_id: 7；
// mock useSeatMap 返回两行两列空位；mock useStudentSelfCheckin 的 mutate 记录载荷
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import StudentCheckin from '@/views/student/Checkin.vue'

const mutate = vi.fn()

vi.mock('@/composables/useStudentCheckin', () => ({
  useStudentCourseSession: () => ({
    data: ref({
      id: 10, course_name: '计算机基础', classroom: '机房302',
      seat_classroom_id: 7, status: 'active',
    }),
    isLoading: ref(false), error: ref(null),
  }),
  useStudentSelfCheckin: () => ({ mutate, isPending: ref(false) }),
  useHasCheckedInSession: () => ({ data: ref(false) }),
}))

vi.mock('@/composables/useSeatMap', () => ({
  useSeatMap: () => ({
    data: ref({
      classroom: { id: 7, name: '机房302', rows: 1, cols: 2, status: 'active', seat_count: 2 },
      seats: [
        { seat_id: 71, seat_no: 'P11', row: 1, col: 1, is_broken: false, state: 'empty', student_id: null, student_name: null },
        { seat_id: 72, seat_no: 'P12', row: 1, col: 2, is_broken: false, state: 'empty', student_id: null, student_name: null },
      ],
    }),
    isLoading: ref(false), error: ref(null),
  }),
}))

vi.mock('@/stores', () => ({
  useAuthStore: () => ({ user: { id: 'S001', name: '张三', role: 'student' } }),
}))
vi.mock('@/composables/useToast', () => ({ useToast: () => ({ showToast: vi.fn() }) }))
vi.mock('@/lib/device', () => ({
  getDeviceId: () => Promise.resolve('dev-1'),
  getDeviceInfo: () => 'test',
}))

function mountPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return mount(StudentCheckin, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs: {
        Card: { template: '<div><slot /></div>' },
        Button: { template: '<button @click="$emit(\'click\')"><slot /></button>' },
        Input: {
          props: ['modelValue'],
          template: '<input class="mock-input" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        SeatMap: {
          props: ['seats'],
          template: '<div class="mock-seatmap"><button v-for="s in seats" :key="s.seat_id" class="mock-seat" @click="$emit(\'seat-click\', s)">{{ s.seat_no }}</button></div>',
        },
        SeatCheckinAnimator: { props: ['state'], template: '<div class="mock-animator" />' },
      },
    },
  })
}

describe('学生座位签到', () => {
  beforeEach(() => mutate.mockReset())

  it('有座位图时渲染 SeatMap', () => {
    const wrapper = mountPage()
    expect(wrapper.find('.mock-seatmap').exists()).toBe(true)
  })

  it('点座位 + 输验证码 → 提交带 seat_id', async () => {
    const wrapper = mountPage()
    await wrapper.findAll('.mock-seat')[0].trigger('click')
    await wrapper.find('.mock-input').setValue('123456')
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ seat_id: 71 }),
      expect.anything(),
    )
  })

  it('未选座位时提交被拦截', async () => {
    const wrapper = mountPage()
    await wrapper.find('.mock-input').setValue('123456')
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(mutate).not.toHaveBeenCalled()
  })
})
```

（按钮/输入框的具体 selector 按 Checkin.vue 实际结构调整。）

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend-v3 && pnpm test:run test/views/StudentSeatCheckin.spec.ts`
Expected: FAIL（无 SeatMap 分支）

- [ ] **Step 3: 实现 Checkin.vue 分支**

在现有模板中，验证码卡片外包一层 `v-if="!seatClassroomId"`，新增 `v-else` 的座位图块；`seatClassroomId = computed(() => session.value?.seat_classroom_id ?? null)`；`selectedSeat = ref<SeatCell | null>(null)`；提交时 `seat_id: selectedSeat.value.seat_id`；成功/失败驱动 animator 状态。**保留原有所有逻辑路径**（无座位图课堂行为零变化）。

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend-v3 && pnpm test:run test/views/`
Expected: 新测试 + 既有 StudentCheckin.spec.ts 全过

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/views/student/Checkin.vue frontend-v3/test/views/StudentSeatCheckin.spec.ts frontend-v3/test/views/StudentCheckin.spec.ts
git commit -m "feat(seat): 学生签到页接入座位图流程（选座→验证码→动画）"
```

---

### Task 12: 教师端——教室管理 + 课堂实时座位图

**Files:**
- Create: `frontend-v3/src/views/teacher/Classrooms.vue`（教室列表 + 新建/编辑布局 Dialog）
- Modify: `frontend-v3/src/router/index.ts`（教师 children 加 `{ path: 'classrooms', name: 'TeacherClassrooms', component: () => import('@/views/teacher/Classrooms.vue') }`；admin 段同样加 `/admin/classrooms` 复用同组件）
- Modify: `frontend-v3/src/layouts/DashboardLayout.vue`（教师与管理员导航数组各加 `{ name: '教室管理', path: '/<role>/classrooms', icon: Armchair }`——lucide 有 `Armchair` 图标；先确认 import 可用）
- Modify: `frontend-v3/src/components/ui/MobileDrawer.vue`（若抽屉有自己独立的导航数组则同步加）
- Modify: `frontend-v3/src/views/teacher/CourseSession.vue`（活跃课堂有 `seat_classroom_id` 时挂 `SeatMap` 实时面板 + 点座位弹操作：标记/取消故障、调座到该空位）
- Test: `frontend-v3/test/views/Classrooms.spec.ts`、`frontend-v3/test/views/TeacherSessionSeatMap.spec.ts`

**Interfaces:**
- Consumes: Task 8 API + Task 10 SeatMap（teacher 模式）
- Produces: 教师可配教室布局、看实时座位态、标记故障、给学生调座

**教师课堂页交互**：
- `SeatMap mode="teacher"` + `useSeatMap(seat_classroom_id, sessionId)`（10s 轮询自动刷新）
- 点座位 → 弹层两个操作：
  - 「标记电脑故障 / 取消故障」→ `seatsApi.setBroken` → invalidate `'seat-map'`
  - 「把学生调到这里」→ 学生选择（本班学生列表）→ `seatOverridesApi.set` → invalidate
- 故障中的座位若已有人固定分配，教师端显示姓名 + 故障标记叠加

- [ ] **Step 1: 写失败的测试**

```ts
// frontend-v3/test/views/Classrooms.spec.ts（要点）
// - mock classroomsApi.list 返回两间教室 → 渲染两行（名称 + rows×cols + seat_count）
// - 点「新建教室」→ Dialog 打开；填名称/排/列 → create 被调用且参数正确
// - list 里 seat_count 展示为「N 个座位」
```

```ts
// frontend-v3/test/views/TeacherSessionSeatMap.spec.ts（要点）
// - mock 活跃课堂带 seat_classroom_id → 渲染 SeatMap
// - 教师点故障标记操作 → seatsApi.setBroken(seatId, true) 被调用
// - 课堂无 seat_classroom_id → 不渲染 SeatMap（原页面不变）
```

- [ ] **Step 2: 运行确认失败**

Run: `cd frontend-v3 && pnpm test:run test/views/Classrooms.spec.ts test/views/TeacherSessionSeatMap.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现**（参照现有管理页模式：`Semesters.vue` 的表格 + Dialog 组合最贴近）

- [ ] **Step 4: 运行确认通过**

Run: `cd frontend-v3 && pnpm test:run`
Expected: 全量 335+ 通过

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/views/teacher/Classrooms.vue frontend-v3/src/views/teacher/CourseSession.vue frontend-v3/src/router/index.ts frontend-v3/src/layouts/DashboardLayout.vue frontend-v3/src/components/ui/MobileDrawer.vue frontend-v3/test/views/Classrooms.spec.ts frontend-v3/test/views/TeacherSessionSeatMap.spec.ts
git commit -m "feat(seat): 教师端——教室管理页 + 课堂实时座位图（故障/调座）"
```

---

### Task 13: 收尾——全量回归 + 文档

- [ ] **Step 1: 后端全量**

Run: `conda run -n student-manage python -m pytest tests/ -q`
Expected: 全绿（注意分库前置条件，见 CLAUDE.md「测试性能设计」）

- [ ] **Step 2: 前端全量 + 类型检查**

Run: `cd frontend-v3 && pnpm test:run && npx vue-tsc --noEmit`
Expected: 全绿 + 0 类型错误

- [ ] **Step 3: 冒烟验证（手动，起服务）**

按 CLAUDE.md 重启流程起后端+前端，走一遍：管理员建教室（3×4）→ 教师开课选该教室 → 学生点座+验证码签到 → 教师端实时看到占用 → 教师标记故障 → 学生端看到不可选。

- [ ] **Step 4: 更新文档**

- `docs/API_CHANGELOG.md`：登记新增端点
- `CHANGELOG.md`：登记特性
- 本计划勾选完成

- [ ] **Step 5: Commit**

```bash
git add docs/API_CHANGELOG.md CHANGELOG.md docs/superpowers/plans/2026-09-22-seat-system.md
git commit -m "docs(seat): 登记座位系统 API 与变更日志"
```

---

## 自我评审记录

**Spec 覆盖**：
- §3 数据模型 → Task 1/2（含两处补全：seat_assignments.classroom_id 冗余、seat_session_overrides 表，已在 Task 1 说明理由）
- §4 布局配置 → Task 3/6/12
- §5 签到流程 → Task 5/7/11
- §6 组件/朝向/故障/调座/编号 → Task 9/10/11/12
- §7 接口 → Task 6/7（broken/override 两个端点是 §6.2 的隐含需求，spec §7 表格没列，计划里显式补齐）
- §8 迁移 → Task 1（幂等、无回填）
- §9 测试方案 → 各 Task 内嵌 + Task 13 全量
- §10 YAGNI → 未引入分区/预约/审批流

**类型一致性**：`SeatCell.state` 四态贯穿后端 dict / 前端类型 / 组件 data-state；`seat_classroom_id` 贯穿 course_sessions 响应 → 前端类型 → Checkin.vue 分支；CRUD 函数名在 Task 3/4/5 定义、Task 6/7 消费，已逐一核对。
