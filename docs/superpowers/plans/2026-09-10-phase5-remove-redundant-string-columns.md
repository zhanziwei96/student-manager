# Phase 5 实施计划：业务表冗余字符串列删除（class_name / semester）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除业务表的 `class_name` / `semester` 字符串冗余列（14 列），过滤统一为纯 FK 条件，展示与权限通过 `class_cache` 的 id→name 解析；删除过渡过滤器 `transition_filters.py`。

**Architecture:** 数据锚点唯一化——业务表只存 `class_id` / `semester_id`（FK）；对外 API 契约不变（响应仍含 `class_name` 键，由 FK 运行时解析；查询参数仍收 class_name，运行时解析为 id）。class_cache 重构为**简单值缓存**（id→name 字符串），避免 ORM 对象跨 session 的 detached 风险（与 term.py 既有修复一致）。

**Tech Stack:** FastAPI + SQLModel + PostgreSQL 12 + Alembic；Vue 3.5（前端无需改动——API 契约不变）+ vitest

**Spec:** [docs/SEMESTER_COHORT_REFACTOR_PLAN.md](../../docs/SEMESTER_COHORT_REFACTOR_PLAN.md) v1.2（Phase 4 步骤 5 收尾 + §2.4 + §七 P1「业务表冗余 class_name：当前规模无收益」）

## Context

Phase 0-4d 已完成并推送。唯一剩余项：业务表 `class_name` / `semester` 字符串列。

**决策依据（已完成分析）**：
- 计划 §七 优化表将「业务表冗余 class_name」列为 P1，实施策略明确「当前规模（2000 学生/10 教师）**无收益**」→ 该反范式化不产生价值
- 计划核心规则「过滤/JOIN 永远用 FK」——字符串列存在会持续诱发字符串过滤（transition_filters 的 `or_` 回退即此类 trick）
- 跨届同名班（2025届「1班」与 2026届「1班」同学期并存）下字符串过滤必然混淆，FK 是唯一正确锚点
- `class_cache`（id↔name 进程级缓存）已存在，为 FK→name 解析提供现成基础设施

**删除范围（14 列）**：

| 表 | class_name | semester |
|---|---|---|
| course_schedules | DELETE（L14） | DELETE（L44） |
| course_sessions | DELETE（L21） | DELETE（L59） |
| schedule_adjustments | — | DELETE（course_session.py L101） |
| checkin_records | DELETE（L37） | DELETE（L23） |
| questions | DELETE（L23） | DELETE（L16） |
| groups | DELETE（L23） | DELETE（L17） |
| group_score_logs | DELETE（L82） | DELETE（L101） |
| class_group_settings | DELETE（L82） | —（PK 已含 semester_id） |

**保留（§2.4 明确为「当前值冗余缓存/展示快照」，非本阶段范围）**：
- `students.class_name`（当前班级缓存，转班时与归属表同步）、`students.class_id`、`students.cohort_year`
- `checkin_records.student_name`（展示快照）

**前端无需改动**：API 响应与查询参数契约不变（见 Architecture）。

## Global Constraints

- Python 命令必须用 `conda run -n student-manage`；前端在 frontend-v3/ 用 pnpm
- 后端测试：项目根目录 `pytest tests/ -q`（xdist 4 分库并行）；测试库靠 SQLModel.metadata 建表（模型改了测试库自动跟随）
- 分支：从 main 切 `feat/remove-string-columns`；禁止直接改 main
- 代码质量五原则（架构一致、可改原代码、不留冗余、不用 trick、统一优雅）
- 后端 API 契约：ApiResponseConst 包装；教师权限从 course_offerings 派生；API 层收 class_name 参数时经 class_cache 解析为 class_id
- class_cache 只缓存**简单值**（int↔str），不缓存 ORM 对象（detached 风险）

---

### Task 1: 模型列删除 + 迁移（回填 + NOT NULL）

**Files:**
- Modify: `backend/app/models/course_schedule.py`、`course_session.py`、`checkin.py`、`question.py`、`group.py`
- Create: `backend/alembic/versions/20260910_remove_redundant_string_columns.py`
- Test: 现有测试大量使用 `class_name=` / `semester=` 构造 → 本任务先只改模型与迁移，测试在 Task 4 统一适配（中间态测试红是预期；每个 Task 结尾以「该 Task 新增/修改的验证」为准，Task 5 做全量绿）

**Interfaces:**
- Produces: 模型层无 `class_name`/`semester` 字符串列；`class_id`/`semester_id` 在 schedules/sessions/groups 上为必填（`int = Field(..., foreign_key=...)`），checkins/questions 保持可空

- [ ] **Step 1: 修改模型**

```python
# course_schedule.py —— 删除 class_name/semester，FK 改为必填
class CourseScheduleBase(SQLModel):
    course_name: str = Field(..., description="课程名称", max_length=100)
    class_id: int = Field(..., foreign_key="classes.id", index=True, description="班级ID")
    semester_id: int = Field(..., foreign_key="semesters.id", index=True, description="学期ID")
    # ...（其余字段不变）

# course_session.py —— CourseSession 与 ScheduleAdjustment 同规则
class CourseSessionBase(SQLModel):
    session_code: str = Field(..., description="课堂码", max_length=20)
    class_id: int = Field(..., foreign_key="classes.id", index=True, description="班级ID")
    semester_id: int = Field(..., foreign_key="semesters.id", index=True, description="学期ID")

# checkin.py —— class_name 删除，class_id 保持可空（历史签到可能无班级）
# class_id: Optional[int] = Field(default=None, foreign_key="classes.id", index=True) 已存在；删 class_name 与 semester

# question.py —— 删 class_name / semester（class_id 已存在且可空）
# group.py —— Group/GroupScoreLog/ClassGroupSettings 删 class_name 与 semester
```

同时删除这些文件里 `from app.core.term import get_current_term` 的 import 与 `default_factory=get_current_term`。

- [ ] **Step 2: 写迁移**

```python
"""remove redundant class_name/semester string columns from business tables"""
from typing import Union, Sequence
from alembic import op
import sqlalchemy as sa

revision = "20260910_remove_redundant_string_columns"
down_revision = "20260909_remove_assigned_classes"

def upgrade() -> None:
    # 回填：FK 为空且字符串可解析的行（best-effort；跨届同名班取最小 id）
    op.execute("""
        UPDATE course_schedules t SET class_id = c.id
        FROM classes c WHERE t.class_id IS NULL AND t.class_name = c.name
    """)
    op.execute("""
        UPDATE course_schedules t SET semester_id = s.id
        FROM semesters s WHERE t.semester_id IS NULL AND t.semester = s.label
    """)
    # （course_sessions / schedule_adjustments / checkin_records / questions /
    #   groups / group_score_logs 同模式，逐表执行）

    for table in ("course_schedules", "course_sessions", "schedule_adjustments",
                  "checkin_records", "questions", "groups", "group_score_logs"):
        op.drop_column(table, "semester")
    for table in ("course_schedules", "course_sessions", "checkin_records",
                  "questions", "groups", "group_score_logs", "class_group_settings"):
        op.drop_column(table, "class_name")

    # FK 必填化（回填后无 NULL）
    for table in ("course_schedules", "course_sessions", "groups"):
        op.alter_column(table, "class_id", nullable=False)
    for table in ("course_schedules", "course_sessions", "schedule_adjustments",
                  "groups", "group_score_logs"):
        op.alter_column(table, "semester_id", nullable=False)

def downgrade() -> None:
    raise NotImplementedError("冗余列已废弃，不回滚")
```

> 注意：`class_group_settings.class_name` 回退查询（`_get_class_group_settings` 的字符串回退）在 Task 3 删除。

- [ ] **Step 3: 迁移可执行性验证**

Run: `cd backend && conda run -n student-manage alembic upgrade head`
Expected: 无报错（对本地 dev 库执行；测试库由 SQLModel.metadata 重建）

- [ ] **Step 4: Commit**

```bash
git add backend/app/models backend/alembic/versions/20260910_remove_redundant_string_columns.py
git commit -m "refactor(models): remove class_name/semester string columns (FK-only anchor)"
```

---

### Task 2: 过滤器纯 FK 化 + 删除 transition_filters.py

**Files:**
- Delete: `backend/app/core/transition_filters.py`
- Modify: `backend/app/crud/student.py`、`checkin.py`、`group.py`、`group_score.py`、`question.py`、`schedule.py`、`course_session.py`、`backend/app/api/routes/schedules.py`

**Interfaces:**
- Consumes: Task 1 模型；`get_class_id_by_name(session, name)`（class_cache，保留）
- Produces: 所有过滤为纯 FK 条件（`Column.class_id == id` / `Column.semester_id == id`）

- [ ] **Step 1: 替换 31 处过滤调用**

模式A（班级过滤）：
```python
# 旧
query.where(class_filter(
    CourseSchedule.class_id, CourseSchedule.class_name,
    get_class_id_by_name(session, class_name), class_name,
))
# 新
query.where(CourseSchedule.class_id == get_class_id_by_name(session, class_name))
# 注：班级不存在时 class_id 为 None → SQL IS NULL → 空结果（fail-closed，行为正确）
```

模式B（学期过滤）：
```python
# 旧
query.where(semester_filter(
    CourseSession.semester_id, CourseSession.semester,
    get_current_semester_id(session), get_current_term(),
))
# 新
query.where(CourseSession.semester_id == get_current_semester_id(session))
```

- [ ] **Step 2: 两处直接字符串比较改 FK**（`crud/schedule.py:249`、`api/routes/checkin.py:349`）

```python
# crud/schedule.py:249
CourseSchedule.semester_id == get_current_semester_id(session)
# api/routes/checkin.py:349
CourseSession.semester_id == get_current_semester_id(session)
```

- [ ] **Step 3: 删除文件与 import**

```bash
git rm backend/app/core/transition_filters.py
grep -rn "transition_filters" backend/app --include="*.py"   # 期望：0 结果
```

- [ ] **Step 4: Commit**

```bash
git add -A backend/app
git commit -m "refactor(filters): pure-FK filters, remove transition_filters"
```

---

### Task 3: 写入路径 FK 化 + 展示路径 id→name 解析

**Files:**
- Modify: `backend/app/core/class_cache.py`（简单值缓存 + 批量解析）、`backend/app/core/term.py`（删 get_current_term）
- Modify: `backend/app/crud/course_session.py`、`checkin.py`、`question.py`、`schedule.py`、`group.py`、`group_score.py`、`student.py`
- Modify: `backend/app/api/routes/course_sessions.py`、`checkin.py`、`questions.py`、`schedules.py`、`groups.py`、`group_scores.py`、`term.py`

**Interfaces:**
- Produces:
  - `class_cache.get_class_name_by_id(session, class_id) -> Optional[str]`
  - `class_cache.get_class_names(session, class_ids: Iterable[int]) -> Dict[int, str]`（批量，简单值缓存）
  - `class_cache.get_class_id_by_name(session, class_name) -> Optional[int]`（保留）
  - API 响应 `class_name` 键 = `get_class_name_by_id(...)` 解析值；查询参数 `class_name` = `get_class_id_by_name(...)` 解析为过滤 id

- [ ] **Step 1: class_cache 重构（简单值缓存）**

```python
"""班级映射缓存 - class_id ↔ class_name（进程级简单值缓存）

只缓存简单值（字符串），不缓存 ORM 对象——避免跨 session 的 detached
对象属性刷新问题（与 term.py 缓存策略一致）。
"""
from typing import Dict, Iterable, Optional
from sqlmodel import Session, select

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


def get_class_names(session: Session, class_ids: Iterable[Optional[int]]) -> Dict[int, str]:
    """批量解析班级名（命中缓存跳过；未命中一次查询）"""
    ids = {i for i in class_ids if i is not None}
    missing = [i for i in ids if i not in _class_name_by_id]
    if missing:
        from app.models import Class_
        from sqlmodel import col
        for cls in session.exec(select(Class_).where(col(Class_.id).in_(missing))).all():
            _class_name_by_id[cls.id] = cls.name
            _class_id_by_name[cls.name] = cls.id
    return {i: _class_name_by_id[i] for i in ids if i in _class_name_by_id}


def get_class_id_by_name(session: Session, class_name: Optional[str]) -> Optional[int]:
    """按班级名解析 class_id（未分班/不存在返回 None）"""
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


def invalidate_class_cache() -> None:
    """清除班级映射缓存（班级创建/改名/删除后调用）"""
    _class_name_by_id.clear()
    _class_id_by_name.clear()
```

> `students.py` 转班端点原用 `get_class_by_id`（ORM 对象）取 `.id/.name/.cohort_year` → 改为直接 `session.get(Class_, body.class_id)`（单次管理操作，无需缓存）。

- [ ] **Step 2: 删除 term.py::get_current_term**

```python
# api/routes/term.py —— 用当前学期实体 label
sem = get_current_semester(session)
return {..., "term": sem.label if sem else "", ...}
# core/term.py —— 删除 get_current_term 与 _current_semester_label 的对外用途
```

- [ ] **Step 3: 写入路径只写 FK**

各 crud create 函数：删除 `class_name=` / `semester=` 赋值，只写 `class_id=` / `semester_id=`（`class_id` 由入参 class_name 经 `get_class_id_by_name` 解析；`semester_id` 由 `get_current_semester_id(session)` 取）。`_get_class_group_settings` 删除字符串回退分支（仅按复合主键查询）。

- [ ] **Step 4: 展示路径批量解析**

```python
# 例：课堂列表响应
name_map = get_class_names(session, (cs.class_id for cs in sessions))
...
{"class_name": name_map.get(cs.class_id), ...}
```

涉及：course_sessions（active/class 状态/历史）、checkin（列表/统计/代签）、questions（列表）、schedules（列表/today）、groups（列表/详情/我的小组）、group_scores（日志列表）。

- [ ] **Step 5: Commit**

```bash
git add -A backend/app
git commit -m "refactor(crud): FK-only writes + id->name resolution for display"
```

---

### Task 4: 测试适配（fixtures 与用例）

**Files:**
- Modify: `tests/conftest.py`、`tests/integration/conftest.py`、`tests/unit/test_semester_fields.py`、`tests/unit/test_semester_filter_crud.py`、`tests/unit/crud/test_*.py`、`tests/integration/test_*.py`（约 21 个文件 207 处）

**Interfaces:**
- Consumes: Task 1-3 产物
- Produces: 全量测试绿

- [ ] **Step 1: 提供测试辅助 fixture**（integration conftest）

```python
@pytest.fixture
def current_semester_id(test_engine):
    """seed 当前学期并返回 semester_id"""
    from datetime import date
    from app.models import Semester
    from app.core.term import invalidate_semester_cache
    with Session(_test_engine) as session:
        sem = session.exec(select(Semester).where(Semester.is_current.is_(True))).first()
        if sem is None:
            sem = Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                           total_weeks=20, is_current=True)
            session.add(sem)
            session.commit()
            session.refresh(sem)
        invalidate_semester_cache()
        return sem.id


@pytest.fixture
def class_ids(test_engine):
    """seed 一班/二班并返回 {name: id}"""
    from app.models import Class_
    with Session(_test_engine) as session:
        result = {}
        for name in ("一班", "二班", "三班"):
            cls = session.exec(select(Class_).where(Class_.name == name)).first()
            if cls is None:
                cls = Class_(name=name, cohort_year="2026")
                session.add(cls)
                session.commit()
                session.refresh(cls)
            result[name] = cls.id
        return result
```

- [ ] **Step 2: 批量替换测试构造**

```python
# 旧（业务表构造）
CourseSchedule(course_name="数学", class_name="1班", semester="2026-2027-1", ...)
# 新
CourseSchedule(course_name="数学", class_id=class_ids["1班"], semester_id=current_semester_id, ...)
```

逐文件处理 `class_name=` / `semester=` 构造（**排除** `Student(class_name=...)` 与 `CheckinRecord(student_name=...)`——这两者保留）。测试函数签名按需加 `current_semester_id` / `class_ids` fixture 参数。

- [ ] **Step 3: 更新过滤行为断言**（班级不存在 → 空结果，不再回退字符串）

- [ ] **Step 4: 全量测试绿**

Run: `conda run -n student-manage pytest tests/ -q`
Expected: 全 passed

- [ ] **Step 5: Commit**

```bash
git add -A tests
git commit -m "test: adapt fixtures to FK-only schema"
```

---

### Task 5: 全量回归（前后端）+ 合并推送

- [ ] **Step 1: 后端全量** `conda run -n student-manage pytest tests/ -q` → 全绿
- [ ] **Step 2: 前端全量**（契约未变，应无需改动）`cd frontend-v3 && pnpm test:run && pnpm exec vue-tsc --noEmit`
- [ ] **Step 3: 前端冒烟确认**（可选）：启动前后端，确认课堂/签到/小组页面正常显示班级名（由 FK 解析）
- [ ] **Step 4: finishing-a-development-branch 合并 main + 推送 GitHub**

---

## Self-Review

**Spec 覆盖检查**（对照 SEMESTER_COHORT_REFACTOR_PLAN）：
- ✅ Phase 4 步骤 5（业务表 class_name / semester 字符串列删除）→ Task 1
- ✅ §2.4 核心规则「过滤/JOIN 永远用 FK」→ Task 2（transition_filters 删除，31 处纯 FK）
- ✅ §七 P1「业务表冗余 class_name：当前规模无收益」→ 本计划即为删除该 P1 优化项（判定为不必要）
- ✅ §2.4 保留项（students.class_name/class_id/cohort_year、checkin student_name）→ 不删，Context 已列明
- ✅ 前端契约不变（响应 class_name 键由 FK 解析）→ 前端零改动，Task 5 验证

**占位符扫描**：无 TODO/TBD；迁移回填 SQL 与 class_cache 实现给出完整代码；`class_group_settings` 回退分支删除点明确。

**类型一致性**：`get_class_name_by_id` / `get_class_names` / `get_class_id_by_name` 在 Task 3 Step 1 定义，Step 4 展示路径与 Task 4 fixtures 使用同名同签名；`get_class_by_id` 被 `get_class_name_by_id` 取代（students.py 转班改 `session.get`）。

## 分支与执行顺序

- 分支 `feat/remove-string-columns`（从 main 切出，Task 1-5）
- Task 1-3 为后端连贯改动（中间态测试红属预期），Task 4 恢复全绿，Task 5 合并推送
- 完成后本仓库重构计划（Phase 0-5）全部收官
