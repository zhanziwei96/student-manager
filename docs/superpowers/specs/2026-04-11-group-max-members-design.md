# 班级小组人数上限设计

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 教师为每个班级设定小组人数上限，系统在学生加入小组时强制执行。

**Architecture:** 新建 `class_group_settings` 表存储班级级别的小组设置。后端在加入/审批环节检查上限，前端展示剩余容量。

**Tech Stack:** FastAPI + SQLModel (后端), Vue 3 + TanStack Query (前端)

---

## 1. 数据模型

### 新建表：`class_group_settings`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `class_name` | str | PK | 班级名称 |
| `max_members_per_group` | int | default=5, 范围 2-10 | 每组上限人数 |
| `updated_at` | datetime | auto | 最后修改时间 |

SQLModel 定义放在 `backend/app/models/group.py` 中。

### 默认值策略

班级第一次访问小组功能时自动创建默认记录（max=5）。通过 `get_or_create` 模式：查询不存在则插入。

---

## 2. 后端 CRUD

文件：`backend/app/crud/group.py`

新增函数：

```python
def get_class_group_settings(session, class_name) -> ClassGroupSettings | None
    # 按 class_name 查询

def get_or_create_class_group_settings(session, class_name) -> ClassGroupSettings
    # 查询，不存在则创建（max=5）

def update_class_group_settings(session, class_name, max_members) -> ClassGroupSettings
    # 更新 max_members_per_group
```

### 修改现有函数

**`approve_membership_request()`** — 审批入组前增加检查：
```python
settings = get_class_group_settings(session, group.class_name)
current_count = len(get_group_members(session, group.id))
if settings and current_count >= settings.max_members_per_group:
    raise ValueError("该小组已满")
```

**`auto_assign_unassigned_students()`** — 读取班级设置作为分组大小：
```python
settings = get_class_group_settings(session, class_name)
group_size = settings.max_members_per_group if settings else group_size
```

---

## 3. 后端 API

### 新增端点

**GET /teacher/class-group-settings?class_name=X**
- 权限：require_teacher
- 响应：`{success: true, data: {class_name, max_members_per_group, updated_at}}`
- 不存在时返回默认值 `{max_members_per_group: 5}`

**PUT /teacher/class-group-settings**
- 权限：require_teacher
- 请求体：`{class_name: str, max_members_per_group: int}`
- 校验：`max_members_per_group` 在 2-10 之间
- 校验：新上限 >= 该班所有小组中当前最大成员数，否则返回错误提示
- 响应：`{success: true, data: {class_name, max_members_per_group}}`

### 修改现有端点

**POST /student/groups/{group_id}/join-requests** — 学生申请加入时：
```python
settings = get_class_group_settings(session, group.class_name)
members = get_group_members(session, group.id)
if settings and len(members) >= settings.max_members_per_group:
    raise HTTPException(400, "该小组已满")
```

**GET /student/groups?class_name=X** — 学生小组列表增加字段：
```python
# 每个组返回时增加 max_members 和 is_full
{
    "id": 1,
    "name": "第一组",
    "leader_student_id": "...",
    "member_count": 3,
    "max_members": 5,
    "is_full": False
}
```

---

## 4. 前端教师页

文件：`frontend-v3/src/views/teacher/Groups.vue`

在页面顶部、班级选择器旁边，增加一行设置区：

```
[班级选择器 ▼ 2025中医康复治疗2班]    每组上限：[5] [保存]
```

- 数字输入框（min=2, max=10）
- 保存按钮，调用 `PUT /teacher/class-group-settings`
- 成功后 toast 提示"已更新"

### 新增 composable

文件：`frontend-v3/src/features/group-collaboration/composables/useGroupSettings.ts`

```typescript
export function useClassGroupSettings(className: MaybeRefOrGetter<string>)
  // useQuery: GET /teacher/class-group-settings?class_name=...

export function useUpdateClassGroupSettings()
  // useMutation: PUT /teacher/class-group-settings
  // onSuccess: invalidateQueries(['class-group-settings'])
```

### 新增 API 函数

文件：`frontend-v3/src/api/groups.ts`

```typescript
getClassGroupSettings: (className: string) =>
  get('/teacher/class-group-settings', { class_name: className }),
updateClassGroupSettings: (data: { class_name: string; max_members_per_group: number }) =>
  put('/teacher/class-group-settings', data),
```

---

## 5. 前端学生页

文件：`frontend-v3/src/views/student/MyGroup.vue`

### 可加入小组列表

- 成员数显示从 `3 人` 改为 `3 / 5 人`
- 已满的组（`is_full === true`）："申请加入"按钮置灰并显示"已满"

```vue
<Button size="sm" :disabled="g.is_full" @click="handleJoin(g.id)">
  <LogIn class="h-3.5 w-3.5 mr-1" />
  {{ g.is_full ? '已满' : '申请加入' }}
</Button>
```

---

## 6. 数据库迁移

新建迁移文件 `migrations/xxx_add_class_group_settings.sql`：

```sql
CREATE TABLE IF NOT EXISTS class_group_settings (
    class_name TEXT PRIMARY KEY,
    max_members_per_group INTEGER NOT NULL DEFAULT 5,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

迁移通过 `events/startup.py` 中的自动建表逻辑处理（SQLModel 的 `create_all`）。

---

## 7. 测试

### 后端测试

- `tests/unit/crud/test_group.py` — 新增：get_or_create_class_group_settings, 上下限校验
- `tests/integration/test_groups_api.py` — 新增：教师设置/修改上限, 学生加入满员组被拒

### 前端测试

- `test/views/teacher/Groups.spec.ts` — 新增上限设置的 mock 和渲染测试
- `test/views/student/MyGroup.spec.ts` — 新增 is_full 按钮状态测试
