# 第二学期 P0 改造设计：学期概念 + 数据归档 + 越权修复

---

**文档版本**: v1.0  
**生成时间**: 2026-09-04  
**状态**: ✅ 已获用户确认  
**关联问题**: 系统无学期概念（第二学期数据无法隔离）、多个接口存在越权漏洞、上学期数据需要归档

---

## 1. 背景与目标

ClassHub 已实际使用一个学期（2025-2026-2）。第二学期（2026-2027-1）于 **2026-09-07（周一）** 开学。当前系统存在三类必须开学前解决的问题：

1. **无学期概念**：全部业务表无 semester 字段，课表/签到/分数/小组/问答数据跨学期累积混淆；周次计算前后端矛盾（后端按"当年 2 月 1 日"推算 9 月为第 31 周，前端硬编码 2026-03-30 基准并 clamp 到 20 周）。
2. **越权漏洞**：改分、添加学生、签到查询等接口只校验"已登录"，学生可改任意学生分数、读他班签到明细；`GET /students/{id}` 泄露 password_hash。
3. **无归档机制**：上学期数据无任何学期隔离或归档手段。

**目标**：开学前完成学期概念引入（软归档上学期数据）、周次体系统一、分数学期化重置流程、越权漏洞修复。

## 2. 已确认的决策（需求澄清记录）

| 决策点 | 结论 |
|--------|------|
| 归档方式 | **软归档**：semester 字段标记，数据留在原表，查询按当前学期过滤 |
| 分数语义 | **学期分**：每学期重置，期末分归档写入 score_logs |
| P0 范围 | 学期概念 + 归档 + 周次统一 + 分数重置 + 越权修复；**班级实体化另起子项目**（本次不含） |
| 学期标识格式 | `2026-2027-1`（学年+学期号：1=秋季，2=春季） |
| 开学日期 | 2026-09-07（第 1 周开始） |
| 历史可查性 | **只归档不展示**：前端只显示当前学期，无历史查看界面 |
| 架构方案 | **A：semester 列 + 配置驱动**（不用 terms 表、不用多 schema） |
| 上学期标识 | `2025-2026-2`（历史数据回填值） |

## 3. 设计

### 3.1 数据模型与迁移

**新增 `semester` 列（TEXT 可空）的表**，历史行统一回填 `'2025-2026-2'`，每张表加 B-tree 索引：

| 表 | 理由 |
|----|------|
| `course_schedules` | 课表学期归属；**导入查重键加入 semester**（解决新学期同课程/教师/时段被误判重复） |
| `course_sessions` | 活跃课堂检查、教师课堂历史按学期过滤；**部分唯一索引重建**（"同班同时仅一个 active"加 semester 维度，解决旧 active 卡新学期开课） |
| `schedule_adjustments` | 调课记录按学期过滤，避免新旧学期 (schedule_id, week_number) 错位 |
| `checkin_records` | admin 签到流水只显示当前学期 |
| `score_logs` | 分数日志学期过滤 + **分数归档记录载体** |
| `groups` / `group_tasks` / `group_evaluation_scores` | 互评按学期隔离；遗留 evaluating 任务不再卡新学期互斥检查 |
| `questions` | 课堂问答按学期过滤 |

**不加 semester 的表**：`students`（跨学期实体）、`users`、`lost_found`（按 status 自然收敛）、`class_group_settings`（班级级配置跨学期复用）、`device_binds`（经 session 推导）、`audit_logs`（按时间自然排序）。

**迁移方式**：一条 alembic 迁移（`backend/alembic/versions/`），包含加列 + 回填 + 索引 + course_sessions 部分唯一索引重建。迁移脚本需保证 SQLite（测试库）与 PostgreSQL（开发/生产库）双方言可用（遵循现有 `sqlite_where` + `postgresql_where` 双写模式）。

**分数归档设计**：
- `students.score` 保持"当前学期累计分"。
- 学期切换时：每生写一条 `score_log`（`reason='[学期归档] 2025-2026-2'`，old_score=期末分，new_score=0，delta=-期末分），然后 `score` 置 0，单事务完成。
- 上学期期末分查询：`SELECT old_score FROM score_logs WHERE reason LIKE '[学期归档]%'`——不加新表、不加新字段。

### 3.2 后端学期上下文

- `backend/app/core/config.py` Settings 增加：
  - `TERM__LABEL: str = '2026-2027-1'`
  - `TERM__START_DATE: date = '2026-09-07'`
  - `TERM__TOTAL_WEEKS: int = 20`
- 新建 `backend/app/core/term.py`：
  - `get_current_term() -> str`：返回配置的学期标识
  - `get_current_week_number(today: date | None = None) -> int`：基于 `TERM__START_DATE` 周一起算；开学前返回 0；超过 `TERM__TOTAL_WEEKS` 返回总周数
  - **收敛现有两处互相矛盾的周次计算副本**（`api/routes/schedules.py`、`api/routes/course_sessions.py` 各一份 `_get_current_week_number`）为单一真源
- 写入侧：相关 CRUD 创建函数（create_schedule、create_session、create_score_log、create_group 等）显式填充 `semester=get_current_term()`。
- 读取侧：核心查询统一 `WHERE semester == current_term`：
  - 课表：`get_all_schedules`、`get_today_schedules`、按周查询
  - 课堂：`get_teacher_course_sessions`、活跃课堂检查
  - 签到：`get_all_checkins`、`get_today_checkins`
  - 小组：`get_groups_by_class`、`get_group_tasks_by_class` 及互评互斥检查
  - 问答：questions 列表查询
- 新增 `GET /api/term/current` → `{term, start_date, current_week, total_weeks}`，前端周次改从这里获取。
- 调课接口周次校验 `1 <= week <= 20` → 使用配置的 `TERM__TOTAL_WEEKS`。

### 3.3 越权修复（RBAC 补齐）

| 接口 | 修复 |
|------|------|
| `PUT /students/{id}/score` | → `require_admin_or_teacher`，**教师仅限自己班**（assigned_classes 校验） |
| `POST /students` | → `require_admin`（注释本意如此） |
| `GET /students/{id}` | 教师限自己班；**响应改白名单模型，去掉 password_hash** |
| `GET /students/{id}/scores` | 学生限自己、教师限自己班 |
| `GET /checkins`、`GET /checkins/session/{id}`、`GET /checkins/stats` | → `require_admin_or_teacher` + 教师班别校验 |
| `GET /course-sessions/active` | → 至少 `get_current_user`（学生签到需要） |
| 失物招领教师改/删他人发布 | → 校验 `publisher_id`（同属越权类，顺手修） |

每个修复配**学生越权负向测试**（学生 token 改分 → 403、读他班签到 → 403、教师读他班学生 → 403 等）。

### 3.4 前端改造

1. 新建 `useTermInfo` composable：从 `GET /api/term/current` 获取 `{term, start_date, current_week, total_weeks}`。
2. `src/lib/date.ts`：`getCurrentWeek()` 去掉硬编码基准日期（2026-03-30）和 `clamp(1, 20)`，改为基于后端下发的 `start_date` 计算；开学前返回 0，UI 显示"未开学"。
3. `src/views/teacher/Schedules.vue`：`weekOptions = Array.from({length: 20})` 改用后端 `total_weeks`；"第 N 周"标签全部走统一周次来源。
4. 顺手修缓存 bug：`src/composables/useCourseSessions.ts` 失效 key `'today-schedules'` → 真实的 `['schedules','today']`（开课后"今日课表"不刷新的问题）。
5. **范围控制**：不做历史查看界面、不做学期切换器（已确认"只归档不展示"）；前端所有列表默认只显示当前学期数据（后端已过滤，前端无感知）。

### 3.5 学期切换脚本

新建 `backend/scripts/semester_rollover.py`（开学前手动执行一次，交互式确认，幂等可重跑）：

```
1. 前置检查：当前 TERM__LABEL 与库内 semester 分布核对
2. 快照备份：pg_dump 导出当前库 → backups/term-2025-2026-2/（软归档的双保险）
3. 收敛遗留课堂：旧学期 active/scheduled 的 course_sessions → ended
4. 收敛小组：groups.is_active=False；遗留 evaluating 的 group_tasks → closed
5. 分数归档重置：每生写归档 score_log + score 置 0（单事务）
6. 学生处理：可选 --disable-graduates <名单文件>，软禁用毕业/退学学生（is_account_enabled=False）
7. 输出验证报告：各表行数、归档记录数、待处理课堂数
```

幂等性：重复执行不产生二次归档（通过检测归档 score_log 是否已存在判断）。

### 3.6 测试策略

| 层 | 内容 |
|----|------|
| 单元测试 | `tests/unit/test_term.py`：周次计算（开学前=0、第 1 周、跨周边界、学期切换）；CRUD semester 自动填充 |
| 集成测试 | semester 写入自动填充；**跨学期查询隔离**（上学期数据不出现在当前学期查询）；**越权负向测试**（学生 token 改分→403、读他班签到→403、教师读他班学生→403、学生详情无 password_hash） |
| 前端测试 | `useTermInfo`、date.ts 周次逻辑（模拟后端返回）、缓存失效 key 修复的回归测试 |
| 回归 | 全量后端 467 个 + 前端 130 个测试必须全绿；测试库仍用 SQLite 内存库（迁移脚本需保证双方言可用） |

## 4. 范围外（本次不做）

- **班级实体化**（classes 表 + 全模块 class_name 迁移）——另起子项目
- 学生升级/分班/毕业的正规机制（本次仅提供学期切换脚本中的软禁用 + 已有数据不动）
- 历史数据在线查看界面（只归档不展示）
- JWT 刷新/吊销机制（REMAINING_ISSUES P0-2，用户此前要求暂缓）
- 签到列表服务端分页、大组件拆分、N+1 优化等 P1/P2 项
- 转班接口（PUT /students 路由补齐）——随班级实体化子项目实施

## 5. 成功标准

1. 第二学期开学（2026-09-07）当天，后端 `GET /api/term/current` 返回 `current_week=1`，前后端周次显示一致。
2. 上学期课表/课堂/签到/分数/小组/问答不出现在当前学期任何查询结果中；数据仍完整保留在库中（按 semester 标记）。
3. 分数在学期切换脚本执行后从 0 重新累计；上学期期末分可通过 score_logs 归档记录查询。
4. 所有越权修复接口对学生 token 返回 403（负向测试全绿）；学生详情接口不含 password_hash。
5. 全量测试回归通过（后端 467 + 前端 130）。
