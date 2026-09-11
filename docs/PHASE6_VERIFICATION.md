# Phase 6 端到端验证与上线验收方案

---

**适用分支**: `feat/class-id-anchor`
**文档版本**: v1.0
**最后更新**: 2026-09-11
**关联文档**: [API_CHANGELOG.md](./API_CHANGELOG.md) v3.1.0 · [DEPRECATIONS.md](./DEPRECATIONS.md) · [SEMESTER_DEPLOYMENT.md](./SEMESTER_DEPLOYMENT.md)

---

## 1. 目标

本次重构把「班级」的唯一锚点从**裸班级名**改为 **class_id**。验证的不只是"功能没坏"，而是**歧义被真正消除**——这是本次改动存在的唯一理由。

### 1.1 被修复的两个真实缺陷（必须在验证中复现"已修复"）

| # | 缺陷 | 旧行为 |
|---|------|--------|
| D1 | **跨专业串班** | `class_cache.get_class_id_by_name("1班")` 无 `ORDER BY` 取首行 → 3 个专业的 `1班` 中任取其一。给「软件工程1班」的签到/课表/小组操作会落到别的专业 |
| D2 | **教师权限越权 + 静默失效** | 权限真源 `course_offerings.class_scope` 是自由文本，按逗号 split 后与裸班名比对：填 `1班` → 获得**所有专业** `1班` 权限（越权）；填 `计科1-2班`（UI 占位符写法）→ 匹配不到任何班，教师**静默失去全部班级权限** |

---

## 2. 前置条件

### 2.1 开发库当前状态（2026-09-11 实测）

| 项 | 值 | 说明 |
|---|---|---|
| alembic 版本 | `20260911_add_class_status` | **落后于代码 3 个迁移** |
| `course_offering_classes` 表 | **不存在** | 迁移未跑 |
| `students.class_name` 列 | **仍存在** | 迁移未跑 |
| 班级 / 学生 / 教学班 | 10 / 2 / 1 | — |
| 裸名重复 | `1班×3`、`6班×2`、`2班×2` | **歧义场景真实存在，可直接用于验收** |
| 当前学期 | `2026-2027-1` | — |

> ⚠️ **必须先执行第 3 节迁移**，否则新代码启动即因缺表/缺列报错。

### 2.2 连接角色（易错点）

| 库 | 属主 / 角色 | 密码 |
|---|---|---|
| `classhub`（开发） | `yufeng` | `yufeng` |
| `classhub_test_0..3`、`classhub_migration_test_0..3`（测试） | `classhub` | `classhub_dev` |

用 `classhub` 角色连开发库会 `permission denied`。

### 2.3 启动服务

```bash
# 数据库（WSL 重启后会掉，且 /var/run/postgresql 需重建）
sudo service postgresql start
sleep 5
psql "postgresql://yufeng:yufeng@localhost:5432/classhub" -tAc "SELECT 'PG OK'"   # 等恢复完成

# 后端（终端 1）
cd backend && conda run -n student-manage ENV=production python main.py
curl -s --max-time 5 http://localhost:8000/api/v1/health

# 前端（终端 2）
cd frontend-v3 && pnpm dev        # 端口 5174（5173 被 Windows svchost 占用）
```

---

## 3. 迁移执行

### 3.1 生产/开发库前置检查（**必做，否则迁移会失败**）

`20260911c` 会重建 `uix_offering`：唯一约束由
`(course_id, semester_id, teacher_id, class_scope)` 收窄为 `(course_id, semester_id, teacher_id)`。
去掉 `class_scope` 维度后，原先"合法共存"的两行可能撞唯一键：

```sql
SELECT course_id, semester_id, teacher_id
FROM course_offerings
GROUP BY 1,2,3 HAVING count(*) > 1;
```

**有返回行 → 先解决重复再迁移。** 无返回行 → 可安全执行。

### 3.2 备份

```bash
pg_dump -h localhost -U yufeng -d classhub -Fc -f ~/classhub_pre_phase6_$(date +%Y%m%d_%H%M).dump
```

### 3.3 执行迁移

```bash
cd backend
conda run -n student-manage alembic -c alembic.ini upgrade head
```

依次应用 3 个迁移：

| 迁移 | 作用 |
|---|---|
| `20260911b_drop_students_class_name` | 删 `students.class_name` 列 + 索引 |
| `20260911c_add_course_offering_classes` | 建关联表 + 从 `class_scope` 回填 + 重建 `uix_offering` + 删 `class_scope` 列 |
| `20260911_add_class_status`（基线） | 已在 dev 应用 |

### 3.4 迁移后核对

```sql
-- 1) 关联表已建
SELECT to_regclass('public.course_offering_classes');            -- 非 NULL

-- 2) class_name 列已删
SELECT column_name FROM information_schema.columns
WHERE table_name='students' AND column_name IN ('class_name','class_id');  -- 只剩 class_id

-- 3) 唯一约束已收窄
SELECT pg_get_constraintdef(oid) FROM pg_constraint
WHERE conname='uix_offering';   -- UNIQUE (course_id, semester_id, teacher_id)

-- 4) 回填结果：无关联行 = 全部班级（通配）
SELECT o.id, o.teacher_name, count(c.class_id) AS linked_classes
FROM course_offerings o
LEFT JOIN course_offering_classes c ON c.offering_id = o.id
GROUP BY o.id, o.teacher_name;
```

**预期**：开发库那 1 个教学班原 `class_scope="所有专业"`（无法唯一匹配任何班）→ `linked_classes = 0` → **通配全部班级**。这是刻意保留的过渡语义（见 §5.3）。
> ⚠️ 若 `linked_classes = 0` 出现在**本应有明确范围**的教学班上，说明回填丢失了该 offering 的范围，需人工补录。

---

## 4. 自动化验证

```bash
# 后端全量（xdist 4 分库并行）
cd /home/yufeng/student-manage-v3-security/student-manager/.worktrees/class-id-anchor
conda run -n student-manage python -m pytest tests/ -q -p no:randomly
# 期望: 791 passed, 0 failed

# 前端
cd frontend-v3
pnpm exec vue-tsc --noEmit        # 期望: 退出码 0，无输出
pnpm test:run                     # 期望: Test Files 40 passed, Tests 242 passed
```

> 💡 提速：迭代期只跑目标文件；全量仅在里程碑执行。可用
> `PYTEST_XDIST_WORKER=gw1 ... -n 0` 固定到单个测试库分片（多代理并行时避免抢库），
> 但**串行会显著变慢**——单任务收尾时应去掉 `-n 0` 用默认 `-n 4`。

### 4.1 已有的歧义回归测试（应全部通过）

| 测试 | 守护的契约 |
|---|---|
| `tests/unit/test_class_cache.py` | 裸名解析函数**已不存在**（`hasattr` 断言）；id→display_name 单向缓存 |
| `tests/unit/test_deps_teacher_class.py` | 教师权限从关联表派生；**无关联行 = 通配放行** |
| `tests/unit/test_migration_core_entities.py::test_backfill_course_offering_classes` | 回填：唯一 token 链接、**歧义 token 跳过**、`所有专业` 留空走通配 |
| `tests/integration/test_disable_students_by_class.py::TestDisabledClassContentCreation` | 禁用班级不可建课堂/小组/问答/**课表** |
| `tests/integration/test_schedule_api.py::test_import_schedules_csv` | 课表导入要求班级**有启用学生** |

---

## 5. 手工端到端链路

启动服务后按序走通 8 条链路。**每条都记录实际结果**，不要只看"没报错"。

### 5.1 主链路

| # | 步骤 | 操作 | 期望 |
|---|---|---|---|
| 1 | 建班 | 管理员 → 班级管理 → 创建：届=2026、专业=软件工程、班级名=`1-2` | 批量创建 2 个班；列表显示完整名 `2026届软件工程1班/2班` |
| 2 | 导入学生 | 学生管理 → 导入，列：`学号/姓名/所属届/专业/班级名` | 按三元组定位班级；不存在的班级自动建；报告 imported/skipped/errors |
| 3 | 建教学班 | 教学班管理 → 创建，**面向范围勾选** `2026届软件工程1班` | 列表"面向范围"显示该班，非"所有班级" |
| 4 | 排课 | 课程表 → 导入，列：`课程名称/所属届/专业/班级名/教师姓名/星期/开始时间/结束时间` | 导入成功；班级无启用学生时该行被拒 |
| 5 | 开课 | 教师端 → 开始上课（选该班） | 生成 session_code；学生端该班可见"进行中" |
| 6 | 签到 | 学生端签到 / 教师代签 | 签到记录 `class_name` 显示完整名 `2026届软件工程1班` |
| 7 | 小组 | 教师端 → 小组 → 自动分组 | 按 `class_id` 建组；班级小组设置生效 |
| 8 | 排行 | 排行榜（全校 / 本班） | 全校榜按**教师+科目**聚合；本班榜只含本班学生 |

### 5.2 🎯 核心验收：跨专业同名班不串班（D1）

开发库已有 `1班×3`（康复治疗技术 / 计算机科学与技术 / 软件工程），直接用：

1. 记下三个 `1班` 的 id：
   ```sql
   SELECT id, cohort_year||'届'||major||name AS display FROM classes WHERE name='1班' ORDER BY id;
   ```
2. 管理员 → 学生管理 → **分别**给三个班各导入 1 名学生（学号如 `AMB1`/`CS1`/`SE1`）。
3. **筛选**：班级下拉选「2026届软件工程1班」→ **列表只应出现 `SE1`**（若出现其他人的学生 = 串班，验收失败）。
4. 建一个教学班，面向范围**只勾选**「2026届软件工程1班」。
5. 用该授课教师登录 → 开课/分组/提问/看学生列表：**只能看到 `SE1` 所在班**。
6. 交叉验证：换「2026届计算机科学与技术1班」重复 4-5，结果互不干扰。

### 5.3 🎯 核心验收：教师权限（D2）

1. 用**只勾选了软件工程1班**的教师账号登录。
2. 尝试访问其他班的资源（直接改 URL 参数 / 用 API）：
   ```bash
   # 应 403
   curl -s --max-time 10 -b cookies.txt \
     "http://localhost:8000/api/v1/teacher/groups?class_id=<计算机1班的id>" -o /dev/null -w "%{http_code}\n"
   ```
3. **通配语义确认**：开发库那 1 个历史教学班（原 `class_scope="所有专业"`）在关联表无行 → 该教师应**对所有班级均有权限**。
   这是刻意保留的过渡行为；上线后应请管理员把这类教学班**补勾真实班级集合**，否则该教师对所有班级（含新建班）持续有权限。

---

## 6. 上线验收清单

- [ ] §3.1 重复预检 SQL 无返回行
- [ ] §3.2 已备份
- [ ] §3.3 迁移 upgrade head 成功
- [ ] §3.4 四项核对全部符合预期
- [ ] §4 后端 791 passed / 前端 242 passed / vue-tsc 干净
- [ ] §5.1 主链路 8 条全部走通
- [ ] §5.2 **跨专业同名班不串班**（本次重构的核心目标）
- [ ] §5.3 教师权限：越权被拒 + 通配行为符合预期
- [ ] 管理员已把"全部班级"教学班补勾为真实班级集合
- [ ] 客户端已按 [DEPRECATIONS.md](./DEPRECATIONS.md) 完成 `class_name` → `class_id` 迁移

## 7. 风险与回滚

| 风险 | 缓解 |
|---|---|
| `uix_offering` 重建撞唯一键 | §3.1 预检；有重复先合并/结束其一 |
| 回填把范围丢成通配（权限放宽） | §3.4 第 4 项核对；对 `linked_classes=0` 的 offering 人工确认 |
| 迁移不可回滚 | 三个迁移均 `raise NotImplementedError`（冗余列已废弃），**只能靠 §3.2 备份恢复** |
| 客户端未同步改造 | 响应 `class_name` 键保留，纯展示不受影响；**逻辑判断/回传必须用 `class_id`** |
