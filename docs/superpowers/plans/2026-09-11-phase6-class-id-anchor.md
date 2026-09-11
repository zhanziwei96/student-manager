# Phase 6 实施计划：class_id 唯一锚点化（消灭裸班名解析歧义）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把所有"按裸班级名解析班级"的入口（API 参数、CRUD 过滤、权限判定、学生冗余列、教学班范围）统一为 `class_id`；展示值统一为 `Class_.display_name`（`{届}届{专业}{班名}`）。

**Architecture:** Phase 5 已确立"业务表只存 FK，响应中的 `class_name` 键由 FK 运行时解析"。本阶段把同一做法推广到 Phase 5 明确遗留的两个字符串锚点——`students.class_name`、`course_offerings.class_scope`——并把所有 API 入参从 `class_name: str` 换成 `class_id: int`。`class_cache` 从「id↔裸名」重构为「id→display_name」单向缓存。

**Tech Stack:** FastAPI + SQLModel + PostgreSQL 15 + Alembic；Vue 3.5 + TanStack Query + vitest

**Spec:** [docs/SEMESTER_COHORT_REFACTOR_PLAN.md](../../SEMESTER_COHORT_REFACTOR_PLAN.md)（Phase 5 收尾）+ [Phase 5 计划](./2026-09-10-phase5-remove-redundant-string-columns.md)

## Context

### 根因

`classes` 表唯一约束是 `(name, major, cohort_year)`，裸班名**允许重复**。但 `class_cache.get_class_id_by_name` 只按 `Class_.name` 匹配：

```python
cls = session.exec(select(Class_).where(Class_.name == class_name)).first()  # 无 order_by，任取一行
```

开发库实测：3 个班共享裸名 `1班`（康复治疗技术 / 计算机科学与技术 / 软件工程），`get_class_id_by_name(session, "1班")` 返回 id=6（康复治疗技术1班）。

教师权限链路上还有第二处：`course_offerings.class_scope` 是**自由文本**（`Field(..., min_length=1, max_length=100)`，无校验），`deps.get_teacher_accessible_classes` 把它按逗号 `split` 成裸班名集合，与裸班名做字符串比对。后果：
- 管理员在 UI 填占位符建议的 `计科1-2班` → token 不匹配任何班名 → 教师**没有任何班级权限**（静默失效）
- 管理员填 `1班` → 教师获得**所有专业** `1班` 的权限（越权）

### 为什么现在做

Phase 5 明确把 `students.class_name`（"当前值冗余缓存/展示快照"）与 `course_offerings.class_scope` 列为**非本阶段范围**。裸名重复问题在 Phase 5 之后由批量建班（同届同专业多班）与多专业并存放大，成为当前唯一残留的字符串锚点。

### 决策（已与用户确认）

| 决策项 | 结论 |
|---|---|
| 兼容策略 | **硬切换**：直接删掉 `class_name` 参数与解析函数，不留双写/回退分支 |
| `students.class_name` | **删除该列**（与 Phase 5 删 6 张表 class_name 的做法一致）；响应中 `class_name` 键保留，值改为运行时解析的 `display_name`，`class_id IS NULL` → `未分班` |
| 展示值 | 统一 `display_name`（`2026届软件工程1班`），替代裸名 |
| `course_offerings.class_scope` | **方案 B**：新增 `course_offering_classes(offering_id, class_id)` 关联表，删 `class_scope` 列；响应 `class_scope` 键由关联表运行时拼装 |
| 通配教学班 | **选项 1**：offering 在 `course_offering_classes` **无关联行** = 全部班级（兼容生产库现有 `class_scope="所有专业"`），并记告警日志提示管理员补全；不引入新字段/开关 |

## 影响面盘点（已完成）

### 后端

| 层 | 数量 | 位置 |
|---|---|---|
| 解析函数调用（按名解析） | 76 | `get_class_id_by_name` 35 + `get_class_ids_by_names` 41 |
| 展示解析（id→名，方向正确、返回值需换成 display_name） | 47 | `get_class_name_by_id` 28 + `get_class_names` 19 |
| CRUD 层 class_name 入参 | 37 | student 8 / group 8 / schedule 5 / question 4 / course_session 4 / ranking 3 / checkin 3 / schedule_adjustment 2 |
| API 层 class_name 入参 | 23 | 见下表 |
| 权限判定 | 2 | `deps.verify_teacher_class_access`（`students.py:323,428` 传入 `student.class_name`） |

**API 入参清单（23 处）**：

| 文件 | 行 |
|---|---|
| `checkin.py` | 53, 63, 73, 85, 393 |
| `course_sessions.py` | 33, 42 |
| `groups.py` | 35, 41, 50, 63, 145, 346 |
| `questions.py` | 29, 52, 103 |
| `schedules.py` | 140 |
| `students.py` | 31, 39, 78, 439（`class_names` 列表） |
| `rankings.py` | 25 |
| `login.py` | 46 |

### 前端（38 文件）

- API 客户端：`checkin.ts` / `schedules.ts` / `students.ts` / `groups.ts` / `courseSession.ts` / `rankings.ts` / `question.ts`
- 视图：`teacher/Schedules.vue`、`teacher/Groups.vue`、`teacher/TeacherRankings.vue`、`teacher/Students.vue`、`teacher/TeacherQuestion.vue`、`student/MyGroup.vue`、`admin/Students.vue`、`admin/Offerings.vue`
- 组合式：`useGroups.ts` / `useGroupSettings.ts` / `useTeacherQuestions.ts` / `usePaginatedStudents.ts`

### 测试

- 44 个后端测试文件引用 `class_name`
- 前端 `test/` 下相关 spec

## Global Constraints

- Python 命令必须用 `conda run -n student-manage`；前端在 `frontend-v3/` 用 `pnpm`
- 后端测试：项目根目录 `pytest tests/ -q`（xdist 4 分库并行）；测试库靠 `SQLModel.metadata` 建表，模型改了自动跟随
- 分支：从 main 切 `feat/class-id-anchor`；禁止直接改 main
- 代码质量五原则（架构一致、可改原代码、不留冗余、不用 trick、统一优雅）
- 后端 API 契约：`ApiResponseConst` 包装
- `class_cache` 只缓存**简单值**（int→str），不缓存 ORM 对象（detached 风险）
- 每个 Task 完成后必须：`pytest tests/ -q` 通过 + 相关前端 `pnpm test:run` 通过

## 任务清单

> **⚠️ 流程纠偏（Task 3 质量评审暴露）**：Task 1 起 `import main` / 集成测试收集即被 `get_class_id_by_name` ImportError 卡死，且该状态会掩盖后续 Task 的回归。新规则：**每个 Task 完成后必须能 `import main`（应用可导入）+ 相关测试文件可运行**——不允许"反正后面 Task 会修"。故插入 Task 3.5 恢复导入。
> **⚠️ 子代理纪律**：实现子代理不得越界改别的 Task 的文件（Task 4 初犯：改了 group_scores/question/ranking 且把 `verify_teacher_class_access` 误传 display_name 字符串）。后续派发需在 prompt 里明确"只改本 Task 清单内的文件"。

- [x] **Task 1 — class_cache 重构**：✅ commit 24f2259
- [x] **Task 2 — 迁移：删 `students.class_name`**：✅ commit 325eb6f + a8dbc10
- [x] **Task 3 — 迁移：`course_offering_classes` 关联表（方案 B）**：✅ commit a9bee35（spec 通过；质量评审 verified-correct，4 项 gate 见下）
  - 评审 gate：(1) 修/xfail `test_deps_teacher_class.py` 2 个失败；(2) 给 `20260911c` 回填加迁移测试（`test_migration_core_entities.py`）；(3) 生产部署前跑重复预检 `GROUP BY course_id,semester_id,teacher_id HAVING count(*)>1`；(4) Task 7 落地前不得合并 main
- [x] **Task 3.5 — 恢复可导入**：✅ commit 19eac79（双评审通过；import main OK，集成 314 + 单元 473 可收集；crud 全部改 class_id；4 个 verify_class_has_active_students 调用点闭合；无转换 bug）。**注意：crud/api 的 class_id 迁移大部分已在本步提前完成**，后续 Task 4-11 主要是「前端契约对齐 + 测试迁移 + 少量 routes 收尾」
  - 评审发现的过渡态（各 Task 收尾时清理）：schedule.py:261 过渡助手裸名歧义（Task 6）、get_all_classes 收窄影响统计（Task 11 确认前端）、enrollments.py:64 + login.py:119,134 死属性（Task 11）
- [ ] **Task 4 — 学生模块**：`crud/student.py`（`get_students` / `get_students_by_class(es)` / `count_students_filtered` / `disable_students_by_class` / `get_all_classes` / `create_student`）改 `class_id: int`；`update_student` 转班写 `class_id`（删 `student.class_name = target.name`）；`api/routes/students.py` 全部 `class_name` 入参改 `class_id`（列表筛选 / `CreateStudentRequest` / 详情 / `disable-by-class` 的 `class_names`→`class_ids`），2 处 `verify_teacher_class_access` 改传 `student.class_id`，"当前课堂签到标记"链路（`get_active_course_session_by_class_name` + `get_today_checkins`）改按 `class_id`；响应 dict 里 `class_name` 键由 `class_id` 经 `get_class_display_names` 运行时拼装
- [ ] **Task 5 — 签到模块**：`crud/checkin.py` 3 处 + `api/routes/checkin.py` 5 处参数
- [ ] **Task 6 — 课表/调课模块**：`crud/schedule.py` 5 处、`crud/schedule_adjustment.py` 2 处、`api/routes/schedules.py:140` 筛选改 `class_id`；**课表 Excel 导入/模板：班级列从「`2025康复治疗技术1班` 粘连串」改为「所属届+专业+班级名」三列（与学生导入对齐），按三元组 `ensure_class` 定位/建班**
- [ ] **Task 7 — 权限真源：教学班范围 id 化**：`deps.get_teacher_accessible_classes` 返回 `set[int]`；`verify_teacher_class_access(user, class_id, session)`；`crud/enrollment.py` 与 `api/routes/course_offerings.py`、`semesters.py` rollover 导出改用关联表；`class_scope` 响应键由关联表运行时拼装
- [ ] **Task 8 — 课堂模块**：`crud/course_session.py` 4 处 + `api/routes/course_sessions.py` 2 处
- [ ] **Task 9 — 小组模块**：`crud/group.py` 8 处（含 `get_class_group_settings` / `get_or_create_class_group_settings` / `update_class_group_settings` 由 class_name 改 class_id）+ `api/routes/groups.py` 6 处
- [ ] **Task 10 — 问答模块**：`crud/question.py` 4 处 + `api/routes/questions.py` 3 处
- [ ] **Task 11 — 排行/统计/登录**：`crud/ranking.py` 3 处、`api/routes/rankings.py:25`、`api/routes/system.py`（`get_all_classes` 调用点）、`api/routes/login.py:46`；**另修 Task 3.5 遗留的 3 处死属性引用：`login.py:119,134`（学生登录读已删的 `student.class_name` 构建 JWT/响应 → 改按 class_id 解析 display_name）、`enrollments.py:64`（`verify_teacher_class_access(user, student.class_name)` → `student.class_id`）**
- [ ] **Task 12 — 前端：API 客户端与类型**：7 个 api 文件 + `types/api.ts` 参数类型
- [ ] **Task 13 — 前端：班级选择器统一**：抽 `<ClassSelect>` 组件（返回 `class_id`，选项展示 `display_name`，按届/专业分组），替换 8 处视图里的裸名下拉/输入
- [ ] **Task 14 — 前端：管理端教学班范围多选**：`admin/Offerings.vue` 自由文本 Input → 班级多选
- [ ] **Task 15 — 测试迁移**：44 个后端测试文件 + 前端 spec
- [ ] **Task 16 — 文档**：`docs/API_CHANGELOG.md`、`docs/DEPRECATIONS.md`、`docs/API_EXAMPLES.md`、`CLAUDE.md`、`SEMESTER_COHORT_REFACTOR_PLAN.md`；另修正 `backend/app/models/class_.py:25` 与 `:46` 里过时的 display_name 注释（仍写"2026届1班"，未含 major）
- [ ] **Task 17 — 端到端验证**：全量后端 + 前端测试；起服务手工验证 8 条主链路（建班 → 导入学生 → 建教学班 → 排课 → 开课 → 签到 → 小组 → 排行）
