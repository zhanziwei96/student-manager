# 小组任务复制功能设计

## 概述

教师可以将自己在某班级创建的小组合作任务复制到另一个班级。复制的内容包括任务标题、描述和评分维度；新任务的状态固定为 `preparing`，不复制互评分配和评分结果。

## 数据复制规则

| 字段 | 来源 | 新任务值 |
|------|------|----------|
| `title` | 源任务.title | 源标题 + "（复制）" |
| `description` | 源任务.description | 原样复制（含 `null`） |
| `class_name` | 请求参数 `target_class_name` | 新班级 |
| `created_by` | 当前登录教师 | 当前教师用户名 |
| `status` | 固定 | `"preparing"` |
| `dimensions` | 源任务关联维度 | 按原 `sort_order` 复制 |
| `started_at` / `closed_at` | — | `None` |
| `created_at` | — | 当前时间 |

**不复制的内容：** 互评分配（`EvaluationAssignment`）、任何评分结果（`GroupEvaluationScore`）。

## 后端 API 设计

### 新端点

`POST /teacher/group-tasks/{task_id}/clone`

### 请求体

```json
{
  "target_class_name": "string"
}
```

### 权限与校验

1. 使用 `require_teacher` 校验教师身份。
2. 校验源任务存在，否则返回 `404 Not Found`。
3. 校验源任务 `created_by` 等于当前教师用户名，否则返回 `403 Forbidden`。
4. 校验 `target_class_name` 非空，否则返回 `400 Bad Request`。

### 响应示例

```json
{
  "success": true,
  "data": {
    "task_id": 123,
    "status": "preparing"
  }
}
```

### 后端改动文件

- `backend/app/api/routes/groups.py`：新增 `CloneGroupTaskRequest` 模型和 `api_clone_group_task` 路由。
- `backend/app/crud/group_task.py`：新增 `clone_group_task(session, source_task_id, target_class_name, created_by)` 函数。

## 前端设计

### UI 改动

- 在 `GroupTasks.vue` 任务卡片上增加 **"复制"** 按钮（使用 `Copy` 图标）。
- 点击后弹出 **复制确认对话框**，包含：
  - 源任务标题（只读）
  - 目标班级选择器（Select，默认当前已选班级，但允许切换）

### API 与状态管理

- `frontend-v3/src/api/groups.ts`：新增 `cloneTask(taskId: number, targetClassName: string)` 方法。
- `frontend-v3/src/features/group-collaboration/composables/useGroupTasks.ts`：新增 `useCloneGroupTask()` mutation。
- 复制成功后调用 `queryClient.invalidateQueries({ queryKey: ['group-tasks'] })`，刷新目标班级任务列表。

### 前端改动文件

- `frontend-v3/src/api/groups.ts`
- `frontend-v3/src/features/group-collaboration/composables/useGroupTasks.ts`
- `frontend-v3/src/views/teacher/GroupTasks.vue`

## 错误处理

| 场景 | 行为 |
|------|------|
| 源任务不存在 | 后端返回 `404 Not Found` |
| 当前教师不是任务创建者 | 后端返回 `403 Forbidden` |
| `target_class_name` 为空 | 后端返回 `400 Bad Request` |
| 网络异常 | 前端使用 `getErrorMessage` 提示错误 |

## 测试覆盖

### 后端单元测试

- `tests/unit/crud/test_group_tasks.py`：
  - `clone_group_task` 正常复制标题、描述和维度。
  - 新任务状态为 `preparing`。

### 后端集成测试

- 教师复制自己的任务 → 成功并返回新 `task_id`。
- 复制不存在的任务 → `404`。
- 复制他人创建的任务 → `403`。

### 前端测试

- `test/views/teacher/GroupTasks.spec.ts`（如存在）：
  - 复制按钮存在且可点击。
  - 复制成功后任务列表刷新。
