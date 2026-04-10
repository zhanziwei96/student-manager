# 小组合作评分功能设计文档

**日期**: 2026-04-11  
**功能**: 学生按小组合作，教师创建任务并设置评分维度，教师打分 + 组外学生互评取平均，展示成绩。  
**方案**: 完整版（方案 B）

---

## 1. 功能概述

### 1.1 核心流程
1. **教师创建任务**：指定班级、任务名称、描述、评分维度（1~5 个）。
2. **学生自由组队**：创建小组或申请加入已有小组，组长审批。
3. **教师启动任务**：任务进入 `evaluating` 状态，系统：
   - 锁定组队（不可再创建/加入/退出/解散小组）
   - 自动生成组间互评指派表（每组评价该组后面的 3 组，循环处理）
4. **评分阶段**：
   - 教师为每个小组的每个维度打分
   - 组外学生按指派表给目标小组的每个维度打分
5. **教师结束任务**：任务进入 `closed` 状态，结果定稿。
6. **查看成绩**：学生和教师均可在雷达图中对比查看「教师评分」与「组外学生评分」。

### 1.2 核心规则
- **评分权重**：教师评分 : 学生评分 = **6 : 4**
- **维度**：教师创建任务时自定义，所有评价者（教师 + 学生）共用同一套维度
- **小组解散**：组长可申请解散，填写原因，教师审批后才生效
- **随机分配**：教师可在任务 `preparing` 阶段一键将未组队学生随机分配到新小组，组长由系统随机指定

---

## 2. 数据模型

### 2.1 新增 SQLModel 表

#### `groups`（小组表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 小组 ID |
| `class_name` | str | 所属班级 |
| `name` | str | 小组名称（学生自定义） |
| `leader_student_id` | str | 组长学号 |
| `is_active` | bool | 默认 `true`，解散后为 `false` |
| `created_at` | datetime | 创建时间 |

#### `group_members`（组员关系表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | ID |
| `group_id` | int FK | 小组 ID |
| `student_id` | str | 学号 |
| `joined_at` | datetime | 加入时间 |

**约束**：一个学生只能同时属于一个班级的 `is_active=true` 的小组（业务逻辑控制，非数据库唯一索引）。

#### `group_membership_requests`（入组申请表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | ID |
| `group_id` | int FK | 目标小组 |
| `student_id` | str | 申请人学号 |
| `status` | str | `pending` / `approved` / `rejected` |
| `created_at` | datetime | |
| `resolved_at` | datetime 或 null | |

#### `group_tasks`（合作任务表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | 任务 ID |
| `class_name` | str | 目标班级 |
| `title` | str | 任务名称 |
| `description` | str | 描述 |
| `status` | str | `preparing` / `evaluating` / `closed` |
| `created_by` | str | 教师 username |
| `created_at` | datetime | |
| `started_at` | datetime 或 null | 启动时间 |
| `closed_at` | datetime 或 null | 结束时间 |

#### `group_task_dimensions`（评分维度定义表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | ID |
| `task_id` | int FK | 任务 ID |
| `name` | str | 维度名称 |
| `sort_order` | int | 排序 |

#### `evaluation_assignments`（组间互评指派表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | ID |
| `task_id` | int FK | 任务 ID |
| `evaluator_group_id` | int FK | 评分小组 |
| `target_group_id` | int FK | 被评小组 |
| `created_at` | datetime | |

#### `group_evaluation_scores`（评分记录表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | ID |
| `task_id` | int FK | 任务 ID |
| `target_group_id` | int FK | 被评小组 |
| `evaluator_type` | str | `teacher` / `student` |
| `evaluator_id` | str | 教师 username 或学生 student_id |
| `dimension_id` | int FK | 维度 ID |
| `score` | int | 0~100 |
| `created_at` | datetime | |

**唯一索引**：`(task_id, target_group_id, evaluator_type, evaluator_id, dimension_id)` — 防止重复打分。

#### `group_dissolution_requests`（解散申请表）
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK | ID |
| `group_id` | int FK | 小组 ID |
| `reason` | str | 解散原因 |
| `status` | str | `pending` / `approved` / `rejected` |
| `created_at` | datetime | |
| `resolved_at` | datetime 或 null | |
| `resolved_by` | str 或 null | 审批教师 username |

---

## 3. 后端 API

### 3.1 教师端

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/teacher/group-tasks` | 创建任务 + 维度 |
| POST | `/api/v1/teacher/group-tasks/{task_id}/start` | 启动任务，锁定组队并生成互评指派 |
| POST | `/api/v1/teacher/group-tasks/{task_id}/close` | 结束任务，结果定稿 |
| GET | `/api/v1/teacher/group-tasks/{task_id}/results` | 查看各组任务成绩及明细 |
| POST | `/api/v1/teacher/group-tasks/{task_id}/scores` | 教师为指定小组维度打分 |
| GET | `/api/v1/teacher/groups` | 查看各班小组列表及成员 |
| POST | `/api/v1/teacher/groups/auto-assign` | 一键随机分配某班未组队学生 |
| POST | `/api/v1/teacher/groups/{group_id}/transfer-leader` | 转让组长身份 |
| GET | `/api/v1/teacher/group-dissolution-requests` | 查看解散申请列表 |
| POST | `/api/v1/teacher/group-dissolution-requests/{req_id}/approve` | 审批通过解散 |
| POST | `/api/v1/teacher/group-dissolution-requests/{req_id}/reject` | 拒绝解散 |

### 3.2 学生端

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/student/groups` | 创建小组（自动成为组长并加入） |
| GET | `/api/v1/student/groups?class_name=xxx` | 查看某班可加入的小组列表 |
| POST | `/api/v1/student/groups/{group_id}/join-requests` | 提交加入申请 |
| POST | `/api/v1/student/groups/join-requests/{req_id}/approve` | 组长批准申请 |
| POST | `/api/v1/student/groups/join-requests/{req_id}/reject` | 组长拒绝申请 |
| POST | `/api/v1/student/groups/dissolution-requests` | 组长提交解散申请 |
| GET | `/api/v1/student/group-tasks` | 我所在班级的任务列表 |
| GET | `/api/v1/student/group-tasks/{task_id}/evaluations` | 获取我需要评价的组及维度 |
| POST | `/api/v1/student/group-tasks/{task_id}/scores` | 提交对目标组的维度评分 |
| GET | `/api/v1/student/groups/my-group/results` | 查看我所在小组的任务成绩 |

---

## 4. 数据流与状态流转

### 4.1 任务状态流转

```
preparing（组队中）
    ↓ 教师手动启动
    ↓ - 检查小组数量 ≥ 2
    ↓ - 锁定组队
    ↓ - 生成 evaluation_assignments
evaluating（评分中）
    ↓ 教师手动结束
    ↓ - 禁止再打分
closed（已结束）
```

### 4.2 关键业务规则

1. **组队锁定**：任务进入 `evaluating` 后，小组成员冻结，不可创建/加入/退出/解散小组。
2. **入组审批**：组长批准新成员时，系统自动让该学生退出旧组（如有），并加入新组。
3. **解散限制**：只有 `preparing` 状态、且该小组未参与任何 `evaluating` / `closed` 任务时，组长才可申请解散。教师批准后，`group.is_active = false`。
4. **互评范围**：某班的 N 个小组按 `id` 排序，第 `i` 组评价第 `(i+1)%N`、`(i+2)%N`、`(i+3)%N` 组。若 `N ≤ 4`，则每组评价其余所有组。
5. **评分次数**：组外学生评分以「小组」为单位。即 A 组被指派评价 B 组，A 组所有成员均可独立给 B 组打分，系统取这些成员的平均值。
6. **教师评分**：每个维度由教师直接给分，即每个维度只有 1 个教师评分。

---

## 5. 评分计算

### 5.1 单维度综合得分
对于某个小组、某个维度：
- `teacher_score` = 教师在该维度的评分
- `peer_score` = 所有组外学生在该维度的评分平均值
- `dimension_final = teacher_score × 0.6 + peer_score × 0.4`

### 5.2 任务总成绩
- `task_final_score` = 各维度 `dimension_final` 的算术平均值

### 5.3 展示
教师端和学生端均使用雷达图展示：
- 紫色轮廓（#6366f1）：教师评分
- 绿色轮廓（#10b981）：组外学生评分平均值

---

## 6. 前端页面

### 6.1 教师端

| 页面 | 路径 | 说明 |
|------|------|------|
| `GroupTasks.vue` | `teacher/group-tasks` | 任务列表 + 创建任务弹窗 |
| `GroupTaskResults.vue` | `teacher/group-tasks/:id/results` | 各组成绩与雷达图对比 |
| `GroupTaskScore.vue` | `teacher/group-tasks/:id/score` | 教师评分录入 |
| `Groups.vue` | `teacher/groups` | 班级小组管理、随机分配、解散审批、组长转让 |

### 6.2 学生端

| 页面 | 路径 | 说明 |
|------|------|------|
| `MyGroup.vue` | `student/my-group` | 我的小组（创建/申请/审批/解散/成绩） |
| `GroupEvaluations.vue` | `student/group-evaluations` | 待评价小组与维度评分 |
| `GroupResults.vue` | `student/group-results` | 小组成绩单（JOJO 风格雷达图） |

### 6.3 新增组件
- `GroupCard` — 小组信息卡片
- `DimensionInputList` — 动态维度编辑
- `ScoreDimensionForm` — 维度评分表单
- `TaskStatusBadge` — 任务状态标签
- `JoinRequestList` — 入组申请列表（组长用）
- `DissolutionRequestDialog` — 解散申请弹窗
- `JojoRadarChart` — 基于 ECharts / Chart.js 的自定义雷达图，JOJO 硬朗线条风格

---

## 7. JOJO 风格雷达图设计

- **网格线**：粗实线（2px），深灰色（#262626），低透明度（0.3）
- **区域填充**：半透明带纹理感的填充色
- **线条**：硬边、无圆角连接，3px 描边
- **颜色**：
  - 教师评分：紫罗兰色 `#6366f1`
  - 组外学生评分：翠绿色 `#10b981`
- **顶点标记**：实心菱形或尖角星，而非普通圆点
- **整体风格**：减少渐变，强调锐利边界和高对比

---

## 8. 测试策略

### 8.1 后端单元测试
- `tests/unit/crud/test_group_tasks.py`
  - 状态流转、互评指派生成（含循环边界）、得分计算（6:4）
- `tests/unit/crud/test_groups.py`
  - 入组审批、旧组退出逻辑、解散条件校验、随机分配算法

### 8.2 后端集成测试
- `tests/integration/test_group_tasks_api.py`
  - 教师创建/启动/结束任务
  - 学生申请/审批/评分
  - 重复评分拦截、权限校验
  - 少于 2 个小组时启动失败

### 8.3 前端组件测试
- `frontend-v3/test/features/groups/`
  - `GroupTaskCreateDialog.spec.ts`（动态维度输入）
  - `ScoreDimensionForm.spec.ts`（评分提交校验）
  - `MyGroup.vue.spec.ts`（审批操作）

### 8.4 E2E 测试
- `tests/e2e/group-evaluation.spec.ts`
  - 教师创建任务 → 学生 A 创建小组 → 学生 B 申请加入 → 组长审批 → 教师启动任务 → 学生互评 → 教师评分 → 查看结果

---

## 9. 历史变更

| 日期 | 内容 |
|------|------|
| 2026-04-11 | 初始版本，确认方案 B，权重 6:4，JOJO 雷达图，组长审批，解散审批，随机分配未组队学生 |
