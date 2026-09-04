# 第二学期 P0 实施计划：学期概念 + 数据归档 + 越权修复

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 引入学期（semester）概念实现上学期数据软归档与周次体系统一，并修复全部 P0 越权漏洞。

**Architecture:** 9 张业务表加 `semester TEXT` 列（模型层 `default_factory=get_current_term()` 自动填充，历史数据由 alembic 迁移回填 `'2025-2026-2'`）；新建 `app/core/term.py` 作为学期与周次的单一真源（收敛现存两处互相矛盾的硬编码实现）；CRUD 读取层统一按当前学期过滤；API 层补 RBAC 依赖修复越权；前端周次改为从 `GET /api/term/current` 获取。

**Tech Stack:** FastAPI + SQLModel + Alembic + PostgreSQL（开发/生产）/SQLite（测试内存库）、Vue 3 + TypeScript + TanStack Query、pytest + vitest。

**参考设计文档:** `docs/superpowers/specs/2026-09-04-semester-archive-p0-design.md`

**测试环境要求（CLAUDE.md 强制）:**
- Python: `conda run -n student-manage python ...` 或已激活 `student-manage` 环境
- 后端测试在项目根目录运行: `pytest tests/... -v`
- 前端测试在 `frontend-v3/` 目录运行: `pnpm test:run`（跑全部）或 `pnpm vitest run <file>`（单文件）

---

## 文件结构

**新建文件：**

| 文件 | 职责 |
|------|------|
| `backend/app/core/term.py` | 学期上下文单一真源：当前学期标识、周次计算 |
| `backend/app/api/routes/term.py` | `GET /api/term/current` 接口 |
| `backend/alembic/versions/<rev>_add_semester_fields.py` | 加 semester 列 + 回填 + 索引 + 部分唯一索引重建 |
| `backend/scripts/semester_rollover.py` | 学期切换脚本（备份/收敛/分数归档/软禁用） |
| `backend/tests/unit/test_term.py` | 周次计算单元测试 |
| `backend/tests/unit/test_semester_fields.py` | 模型 semester 默认填充测试 |
| `backend/tests/unit/test_semester_rollover.py` | 切换脚本幂等性测试 |
| `backend/tests/integration/test_term_api.py` | term API + 跨学期隔离集成测试 |
| `backend/tests/integration/test_authorization_negative.py` | 越权负向测试 |
| `frontend-v3/src/api/term.ts` | 前端 term API 客户端 |
| `frontend-v3/src/composables/useTermInfo.ts` | term 信息 composable |
| `frontend-v3/test/date.term.test.ts` | 前端周次计算新用例 |

**修改文件：**

| 文件 | 修改 |
|------|------|
| `backend/app/core/config.py` | 加 TermSettings（TERM__LABEL/START_DATE/TOTAL_WEEKS） |
| `backend/app/models/course_schedule.py` | CourseSchedule 加 semester |
| `backend/app/models/course_session.py` | CourseSession/ScheduleAdjustment 加 semester + 部分唯一索引重建 |
| `backend/app/models/checkin.py` | CheckinRecord/ScoreLog 加 semester |
| `backend/app/models/group.py` | Group/GroupTask/GroupEvaluationScore 加 semester |
| `backend/app/models/question.py` | Question 加 semester |
| `backend/app/api/deps.py` | 加 verify_teacher_class_access 辅助函数 |
| `backend/app/api/routes/schedules.py` | 删除硬编码周次，改 import term.py |
| `backend/app/api/routes/course_sessions.py` | 同上 |
| `backend/app/api/routes/schedule_adjustments.py` | 周次校验 1-20 → 配置化 |
| `backend/app/api/routes/students.py` | 越权修复（改分/添加/详情/分数历史） |
| `backend/app/api/routes/checkin.py` | 越权修复（签到系列 + active sessions） |
| `backend/app/api/routes/lost_found.py` | 越权修复（publisher_id 校验） |
| `backend/app/crud/schedule.py` | 查询/查重加学期过滤 |
| `backend/app/crud/course_session.py` | 查询加学期过滤 |
| `backend/app/crud/checkin.py` | 查询加学期过滤 |
| `backend/app/crud/group.py` | 查询加学期过滤 |
| `backend/app/crud/group_task.py` | 查询加学期过滤 |
| `backend/app/crud/question.py` | 查询加学期过滤 |
| `backend/main.py` | 注册 term_router |
| `frontend-v3/src/lib/date.ts` | getCurrentWeek 改为学期基准参数化 |
| `frontend-v3/src/views/teacher/Schedules.vue` | 周次来源改 useTermInfo |
| `frontend-v3/src/composables/useCourseSessions.ts` | 修复失效 key bug |

---

## Phase 1：学期配置与周次统一

### Task 1: TermSettings 配置项

**Files:**
- Modify: `backend/app/core/config.py`（import 区与 Settings 类）
- Test: `backend/tests/unit/test_term_settings.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/unit/test_term_settings.py`：

```python
"""TermSettings 配置测试"""
from datetime import date
from app.core.config import TermSettings


def test_term_settings_defaults():
    """默认值为第二学期 2026-2027-1（2026-09-07 开学，20 周）"""
    settings = TermSettings()
    assert settings.label == "2026-2027-1"
    assert settings.start_date == date(2026, 9, 7)
    assert settings.total_weeks == 20


def test_term_settings_env_override(monkeypatch):
    """环境变量 TERM__LABEL 等可覆盖默认值"""
    monkeypatch.setenv("TERM__LABEL", "2027-2028-1")
    monkeypatch.setenv("TERM__START_DATE", "2027-09-06")
    monkeypatch.setenv("TERM__TOTAL_WEEKS", "21")
    settings = TermSettings()
    assert settings.label == "2027-2028-1"
    assert settings.start_date == date(2027, 9, 6)
    assert settings.total_weeks == 21
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_term_settings.py -v`
Expected: FAIL — `ImportError: cannot import name 'TermSettings'`

- [ ] **Step 3: 实现 TermSettings**

`backend/app/core/config.py` 顶部 import 区（第 4 行附近）加 date 导入：

```python
from datetime import date
```

在 `UploadSettings` 类之后（第 175 行后）、`Settings` 主类之前插入：

```python
class TermSettings(BaseSettings):
    """学期配置 - 第二学期引入（semester 软归档 + 周次统一基准）"""
    model_config = SettingsConfigDict(env_prefix="TERM_")

    label: str = Field(default="2026-2027-1", description="当前学期标识（学年+学期号：1=秋季 2=春季）")
    start_date: date = Field(default=date(2026, 9, 7), description="学期开始日期（第1周周一）")
    total_weeks: int = Field(default=20, description="学期总周数")
```

`Settings` 主类（第 194 行 upload 之后）加一行：

```python
    term: TermSettings = Field(default_factory=TermSettings)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_term_settings.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/config.py backend/tests/unit/test_term_settings.py
git commit -m "feat(term): add TermSettings config for semester context"
```

### Task 2: core/term.py 学期上下文模块

**Files:**
- Create: `backend/app/core/term.py`
- Test: `backend/tests/unit/test_term.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/unit/test_term.py`：

```python
"""学期上下文工具测试 - 周次计算单一真源"""
from datetime import date
from app.core.term import (
    get_current_term,
    get_term_start_date,
    get_term_total_weeks,
    get_current_week_number,
    get_week_number_for_date,
)


def test_get_current_term():
    assert get_current_term() == "2026-2027-1"


def test_get_term_start_date():
    assert get_term_start_date() == date(2026, 9, 7)


def test_get_term_total_weeks():
    assert get_term_total_weeks() == 20


def test_week_before_term_start_returns_0():
    """开学前返回 0（前端显示未开学）"""
    assert get_current_week_number(today=date(2026, 9, 4)) == 0


def test_week_first_week_boundaries():
    """第 1 周：周一到周日"""
    assert get_current_week_number(today=date(2026, 9, 7)) == 1
    assert get_current_week_number(today=date(2026, 9, 13)) == 1


def test_week_second_week():
    assert get_current_week_number(today=date(2026, 9, 14)) == 2


def test_week_caps_at_total_weeks():
    """超过总周数返回总周数（学期末不会无限增长）"""
    assert get_current_week_number(today=date(2027, 1, 25)) == 20


def test_get_week_number_for_date_before_term():
    """指定日期周次计算：开学前返回 0"""
    assert get_week_number_for_date(date(2026, 9, 5)) == 0


def test_get_week_number_for_date_during_term():
    assert get_week_number_for_date(date(2026, 9, 21)) == 3
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_term.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.core.term'`

- [ ] **Step 3: 实现 term.py**

创建 `backend/app/core/term.py`：

```python
"""
学期上下文工具 - 单一真源

第二学期引入：集中管理学期标识与教学周次计算，
替代此前散落在 schedules.py / course_sessions.py / 前端 date.ts
中互相矛盾的硬编码周次实现。
"""
from datetime import date, datetime
from typing import Optional

from app.core.config import get_settings


def get_current_term() -> str:
    """获取当前学期标识（如 '2026-2027-1'）"""
    return get_settings().term.label


def get_term_start_date() -> date:
    """获取当前学期开始日期（第 1 周周一）"""
    return get_settings().term.start_date


def get_term_total_weeks() -> int:
    """获取当前学期总周数"""
    return get_settings().term.total_weeks


def get_current_week_number(
    today: Optional[date] = None,
    total_weeks: Optional[int] = None,
) -> int:
    """计算当前教学周次。

    以学期开始日期（周一）为基准：
    - 开学前返回 0（前端显示"未开学"）
    - 学期中返回 1..total_weeks
    - 超过总周数返回 total_weeks

    Args:
        today: 指定日期（测试用），默认今天
        total_weeks: 周数上限，默认取配置 TERM__TOTAL_WEEKS
    """
    if today is None:
        today = datetime.now().date()
    if total_weeks is None:
        total_weeks = get_term_total_weeks()

    start = get_term_start_date()
    if today < start:
        return 0

    days_since_start = (today - start).days
    week = days_since_start // 7 + 1
    return min(week, total_weeks)


def get_week_number_for_date(target_date: date) -> int:
    """计算指定日期所在的教学周次（开学前返回 0）"""
    return get_current_week_number(today=target_date)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_term.py -v`
Expected: PASS（9 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/core/term.py backend/tests/unit/test_term.py
git commit -m "feat(term): add term context module as single source of week calculation"
```

### Task 3: 收敛周次计算副本 + 调课周次校验配置化

**Files:**
- Modify: `backend/app/api/routes/schedules.py:35-58`（删除硬编码实现，改 import）
- Modify: `backend/app/api/routes/course_sessions.py:251-261`（同上）
- Modify: `backend/app/api/routes/schedule_adjustments.py:57-60`（周次上限配置化）

- [ ] **Step 1: 修改 schedules.py**

删除 `backend/app/api/routes/schedules.py` 第 35-58 行的两个本地函数
（`_get_current_week_number` 与 `_get_week_number_for_date` 的全部实现体），
在文件顶部 import 区（第 31 行 `router = APIRouter(...)` 之前）添加：

```python
from app.core.term import (
    get_current_week_number as _get_current_week_number,
    get_week_number_for_date as _get_week_number_for_date,
)
```

说明：用别名保持文件内所有既有调用点（`_get_current_week_number()`、
`_get_week_number_for_date(...)`）无需改动，实现收敛到 term.py。

- [ ] **Step 2: 修改 course_sessions.py**

删除 `backend/app/api/routes/course_sessions.py` 第 251-261 行的本地
`_get_current_week_number` 实现，在文件顶部 import 区添加：

```python
from app.core.term import get_current_week_number as _get_current_week_number
```

- [ ] **Step 3: 修改 schedule_adjustments.py 周次校验**

`backend/app/api/routes/schedule_adjustments.py` 第 57-60 行现为：

```python
    if data.week_number < 1 or data.week_number > 20:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="周次必须在 1-20 范围内"
        )
```

改为：

```python
    from app.core.term import get_term_total_weeks
    total_weeks = get_term_total_weeks()
    if data.week_number < 1 or data.week_number > total_weeks:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"周次必须在 1-{total_weeks} 范围内"
        )
```

- [ ] **Step 4: 回归验证**

Run: `conda run -n student-manage pytest tests/integration/test_schedule_api.py tests/integration/test_schedule_adjustment_api.py tests/integration/test_schedule_consistency.py tests/integration/test_course_session_api.py -v`
Expected: PASS（全部通过；周次行为由 term.py 单测保证）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/schedules.py backend/app/api/routes/course_sessions.py backend/app/api/routes/schedule_adjustments.py
git commit -m "refactor(term): converge hardcoded week calculation to core/term.py"
```

---

## Phase 2：数据模型与迁移

### Task 4: 9 张表模型加 semester 字段 + 部分唯一索引重建

**Files:**
- Modify: `backend/app/models/course_schedule.py`
- Modify: `backend/app/models/course_session.py`
- Modify: `backend/app/models/checkin.py`
- Modify: `backend/app/models/group.py`
- Modify: `backend/app/models/question.py`
- Test: `backend/tests/unit/test_semester_fields.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/unit/test_semester_fields.py`：

```python
"""semester 字段测试：默认自动填充当前学期，可显式指定"""
from app.models import (
    CourseSchedule, CourseSession, ScheduleAdjustment,
    CheckinRecord, ScoreLog,
    Group, GroupTask, GroupEvaluationScore,
)
from app.models.question import Question


def test_semester_default_fills_current_term():
    """不显式指定时，创建对象自动带当前学期标识"""
    sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                          start_time="08:00", end_time="09:40")
    assert sched.semester == "2026-2027-1"

    sess = CourseSession(session_code="TEST001", class_name="1班", teacher_id=1)
    assert sess.semester == "2026-2027-1"

    adj = ScheduleAdjustment(schedule_id=1, week_number=1, type="cancel", created_by=1)
    assert adj.semester == "2026-2027-1"

    checkin = CheckinRecord(student_id="TEST001")
    assert checkin.semester == "2026-2027-1"

    log = ScoreLog(student_id="TEST001", old_score=80.0, new_score=90.0, delta=10.0)
    assert log.semester == "2026-2027-1"

    group = Group(class_name="1班", name="第一组", leader_student_id="TEST001")
    assert group.semester == "2026-2027-1"

    task = GroupTask(class_name="1班", title="小组作业", created_by="teacher1")
    assert task.semester == "2026-2027-1"

    score = GroupEvaluationScore(task_id=1, target_group_id=1, evaluator_type="teacher",
                                 evaluator_id="teacher1", dimension_id=1, score=90)
    assert score.semester == "2026-2027-1"

    question = Question(teacher_id=1, content="今天讲了什么？")
    assert question.semester == "2026-2027-1"


def test_semester_explicit_override():
    """显式指定 semester 时保留指定值（归档脚本回填历史用）"""
    sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                          start_time="08:00", end_time="09:40", semester="2025-2026-2")
    assert sched.semester == "2025-2026-2"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_semester_fields.py -v`
Expected: FAIL — 模型构造报错或 `semester` 为 None

- [ ] **Step 3: 模型加 semester 字段**

`backend/app/models/course_schedule.py`：CourseSchedule 表类加字段（import 区加
`from app.core.term import get_current_term`）：

```python
    semester: Optional[str] = Field(
        default_factory=get_current_term,
        description="学期标识（如 2026-2027-1）",
        max_length=20,
        index=True
    )
```

`backend/app/models/course_session.py`：CourseSession 与 ScheduleAdjustment 表类加同上字段。
同时 CourseSession 的 `__table_args__` 部分唯一索引重建（第 36-42 行）：

```python
        # 同一班级同一学期在同一时间只能有一个活跃课堂（第二学期：加 semester 维度）
        Index(
            'uix_active_class_semester',
            'class_name',
            'semester',
            unique=True,
            sqlite_where=text('status="active"'),
            postgresql_where=text("status='active'")
        ),
```

`backend/app/models/checkin.py`：CheckinRecord 与 ScoreLog 表类加同上字段。
`backend/app/models/group.py`：Group、GroupTask、GroupEvaluationScore 表类加同上字段。
`backend/app/models/question.py`：Question 表类加同上字段（import 区加 term import）。

注意：字段只加在**表类**上（如 `CourseSchedule`），不加在响应模型（如 `CourseScheduleResponse`）上——前端无感知。

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_semester_fields.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 全量单元测试回归（模型改动影响面大）**

Run: `conda run -n student-manage pytest tests/unit -v`
Expected: PASS（全部通过；若有失败先检查是否因索引名变化导致，修复后重跑）

- [ ] **Step 6: 提交**

```bash
git add backend/app/models/course_schedule.py backend/app/models/course_session.py backend/app/models/checkin.py backend/app/models/group.py backend/app/models/question.py backend/tests/unit/test_semester_fields.py
git commit -m "feat(term): add semester column to 9 business tables"
```

### Task 5: alembic 迁移（加列 + 回填 + 索引 + 唯一索引重建）

**Files:**
- Create: `backend/alembic/versions/<timestamp>_add_semester_fields.py`

- [ ] **Step 1: 生成迁移骨架**

Run: `cd backend && conda run -n student-manage alembic revision -m "add semester fields" --rev-id $(date +%Y%m%d_%H%M%S | sed 's/_//g')_add_semester_fields`
Expected: 生成新文件 `backend/alembic/versions/<rev>_add_semester_fields.py`

- [ ] **Step 2: 编写迁移内容**

替换生成文件内容为：

```python
"""add semester fields

Revision ID: <rev>
Revises: 8d7a9e6f9898
Create Date: <生成时间>
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '<rev>'
down_revision: Union[str, Sequence[str], None] = '8d7a9e6f9898'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 上学期（第一学期）标识，历史数据统一回填
PREVIOUS_TERM = '2025-2026-2'

# 需要加 semester 列的表
SEMESTER_TABLES = [
    'course_schedules',
    'course_sessions',
    'schedule_adjustments',
    'checkin_records',
    'score_logs',
    'groups',
    'group_tasks',
    'group_evaluation_scores',
    'questions',
]


def upgrade() -> None:
    """加 semester 列 + 回填历史数据 + 建索引 + 重建活跃课堂唯一索引"""
    for table in SEMESTER_TABLES:
        op.add_column(table, sa.Column('semester', sa.String(length=20), nullable=True))
        # 历史数据回填上学期
        op.execute(f"UPDATE {table} SET semester = '{PREVIOUS_TERM}'")
        # 学期过滤索引
        op.create_index(f'ix_{table}_semester', table, ['semester'], unique=False)

    # course_sessions 部分唯一索引重建：加入 semester 维度
    # （旧的 uix_active_class_name 不含学期，会卡住新学期开课）
    op.drop_index('uix_active_class_name', table_name='course_sessions')
    op.create_index(
        'uix_active_class_semester',
        'course_sessions',
        ['class_name', 'semester'],
        unique=True,
        sqlite_where=sa.text('status="active"'),
        postgresql_where=sa.text("status='active'"),
    )


def downgrade() -> None:
    """回滚：删索引、删列"""
    op.drop_index('uix_active_class_semester', table_name='course_sessions')
    op.create_index(
        'uix_active_class_name',
        'course_sessions',
        ['class_name'],
        unique=True,
        sqlite_where=sa.text('status="active"'),
        postgresql_where=sa.text("status='active'"),
    )
    for table in reversed(SEMESTER_TABLES):
        op.drop_index(f'ix_{table}_semester', table_name=table)
        op.drop_column(table, 'semester')
```

- [ ] **Step 3: 在开发 PostgreSQL 上应用并验证**

先确认本地 PG 状态并启动（CLAUDE.md 服务重启流程）：
```bash
pg_isready -h localhost -p 5432 || sudo service postgresql start
```

Run: `cd backend && conda run -n student-manage alembic upgrade head`
Expected: 迁移成功，无报错

验证回填与索引：
```bash
cd backend && conda run -n student-manage python -c "
import psycopg2
conn = psycopg2.connect('postgresql://yufeng:yufeng@localhost:5432/classhub')
cur = conn.cursor()
cur.execute(\"SELECT semester, COUNT(*) FROM course_schedules GROUP BY semester\")
print('course_schedules:', cur.fetchall())
cur.execute(\"SELECT indexname FROM pg_indexes WHERE tablename='course_sessions'\")
print('course_sessions indexes:', cur.fetchall())
conn.close()
"
```
Expected: 课表全部回填 `('2025-2026-2', N)`；索引含 `uix_active_class_semester` 且无 `uix_active_class_name`

- [ ] **Step 4: 提交**

```bash
git add backend/alembic/versions/
git commit -m "feat(term): add semester columns migration with backfill and index rebuild"
```

---

## Phase 3：CRUD 学期过滤

### Task 6: 读取侧按当前学期过滤

**Files:**
- Modify: `backend/app/crud/schedule.py`
- Modify: `backend/app/crud/course_session.py`
- Modify: `backend/app/crud/checkin.py`
- Modify: `backend/app/crud/group.py`
- Modify: `backend/app/crud/group_task.py`
- Modify: `backend/app/crud/question.py`

- [ ] **Step 1: 写失败测试（跨学期隔离）**

创建 `backend/tests/unit/test_semester_filter_crud.py`：

```python
"""CRUD 学期过滤测试：上学期数据不出现在当前学期查询中"""
from datetime import datetime
import pytest
from sqlmodel import Session, select

from app.models import CourseSchedule, CourseSession, CheckinRecord, ScoreLog
from app.models import Group, GroupTask, Question
from app.crud.schedule import get_schedules
from app.crud.course_session import get_teacher_course_sessions
from app.crud.checkin import get_all_checkins, get_student_score_logs
from app.crud.group import get_groups_by_class
from app.crud.group_task import get_group_tasks_by_class
from app.crud.question import get_questions_by_class


@pytest.fixture
def two_term_data(session: Session):
    """造数据：上学期 + 当前学期各一批"""
    # 上学期课表/课堂/签到/日志/小组/任务/问答
    old_sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                               start_time="08:00", end_time="09:40", semester="2025-2026-2")
    new_sched = CourseSchedule(course_name="数学", class_name="1班", day_of_week=1,
                               start_time="08:00", end_time="09:40", semester="2026-2027-1")
    session.add_all([old_sched, new_sched])
    session.commit()

    old_session = CourseSession(session_code="OLD001", class_name="1班", teacher_id=1,
                                semester="2025-2026-2", status="ended")
    new_session = CourseSession(session_code="NEW001", class_name="1班", teacher_id=1,
                                semester="2026-2027-1", status="ended")
    session.add_all([old_session, new_session])
    session.commit()

    old_checkin = CheckinRecord(student_id="TEST001", session_id=old_session.id,
                                checkin_time=datetime(2026, 3, 1), semester="2025-2026-2")
    new_checkin = CheckinRecord(student_id="TEST001", session_id=new_session.id,
                                checkin_time=datetime(2026, 9, 10), semester="2026-2027-1")
    session.add_all([old_checkin, new_checkin])

    old_log = ScoreLog(student_id="TEST001", old_score=80.0, new_score=90.0, delta=10.0,
                       semester="2025-2026-2")
    new_log = ScoreLog(student_id="TEST001", old_score=90.0, new_score=95.0, delta=5.0,
                       semester="2026-2027-1")
    session.add_all([old_log, new_log])

    old_group = Group(class_name="1班", name="上学期的组", leader_student_id="TEST001",
                      semester="2025-2026-2", is_active=True)
    new_group = Group(class_name="1班", name="新学期的组", leader_student_id="TEST001",
                      semester="2026-2027-1", is_active=True)
    session.add_all([old_group, new_group])

    old_task = GroupTask(class_name="1班", title="上学期任务", created_by="teacher1",
                         semester="2025-2026-2")
    new_task = GroupTask(class_name="1班", title="新学期任务", created_by="teacher1",
                         semester="2026-2027-1")
    session.add_all([old_task, new_task])

    old_q = Question(teacher_id=1, class_name="1班", content="上学期问题", semester="2025-2026-2")
    new_q = Question(teacher_id=1, class_name="1班", content="新学期问题", semester="2026-2027-1")
    session.add_all([old_q, new_q])
    session.commit()
    return session


def test_schedules_filtered_by_current_term(two_term_data):
    schedules = get_schedules(two_term_data)
    assert len(schedules) == 1
    assert schedules[0].semester == "2026-2027-1"


def test_teacher_sessions_filtered_by_current_term(two_term_data):
    sessions = get_teacher_course_sessions(two_term_data, teacher_id=1)
    assert len(sessions) == 1
    assert sessions[0].semester == "2026-2027-1"


def test_checkins_filtered_by_current_term(two_term_data):
    checkins = get_all_checkins(two_term_data)
    assert len(checkins) == 1
    assert checkins[0].semester == "2026-2027-1"


def test_score_logs_filtered_by_current_term(two_term_data):
    logs = get_student_score_logs(two_term_data, "TEST001")
    assert len(logs) == 1
    assert logs[0].semester == "2026-2027-1"


def test_groups_filtered_by_current_term(two_term_data):
    groups = get_groups_by_class(two_term_data, "1班")
    assert len(groups) == 1
    assert groups[0].semester == "2026-2027-1"


def test_group_tasks_filtered_by_current_term(two_term_data):
    tasks = get_group_tasks_by_class(two_term_data, "1班")
    assert len(tasks) == 1
    assert tasks[0].semester == "2026-2027-1"


def test_questions_filtered_by_current_term(two_term_data):
    questions = get_questions_by_class(two_term_data, "1班")
    assert len(questions) == 1
    assert questions[0].semester == "2026-2027-1"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_semester_filter_crud.py -v`
Expected: FAIL — 各查询返回 2 条（上学期数据未过滤）

- [ ] **Step 3: 修改 CRUD 读取函数**

`backend/app/crud/schedule.py`（import 区加 `from app.core.term import get_current_term`）：

`get_schedules`（第 17-32 行）`query = select(CourseSchedule)` 改为：

```python
    query = select(CourseSchedule).where(CourseSchedule.semester == get_current_term())
```

`backend/app/crud/course_session.py`：给以下函数的 `select(CourseSchedule.../CourseSession...)` 基础查询加
`.where(CourseSession.semester == get_current_term())`：
- `get_active_course_session_by_class_name`（第 27 行）
- `get_teacher_active_course_sessions`（第 36 行）
- `get_teacher_scheduled_course_sessions`（第 45 行）
- `get_teacher_course_sessions`（第 127 行）

`backend/app/crud/checkin.py`：
- `get_all_checkins`（第 19 行）：

```python
    query = (
        select(CheckinRecord)
        .where(CheckinRecord.semester == get_current_term())
        .order_by(CheckinRecord.checkin_time.desc())
        .limit(limit)
    )
```

- `get_today_checkins`（第 34 行）加：

```python
    query = select(CheckinRecord).where(
        CheckinRecord.checkin_time >= query_start,
        CheckinRecord.semester == get_current_term(),
    )
```

- `count_today_checkins`（第 46 行）where 加 `CheckinRecord.semester == get_current_term()`：

```python
    query = select(func.count()).select_from(CheckinRecord).where(
        CheckinRecord.checkin_time >= today_start,
        CheckinRecord.semester == get_current_term(),
    )
```

- `get_student_score_logs`（第 142 行）：

```python
    query = (
        select(ScoreLog)
        .where(
            ScoreLog.student_id == student_id,
            ScoreLog.semester == get_current_term(),
        )
        .order_by(ScoreLog.created_at.desc())
    )
```

`backend/app/crud/group.py`：`get_groups_by_class`（第 17-21 行）与
`get_student_active_group`（第 24-35 行）的 where 条件加 `Group.semester == get_current_term()`：

```python
def get_groups_by_class(session: Session, class_name: str) -> List[Group]:
    """获取某班当前学期所有活跃小组"""
    return session.exec(
        select(Group).where(
            Group.class_name == class_name,
            Group.is_active.is_(True),
            Group.semester == get_current_term(),
        ).order_by(Group.id)
    ).all()
```

`backend/app/crud/group_task.py`：
- `get_group_tasks_by_class`（第 75-77 行）加 `GroupTask.semester == get_current_term()`
- `start_group_task`（第 94 行）的 `select(Group).where(...)` 加 `Group.semester == get_current_term()`
- `get_task_results`（第 281、293 行）的 `select(Group).where(...)` 加 `Group.semester == get_current_term()`

`backend/app/crud/question.py`：
- `get_questions_by_teacher`（第 43 行）加 `.where(Question.semester == get_current_term())`
- `get_questions_by_class`（第 58 行）where 条件加 `Question.semester == get_current_term()`：

```python
    query = select(Question).where(
        ((Question.class_name == class_name) | (Question.class_name.is_(None))),
        Question.semester == get_current_term(),
    )
```

`backend/app/api/routes/groups.py` 的 `_check_class_not_evaluating`（第 84-92 行）——
互斥检查直接 select 不走 CRUD，需单独加学期条件（否则上学期遗留
evaluating 任务仍会卡死新学期组队）：

```python
    evaluating_task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == class_name,
            GroupTask.status == "evaluating",
            GroupTask.semester == get_current_term(),
        )
    ).first()
```

注意各文件顶部 import 区加 `from app.core.term import get_current_term`。

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_semester_filter_crud.py -v`
Expected: PASS（7 passed）

- [ ] **Step 5: 全量单元测试回归**

Run: `conda run -n student-manage pytest tests/unit -v`
Expected: PASS（全部通过。若有失败：多为测试数据 fixture 需带 semester 或查询预期条数变化，逐个修复后重跑）

- [ ] **Step 6: 提交**

```bash
git add backend/app/crud/ backend/tests/unit/test_semester_filter_crud.py
git commit -m "feat(term): filter current-term data in CRUD read layer"
```

### Task 7: 课表导入查重键加 semester

**Files:**
- Modify: `backend/app/crud/schedule.py:220-236`
- Test: `backend/tests/integration/test_schedule_api.py`（追加用例）

- [ ] **Step 1: 写失败测试**

在 `backend/tests/integration/test_schedule_api.py` 末尾追加：

```python
def test_import_schedule_dup_key_ignores_previous_term(client, admin_headers):
    """上学期同课程/教师/时段不应阻止新学期导入"""
    from app.models import CourseSchedule

    # 先手工造一条上学期的同键课表
    from sqlmodel import Session
    from app.core.db import engine
    with Session(engine) as session:
        session.add(CourseSchedule(
            course_name="高等数学", class_name="1班", teacher_name="张老师",
            day_of_week=1, start_time="08:00", end_time="09:40",
            week_start=1, week_end=20, semester="2025-2026-2",
        ))
        session.commit()

    # 新学期导入同键课表（应成功而非"课程已存在"）
    import io
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["course_name", "class_name", "teacher_name", "day_of_week",
               "start_time", "end_time", "week_start", "week_end"])
    ws.append(["高等数学", "1班", "张老师", 1, "08:00", "09:40", 1, 20])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    resp = client.post(
        "/api/v1/schedules/import",
        files={"file": ("schedules.xlsx", buf,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert "成功" in resp.json().get("message", "") or resp.json().get("success")
```

（若现有测试文件的 fixture 名与 Excel 构造方式不同，按该文件现有模式适配。）

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_schedule_api.py::test_import_schedule_dup_key_ignores_previous_term -v`
Expected: FAIL — 返回"课程已存在"

- [ ] **Step 3: 修改查重键**

`backend/app/crud/schedule.py` 第 220-228 行的查重查询加 semester 条件：

```python
            # 查重检查（仅当前学期内查重，允许新学期导入与上学期相同的课程）
            existing = session.exec(
                select(CourseSchedule).where(
                    CourseSchedule.course_name == course_name,
                    CourseSchedule.class_name == class_name,
                    CourseSchedule.teacher_name == teacher_name,
                    CourseSchedule.day_of_week == day_of_week,
                    CourseSchedule.start_time == start_time,
                    CourseSchedule.semester == get_current_term(),
                )
            ).first()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_schedule_api.py -v`
Expected: PASS（全部通过）

- [ ] **Step 5: 提交**

```bash
git add backend/app/crud/schedule.py backend/tests/integration/test_schedule_api.py
git commit -m "feat(term): scope schedule import dedup check to current term"
```

---

## Phase 4：API 层（term 接口 + 越权修复）

### Task 8: GET /api/term/current 接口

**Files:**
- Create: `backend/app/api/routes/term.py`
- Modify: `backend/main.py:196`（注册 router）
- Test: `backend/tests/integration/test_term_api.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/integration/test_term_api.py`：

```python
"""term API 集成测试"""
from datetime import date


def test_get_current_term_info(client):
    """返回当前学期标识、开始日期、当前周次、总周数"""
    resp = client.get("/api/v1/term/current")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["term"] == "2026-2027-1"
    assert data["start_date"] == "2026-09-07"
    assert data["total_weeks"] == 20
    # current_week: 0..total_weeks 范围内（取决于运行当天，不再要求具体值）
    assert 0 <= data["current_week"] <= 20
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_term_api.py -v`
Expected: FAIL — 404（路由不存在）

- [ ] **Step 3: 实现路由**

创建 `backend/app/api/routes/term.py`：

```python
"""
学期信息 API - 前端周次计算基准来源
"""
from fastapi import APIRouter

from app.core.term import (
    get_current_term,
    get_term_start_date,
    get_term_total_weeks,
    get_current_week_number,
)
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["term"])


@router.get("/term/current", response_model=ApiResponse[dict])
def get_current_term_info():
    """获取当前学期信息（无认证，前端登录前亦需使用）"""
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "term": get_current_term(),
            "start_date": get_term_start_date().isoformat(),
            "current_week": get_current_week_number(),
            "total_weeks": get_term_total_weeks(),
        }
    }
```

`backend/main.py` 注册（在 196 行 lost_found 之后）：

```python
    from app.api.routes.term import router as term_router
    app.include_router(term_router, prefix=API_V1_PREFIX)
```

（main.py 已有 import 区可合并放置；遵循现有 import 风格。）

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_term_api.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/term.py backend/main.py backend/tests/integration/test_term_api.py
git commit -m "feat(term): add GET /api/term/current endpoint"
```

### Task 9: deps.py 教师班级访问校验辅助函数

**Files:**
- Modify: `backend/app/api/deps.py`
- Test: `backend/tests/unit/test_deps_teacher_class.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/unit/test_deps_teacher_class.py`：

```python
"""verify_teacher_class_access 测试"""
import pytest
from fastapi import HTTPException
from app.api.deps import verify_teacher_class_access


def test_admin_always_allowed(session):
    user = {"sub": "1", "role": "admin", "is_admin": True}
    # admin 不抛异常即为通过
    verify_teacher_class_access(user, "1班", session)


def test_teacher_allowed_for_assigned_class(session):
    from app.models import User
    from app.core.security import hash_password
    teacher = User(username="t1", name="教师1", role="teacher",
                   assigned_classes='["1班", "2班"]',
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    session.add(teacher)
    session.commit()
    user = {"sub": str(teacher.id), "role": "teacher"}
    verify_teacher_class_access(user, "1班", session)


def test_teacher_denied_for_unassigned_class(session):
    from app.models import User
    from app.core.security import hash_password
    teacher = User(username="t1", name="教师1", role="teacher",
                   assigned_classes='["1班"]',
                   password_hash=hash_password("pass123"),
                   is_account_enabled=True)
    session.add(teacher)
    session.commit()
    user = {"sub": str(teacher.id), "role": "teacher"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, "2班", session)
    assert exc_info.value.status_code == 403


def test_student_denied(session):
    user = {"sub": "TEST001", "role": "student"}
    with pytest.raises(HTTPException) as exc_info:
        verify_teacher_class_access(user, "1班", session)
    assert exc_info.value.status_code == 403
```

（User 模型字段名若与上述不符，按 `backend/app/models/user.py` 实际定义调整。）

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_deps_teacher_class.py -v`
Expected: FAIL — `ImportError: cannot import name 'verify_teacher_class_access'`

- [ ] **Step 3: 实现辅助函数**

`backend/app/api/deps.py` 末尾追加（顶部 import 区加 `from sqlmodel import Session`）：

```python
def verify_teacher_class_access(user: dict, class_name: str, session: Session) -> None:
    """校验教师是否有权操作指定班级（admin 放行，teacher 校验 assigned_classes）

    Args:
        user: get_current_user 返回的 JWT claims dict
        class_name: 目标班级名
        session: 数据库会话

    Raises:
        HTTPException 403: 无权限
    """
    from app.models import User

    role = user.get("role", "")
    if role == "admin":
        return
    if role != "teacher":
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="需要管理员或教师权限")

    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无效的用户信息")

    user_obj = session.get(User, int(user_id))
    assigned = user_obj.get_assigned_classes() if user_obj else []
    if class_name not in assigned:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权操作该班级")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_deps_teacher_class.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/deps.py backend/tests/unit/test_deps_teacher_class.py
git commit -m "feat(auth): add verify_teacher_class_access helper for RBAC"
```

### Task 10: students 路由越权修复

**Files:**
- Modify: `backend/app/api/routes/students.py:165-244, 363-378`

- [ ] **Step 1: 写失败测试（负向测试）**

创建 `backend/tests/integration/test_authorization_negative.py`：

```python
"""越权负向测试：未授权角色调用敏感接口必须 403"""
import pytest


def test_student_cannot_update_score(client, student_token, other_student_id):
    """学生不能修改任意学生（含他人和自己）的分数"""
    resp = client.put(
        f"/api/v1/students/{other_student_id}/score",
        json={"score_change": 10, "reason": "越权测试"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403


def test_student_cannot_add_student(client, student_token):
    resp = client.post(
        "/api/v1/students",
        json={"student_id": "HACK001", "name": "越权学生", "class_name": "1班"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403


def test_teacher_cannot_view_other_class_student(client, teacher_token, other_class_student_id):
    """教师不能查看非负责班级的学生详情"""
    resp = client.get(
        f"/api/v1/students/{other_class_student_id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert resp.status_code == 403


def test_student_detail_has_no_password_hash(client, admin_token, student_id):
    """学生详情响应不含 password_hash"""
    resp = client.get(
        f"/api/v1/students/{student_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert "password_hash" not in resp.json()["data"]


def test_student_cannot_read_other_student_scores(client, student_token, other_student_id):
    resp = client.get(
        f"/api/v1/students/{other_student_id}/scores",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert resp.status_code == 403
```

**注意**：fixture 名（`client`、`student_token`、`admin_token`、`teacher_token`、
`student_id` 等）按 `tests/integration/conftest.py` 实际定义适配；若不存在
student_token/teacher_token fixture，先在该 conftest 中添加（参照现有
`test_students_api_enhanced.py` 的登录方式构造，学生登录返回 Cookie 模式则用
`client.post("/api/v1/auth/login", ...)` 后使用同一 client 会话——本项目是
HttpOnly Cookie 认证，越权测试应构造"学生登录后的独立 client 实例"。
执行时以实际认证方式为准，核心断言是 **403 状态码**。）

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_authorization_negative.py -v`
Expected: FAIL — 各用例返回 200/其它（越权未被拦截）

- [ ] **Step 3: 修复 update_score（第 219-244 行）**

```python
@router.put("/students/{student_id}/score", response_model=ScoreUpdateResponse)
async def update_score(
    request: Request,
    student_id: str,
    data: UpdateScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """更新学生分数（admin 或负责该班的教师）"""
    # 先取学生班级做权限校验，再执行更新
    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    verify_teacher_class_access(user, student.class_name, session)

    username = user.get("username", '')

    student = update_student_score(session, student_id, data.score_change, data.reason, username)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
    # ...（原有返回体不变）
```

- [ ] **Step 4: 修复 add_student（第 193-216 行）**

依赖从 `get_current_user` 改为 `require_admin`（函数体内未使用 user，签名同步改）：

```python
@router.post("/students", response_model=StudentCreateResponse)
async def add_student(
    request: Request,
    data: CreateStudentRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(require_admin)
):
    """添加学生（仅管理员）"""
    # ...（函数体不变）
```

- [ ] **Step 5: 修复 get_student_info（第 165-190 行）**

```python
@router.get("/students/{student_id}", response_model=StudentDetailResponse)
async def get_student_info(
    request: Request,
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生信息（学生只能查看自己；教师限负责班级；响应不含 password_hash）"""
    from app.models import UserRoleConst

    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    role = user.get("role", '')
    user_id = user.get("sub", '')

    if role == UserRoleConst.STUDENT:
        if student_id != user_id:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='无权查看其他学生信息')
    elif role == UserRoleConst.TEACHER:
        verify_teacher_class_access(user, student.class_name, session)

    # 白名单字段，防止泄露 password_hash（P0 修复）
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'student_id': student.student_id,
            'name': student.name,
            'class_name': student.class_name,
            'score': student.score,
            'is_account_enabled': student.is_account_enabled,
            'created_at': student.created_at,
        }
    }
```

- [ ] **Step 6: 修复 get_student_scores（第 363-378 行）**

```python
@router.get("/students/{student_id}/scores", response_model=ScoreLogListResponse)
async def get_student_scores(
    request: Request,
    student_id: str,
    limit: int = Query(None, description="数量限制"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生分数历史（学生限自己；教师限负责班级）"""
    from app.models import UserRoleConst
    from app.crud import get_student_score_logs

    role = user.get("role", '')
    if role == UserRoleConst.STUDENT:
        if student_id != user.get("sub", ''):
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail='无权查看他人分数')
    elif role == UserRoleConst.TEACHER:
        student = get_student(session, student_id)
        if not student:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')
        verify_teacher_class_access(user, student.class_name, session)

    logs = get_student_score_logs(session, student_id, limit)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [log.model_dump() for log in logs]
    }
```

顶部 import 区加：

```python
from app.api.deps import verify_teacher_class_access
```

（`require_admin_or_teacher` 若未 import 一并加入。）

- [ ] **Step 7: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_authorization_negative.py tests/integration/test_students_api_enhanced.py -v`
Expected: PASS（全部通过；原有正向用例若因权限收紧失败，检查其 client 是否具备对应角色后适配）

- [ ] **Step 8: 提交**

```bash
git add backend/app/api/routes/students.py backend/tests/integration/test_authorization_negative.py
git commit -m "fix(auth): restrict score/add/detail/scores endpoints to authorized roles"
```

### Task 11: 签到路由越权修复

**Files:**
- Modify: `backend/app/api/routes/checkin.py:215-348`
- Modify: `backend/app/crud/checkin.py:17-20`（get_all_checkins 支持班级过滤）

- [ ] **Step 1: 写失败测试**

在 `backend/tests/integration/test_authorization_negative.py` 追加：

```python
def test_student_cannot_list_all_checkins(client, student_client):
    resp = student_client.get("/api/v1/checkins")
    assert resp.status_code == 403


def test_student_cannot_read_session_checkins(client, student_client, some_session_id):
    resp = student_client.get(f"/api/v1/checkins/session/{some_session_id}")
    assert resp.status_code == 403


def test_student_cannot_read_checkin_stats(client, student_client, some_session_id):
    resp = student_client.get(f"/api/v1/checkins/stats", params={"session_id": some_session_id})
    assert resp.status_code == 403


def test_active_course_sessions_requires_login(client):
    """未登录不可枚举活跃课堂"""
    resp = client.get("/api/v1/course-sessions/active")
    assert resp.status_code == 401
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_authorization_negative.py -v`
Expected: FAIL（学生可访问返回 200）

- [ ] **Step 3: 修复 checkin 路由**

`get_checkin_list`（第 215-227 行）：

```python
@router.get("/checkins", response_model=CheckinListResponse)
def get_checkin_list(
    request: Request,
    limit: int = Query(200, ge=1, le=1000, description="返回条数限制"),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取签到记录列表（admin 全量；教师限负责班级）"""
    class_names = None
    if user.get("role") != "admin":
        from app.models import User
        user_obj = session.get(User, int(user.get("sub", 0)))
        class_names = user_obj.get_assigned_classes() if user_obj else []

    checkins = get_all_checkins(session, limit=limit, class_names=class_names)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [c.model_dump() for c in checkins]
    }
```

`crud/checkin.py` 的 `get_all_checkins` 加 `class_names` 参数：

```python
def get_all_checkins(
    session: Session,
    limit: int = 200,
    class_names: Optional[List[str]] = None,
) -> List[CheckinRecord]:
    """获取签到记录列表（按时间倒序，用于 admin 签到管理；可选按班级过滤）"""
    query = (
        select(CheckinRecord)
        .where(CheckinRecord.semester == get_current_term())
    )
    if class_names:
        query = query.where(CheckinRecord.class_name.in_(class_names))
    query = query.order_by(CheckinRecord.checkin_time.desc()).limit(limit)
    return list(session.exec(query).all())
```

`get_session_checkin_list`（第 228-243 行）：

```python
@router.get("/checkins/session/{session_id}", response_model=CheckinListResponse)
def get_session_checkin_list(
    request: Request,
    session_id: int,
    db_session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取指定课堂会话的签到列表（admin 或负责该班的教师）"""
    cs = get_course_session(db_session, session_id)
    if not cs:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课堂不存在")
    verify_teacher_class_access(user, cs.class_name, db_session)

    checkins = get_checkins_by_session_id(db_session, session_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [c.model_dump() for c in checkins]
    }
```

`get_checkin_stats`（第 244-324 行）：依赖改为 `require_admin_or_teacher`；
在 `if session_id:` 分支查到 `cs` 后加：

```python
        verify_teacher_class_access(user, cs.class_name, db_session)
```

（无 session_id 分支保持原逻辑——只查当前教师自己的活跃课堂。）

`get_active_course_sessions`（第 326-348 行）：加认证依赖：

```python
@router.get("/course-sessions/active", response_model=ActiveSessionsResponse)
def get_active_course_sessions(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取所有活跃课堂列表（需登录，学生签到页使用）"""
```

顶部 import 区加：

```python
from app.api.deps import verify_teacher_class_access, require_admin_or_teacher
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_authorization_negative.py tests/integration/test_checkin_api_enhanced.py tests/integration/test_active_class_sessions.py -v`
Expected: PASS（全部通过；原有用例需按新权限适配 client）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/checkin.py backend/app/crud/checkin.py backend/tests/integration/test_authorization_negative.py
git commit -m "fix(auth): restrict checkin list/stats/active-sessions endpoints"
```

### Task 12: 失物招领教师接口 publisher_id 校验

**Files:**
- Modify: `backend/app/api/routes/lost_found.py:212-296`

- [ ] **Step 1: 写失败测试**

在 `backend/tests/integration/test_authorization_negative.py` 追加（teacher 编辑/删除
他人发布的物品应 403）：

```python
def test_teacher_cannot_delete_others_lost_found_item(client, teacher_token, other_item_id):
    resp = client.delete(
        f"/api/v1/teacher/lost-found/{other_item_id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert resp.status_code == 403
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_authorization_negative.py::test_teacher_cannot_delete_others_lost_found_item -v`
Expected: FAIL（返回 200 删除成功）

- [ ] **Step 3: 修复四个教师接口**

`teacher_update_item`、`teacher_delete_item`、`teacher_confirm_claim`、`teacher_reject_claim`
在查到 item 后加：

```python
    # P0 修复：教师只能操作自己发布的物品（admin 不受限）
    if user.get("role") != "admin" and item.publisher_id != int(user.get("sub", 0)):
        raise HTTPException(status_code=403, detail="无权操作他人发布的物品")
```

（插入位置：各函数 `item = get_lost_found_item(...)` 与 404 检查之后。）

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_authorization_negative.py tests/integration/test_lost_found_api.py -v`
Expected: PASS（全部通过）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/lost_found.py backend/tests/integration/test_authorization_negative.py
git commit -m "fix(auth): restrict teacher lost-found ops to own items"
```

---

## Phase 5：前端改造

### Task 13: 前端 term API + useTermInfo + date.ts 改造

**Files:**
- Create: `frontend-v3/src/api/term.ts`
- Create: `frontend-v3/src/composables/useTermInfo.ts`
- Modify: `frontend-v3/src/lib/date.ts:68-95`
- Test: `frontend-v3/test/date.term.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `frontend-v3/test/date.term.test.ts`：

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest'
import { getCurrentWeek } from '@/lib/date'

describe('getCurrentWeek 学期基准（第二学期改造）', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('开学前返回 0', () => {
    vi.setSystemTime(new Date('2026-09-04T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(0)
  })

  it('第 1 周返回 1', () => {
    vi.setSystemTime(new Date('2026-09-07T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(1)
  })

  it('第 2 周返回 2', () => {
    vi.setSystemTime(new Date('2026-09-14T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(2)
  })

  it('超过总周数封顶', () => {
    vi.setSystemTime(new Date('2027-01-25T10:00:00'))
    expect(getCurrentWeek('2026-09-07', 20)).toBe(20)
  })

  it('无学期基准时返回 1（向后兼容）', () => {
    expect(getCurrentWeek(null, 20)).toBe(1)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend-v3 && pnpm vitest run test/date.term.test.ts`
Expected: FAIL — 旧实现返回 20（clamp）而非 0/1/2

- [ ] **Step 3: 改造 date.ts**

替换 `frontend-v3/src/lib/date.ts` 的 `getCurrentWeek`（第 63-95 行）为：

```typescript
/**
 * 获取当前周次（基于学期开始日期）
 * 第二学期改造：基准日期由后端 GET /api/term/current 下发，
 * 不再硬编码；开学前返回 0（UI 显示"未开学"）。
 *
 * @param termStartDate 学期开始日期（第 1 周周一，ISO 字符串）
 * @param totalWeeks 学期总周数
 * @returns 当前周次：0=未开学，1..totalWeeks=学期中
 */
export function getCurrentWeek(
  termStartDate?: string | null,
  totalWeeks = 20,
): number {
  // 无学期基准时返回 1（向后兼容，避免全站误显示）
  if (!termStartDate) return 1

  const start = new Date(termStartDate)
  const now = new Date()

  // 开学前返回 0
  if (now < start) return 0

  const msPerWeek = 7 * 24 * 60 * 60 * 1000
  const diff = Math.floor((now.getTime() - start.getTime()) / msPerWeek)
  return Math.min(diff + 1, totalWeeks)
}
```

- [ ] **Step 4: 实现 term API 客户端与 composable**

创建 `frontend-v3/src/api/term.ts`：

```typescript
/**
 * 学期信息 API
 */
import { get } from '@/lib/api'

export interface TermInfo {
  term: string
  start_date: string
  current_week: number
  total_weeks: number
}

export const termApi = {
  getCurrent: () => get<TermInfo>('/term/current'),
}
```

创建 `frontend-v3/src/composables/useTermInfo.ts`：

```typescript
/**
 * 当前学期信息（周次计算基准）
 * 数据来源：后端 GET /api/term/current
 */
import { useQuery } from '@tanstack/vue-query'
import { termApi } from '@/api'

export function useTermInfo() {
  const { data, isPending, error } = useQuery({
    queryKey: ['term', 'current'],
    queryFn: () => termApi.getCurrent(),
    staleTime: 60 * 60 * 1000, // 学期信息几乎不变，1 小时缓存
    retry: 1,
  })
  return { data, isPending, error }
}
```

确认 `frontend-v3/src/api/index.ts` 的导出模式，追加 `termApi` 与 `TermInfo` 导出（遵循现有 barrel 导出风格）。

- [ ] **Step 5: 运行测试确认通过**

Run: `cd frontend-v3 && pnpm vitest run test/date.term.test.ts`
Expected: PASS（5 passed）

- [ ] **Step 6: 提交**

```bash
git add frontend-v3/src/lib/date.ts frontend-v3/src/api/term.ts frontend-v3/src/composables/useTermInfo.ts frontend-v3/test/date.term.test.ts
git commit -m "feat(term): frontend week calculation from backend term info"
```

### Task 14: Schedules.vue 周次来源改造

**Files:**
- Modify: `frontend-v3/src/views/teacher/Schedules.vue`

- [ ] **Step 1: 定位调用点**

Run: `grep -n "getCurrentWeek\|weekOptions\|Array.from({length" frontend-v3/src/views/teacher/Schedules.vue`
Expected: 找到 `getCurrentWeek()` 调用与第 89 行附近 `weekOptions = Array.from({length:20})`

- [ ] **Step 2: 修改 Schedules.vue**

script 部分引入并改造：

```typescript
import { useTermInfo } from '@/composables/useTermInfo'
// ...
const { data: termInfo } = useTermInfo()

// 周次选项：总周数来自后端（fallback 20）
const totalWeeks = computed(() => termInfo.value?.total_weeks ?? 20)
const weekOptions = computed(() =>
  Array.from({ length: totalWeeks.value }, (_, i) => i + 1),
)

// 当前周：后端下发 current_week（fallback 本地计算）
const currentWeek = computed(() => {
  if (termInfo.value) return termInfo.value.current_week
  return getCurrentWeek()
})
```

模板中所有 `getCurrentWeek()` 的直接调用替换为 `currentWeek`；
`Array.from({length:20})` 引用替换为 `weekOptions`。

- [ ] **Step 3: 全工程检查其它调用点**

Run: `grep -rn "getCurrentWeek" frontend-v3/src`
Expected: 仅 `lib/date.ts`（定义）与 `Schedules.vue`（已改）；若还有其它文件（如
CourseSession.vue），同样改用 `useTermInfo` 的 `current_week` 或传参调用。

- [ ] **Step 4: 前端全量测试回归**

Run: `cd frontend-v3 && pnpm test:run`
Expected: PASS（全部 130+ 用例；Schedules 相关用例若失败按新逻辑适配）

- [ ] **Step 5: 提交**

```bash
git add frontend-v3/src/views/teacher/Schedules.vue
git commit -m "feat(term): Schedules.vue week source from backend term API"
```

### Task 15: 缓存失效 key bug 修复

**Files:**
- Modify: `frontend-v3/src/composables/useCourseSessions.ts:75`

- [ ] **Step 1: 修改失效 key**

`useCourseSessionStart` 的 onSuccess 中：

```typescript
      queryClient.invalidateQueries({ queryKey: ['courseSessions'] })
      queryClient.invalidateQueries({ queryKey: ['active-class-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['today-schedules'] })
```

改为（真实 key 为 `['schedules', 'today']`，见 useSchedules.ts:40）：

```typescript
      queryClient.invalidateQueries({ queryKey: ['courseSessions'] })
      queryClient.invalidateQueries({ queryKey: ['active-class-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['schedules', 'today'] })
```

- [ ] **Step 2: 前端测试回归**

Run: `cd frontend-v3 && pnpm vitest run test/composables/ 2>/dev/null || pnpm test:run`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add frontend-v3/src/composables/useCourseSessions.ts
git commit -m "fix(cache): correct today-schedules invalidation key"
```

---

## Phase 6：学期切换脚本

### Task 16: semester_rollover.py 学期切换脚本

**Files:**
- Create: `backend/scripts/semester_rollover.py`
- Test: `backend/tests/unit/test_semester_rollover.py`

- [ ] **Step 1: 写失败测试**

创建 `backend/tests/unit/test_semester_rollover.py`：

```python
"""学期切换脚本测试：分数归档幂等性"""
from app.models import Student, ScoreLog
from app.core.security import hash_password
from scripts.semester_rollover import _archive_scores, ARCHIVE_REASON_PREFIX


def _make_student(session, student_id="TEST001", score=85.0):
    student = Student(
        student_id=student_id, name="测试学生", class_name="测试班级",
        score=score, password_hash=hash_password("pass123"),
        is_account_enabled=True,
    )
    session.add(student)
    session.commit()
    return student


def test_archive_scores_writes_archive_log_and_resets(session):
    from sqlmodel import select
    _make_student(session, score=85.0)
    archived, skipped = _archive_scores(session, "2025-2026-2")
    assert archived == 1
    assert skipped == 0

    student = session.get(Student, "TEST001")
    assert student.score == 0.0

    logs = session.exec(
        select(ScoreLog).where(ScoreLog.student_id == "TEST001")
    ).all()
    assert len(logs) == 1
    assert logs[0].reason == f"{ARCHIVE_REASON_PREFIX} 2025-2026-2"
    assert logs[0].old_score == 85.0
    assert logs[0].new_score == 0.0
    assert logs[0].delta == -85.0
    assert logs[0].semester == "2025-2026-2"


def test_archive_scores_is_idempotent(session):
    """重复执行不产生二次归档"""
    _make_student(session, score=85.0)
    _archive_scores(session, "2025-2026-2")
    # 模拟第二次执行：分数已重置为 0
    archived, skipped = _archive_scores(session, "2025-2026-2")
    assert archived == 0
    assert skipped == 1

    from sqlmodel import select
    logs = session.exec(select(ScoreLog).where(ScoreLog.student_id == "TEST001")).all()
    assert len(logs) == 1
```

- [ ] **Step 2: 创建包标记并运行测试确认失败**

先创建空文件 `backend/scripts/__init__.py`（使 scripts 成为可导入包，
conftest 已将 backend 加入 sys.path）：

```bash
touch backend/scripts/__init__.py
```

Run: `conda run -n student-manage pytest tests/unit/test_semester_rollover.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.semester_rollover'`

- [ ] **Step 3: 实现脚本**

创建 `backend/scripts/semester_rollover.py`：

```python
"""
学期切换脚本 - 开学前手动执行一次（幂等可重跑）

用法:
    cd backend
    python scripts/semester_rollover.py [--disable-graduates 名单.txt]

流程:
    1. 前置检查（当前学期配置、库内 semester 分布）
    2. 快照备份（pg_dump 到 backups/）
    3. 收敛遗留课堂（旧学期 active/scheduled -> ended）
    4. 收敛小组（is_active=False；遗留 evaluating 任务 -> closed）
    5. 分数归档重置（每生写归档 score_log + score 置 0，单事务）
    6. 可选软禁用毕业/退学学生
    7. 输出验证报告
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, Tuple

# 保证以 backend 为工作目录运行时能 import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, update

from app.core.config import get_settings
from app.core.db import engine
from app.core.term import get_current_term
from app.models import CourseSession, Group, GroupTask, ScoreLog, Student

ARCHIVE_REASON_PREFIX = "[学期归档]"


def _archive_scores(session: Session, old_term: str) -> Tuple[int, int]:
    """分数归档重置：每生写一条归档 score_log 并把 score 置 0（幂等）

    Returns:
        (归档人数, 跳过人数) - 已存在归档记录的学生跳过
    """
    students = session.exec(select(Student)).all()
    archived = 0
    skipped = 0

    for student in students:
        existing = session.exec(
            select(ScoreLog).where(
                ScoreLog.student_id == student.student_id,
                ScoreLog.reason == f"{ARCHIVE_REASON_PREFIX} {old_term}",
            )
        ).first()
        if existing:
            skipped += 1
            continue

        session.add(ScoreLog(
            student_id=student.student_id,
            old_score=student.score,
            new_score=0.0,
            delta=-student.score,
            reason=f"{ARCHIVE_REASON_PREFIX} {old_term}",
            operator="system",
            semester=old_term,
        ))
        student.score = 0.0
        session.add(student)
        archived += 1

    session.commit()
    return archived, skipped


def _close_legacy_sessions(session: Session, old_term: str) -> int:
    """旧学期遗留 active/scheduled 课堂 -> ended"""
    result = session.exec(
        update(CourseSession)
        .where(
            CourseSession.semester == old_term,
            CourseSession.status.in_(["active", "scheduled"]),
        )
        .values(status="ended")
    )
    session.commit()
    return result.rowcount


def _close_legacy_groups(session: Session, old_term: str) -> Tuple[int, int]:
    """旧学期小组失效；遗留 evaluating 任务 -> closed"""
    groups_result = session.exec(
        update(Group).where(Group.semester == old_term).values(is_active=False)
    )
    tasks_result = session.exec(
        update(GroupTask)
        .where(GroupTask.semester == old_term, GroupTask.status == "evaluating")
        .values(status="closed")
    )
    session.commit()
    return groups_result.rowcount, tasks_result.rowcount


def _disable_graduates(session: Session, names_file: str) -> int:
    """软禁用毕业/退学学生（名单文件每行一个学号）"""
    with open(names_file, encoding="utf-8") as f:
        ids = [line.strip() for line in f if line.strip()]
    result = session.exec(
        update(Student)
        .where(Student.student_id.in_(ids))
        .values(is_account_enabled=False)
    )
    session.commit()
    return result.rowcount


def _snapshot_backup(old_term: str) -> None:
    """pg_dump 快照备份（软归档的双保险）"""
    settings = get_settings()
    url = settings.database.url or ""
    backup_dir = os.path.join("backups", f"term-{old_term}")
    os.makedirs(backup_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_path = os.path.join(backup_dir, f"classhub_{stamp}.sql")

    if url.startswith("postgresql"):
        subprocess.run(["pg_dump", url, "-f", dump_path], check=True)
        print(f"[备份] PostgreSQL 快照已导出: {dump_path}")
    else:
        print("[警告] 未配置 PostgreSQL URL，跳过 pg_dump（请手动备份）")


def main() -> None:
    parser = argparse.ArgumentParser(description="学期切换脚本")
    parser.add_argument("--disable-graduates", default=None, help="毕业/退学学号名单文件")
    parser.add_argument("--skip-backup", action="store_true", help="跳过 pg_dump 备份")
    parser.add_argument("--old-term", default=None, help="要归档的旧学期标识")
    args = parser.parse_args()

    settings = get_settings()
    old_term = args.old_term or "2025-2026-2"
    new_term = get_current_term()

    print(f"[前置检查] 旧学期={old_term} 新学年={new_term}")
    print(f"[前置检查] 配置 TERM__START_DATE={settings.term.start_date} "
          f"TERM__TOTAL_WEEKS={settings.term.total_weeks}")

    # 交互确认（非交互环境用 --yes 跳过）
    if not args.skip_backup:
        answer = input(f"确认开始学期切换（旧学期 {old_term} -> 新学年 {new_term}）？[y/N] ")
        if answer.lower() != "y":
            print("已取消")
            return
        _snapshot_backup(old_term)

    with Session(engine) as session:
        sessions_closed = _close_legacy_sessions(session, old_term)
        groups_closed, tasks_closed = _close_legacy_groups(session, old_term)
        archived, skipped = _archive_scores(session, old_term)
        disabled = 0
        if args.disable_graduates:
            disabled = _disable_graduates(session, args.disable_graduates)

        total_students = session.exec(select(Student)).all()
        print("\n[验证报告]")
        print(f"  遗留课堂收敛: {sessions_closed}")
        print(f"  小组失效: {groups_closed}  任务关闭: {tasks_closed}")
        print(f"  分数归档: {archived}  跳过(幂等): {skipped}")
        print(f"  软禁用学生: {disabled}")
        print(f"  库内学生总数: {len(total_students)}")
        print("\n学期切换完成。")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_semester_rollover.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/scripts/semester_rollover.py backend/tests/unit/test_semester_rollover.py
git commit -m "feat(term): add idempotent semester rollover script"
```

---

## Phase 7：收尾

### Task 17: 全量回归 + 配置文档

**Files:**
- Modify: `backend/.env.example`（加 TERM 配置示例）
- Modify: `backend/.env` 与 `backend/.env.production`（加 TERM 配置，值用默认即可）

- [ ] **Step 1: 后端全量测试**

Run: `conda run -n student-manage pytest tests/ -v`
Expected: PASS — 全部通过（467 原有 + 新增约 30 个；若有失败逐个修复后重跑，**禁止跳过失败用例**）

- [ ] **Step 2: 前端全量测试**

Run: `cd frontend-v3 && pnpm test:run`
Expected: PASS（130+ 用例全绿）

- [ ] **Step 3: 配置项落文件**

`backend/.env.example` 追加：

```bash
# 学期配置（第二学期引入）
TERM__LABEL=2026-2027-1
TERM__START_DATE=2026-09-07
TERM__TOTAL_WEEKS=20
```

`backend/.env` 与 `backend/.env.production` 追加同样三行。

- [ ] **Step 4: 服务重启验证（CLAUDE.md 完整流程）**

```bash
make status                 # 检查当前服务状态
make stop                   # 停止
sleep 3                     # 等待3秒
# 检查残留进程：ps aux | grep -E "uvicorn|gunicorn|vite"
# 启动后端（终端1）: cd backend && conda run -n student-manage ENV=production python main.py
# 启动前端（终端2）: cd frontend-v3 && pnpm dev
sleep 5                     # 等待5秒
curl -s --max-time 10 http://localhost:8000/api/v1/term/current
```
Expected: 返回 `{"success": true, "data": {"term": "2026-2027-1", "start_date": "2026-09-07", "current_week": 0, "total_weeks": 20}}`（2026-09-04 处于开学前，current_week=0）

- [ ] **Step 5: 最终提交**

```bash
git add backend/.env.example backend/.env backend/.env.production
git commit -m "chore(term): add TERM config entries to env files"
```

---

## 执行顺序与依赖

```
Phase 1 (Task 1→2→3)   学期配置与周次统一          [无依赖]
Phase 2 (Task 4→5)     模型 + 迁移                  [依赖 Task 2 的 term.py]
Phase 3 (Task 6→7)     CRUD 过滤                   [依赖 Task 4]
Phase 4 (Task 8→9→10→11→12)  API 层               [依赖 Task 2/6/9 内部有序]
Phase 5 (Task 13→14→15) 前端                       [依赖 Task 8 的 API]
Phase 6 (Task 16)      切换脚本                    [依赖 Task 4]
Phase 7 (Task 17)      收尾                        [依赖全部]
```

## 风险与回滚

- **迁移风险**：Task 5 的 alembic 迁移在开发 PG 上执行前，先手动 `pg_dump` 一份全库快照。回滚用 `alembic downgrade -1`。
- **权限收紧兼容性**：越权修复可能破坏前端既有调用（如学生页调用受限接口），前端全量测试 + 手动验证登录/签到/查分三个核心流程。
- **默认值风险**：`TERM__START_DATE` 默认 2026-09-07 硬编码在 config 中，**每学期开学前需更新配置**（在 .env 中覆盖，勿改代码默认值）。
