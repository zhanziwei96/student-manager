# 班级小组人数上限 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 教师为每个班级设定小组人数上限（2-10），系统在学生加入/审批时强制执行，已满的组不可加入。

**Architecture:** 新建 `ClassGroupSettings` 模型 + CRUD + 两个 API 端点（GET/PUT），修改现有加入/审批端点增加上限检查，前端教师页加设置控件，学生页展示容量。

**Tech Stack:** FastAPI + SQLModel (后端), Vue 3 + TanStack Query + ofetch (前端)

---

### Task 1: 数据模型 — ClassGroupSettings

**Files:**
- Modify: `backend/app/models/group.py` — 添加 ClassGroupSettings 模型
- Modify: `backend/app/models/__init__.py` — 导出新模型

- [ ] **Step 1: 在 group.py 末尾添加 ClassGroupSettings 模型**

```python
class ClassGroupSettings(SQLModel, table=True):
    """班级小组设置表"""
    __tablename__ = "class_group_settings"

    class_name: str = Field(..., description="班级名称", max_length=100, primary_key=True)
    max_members_per_group: int = Field(default=5, description="每组上限人数")
    updated_at: datetime = Field(default_factory=get_now, description="最后修改时间")
```

- [ ] **Step 2: 在 `backend/app/models/__init__.py` 中导入并导出**

在 group 的 import 行添加 `ClassGroupSettings`：

```python
from app.models.group import (
    Group, GroupMember, GroupMembershipRequest,
    GroupTask, GroupTaskDimension, EvaluationAssignment,
    GroupEvaluationScore, GroupDissolutionRequest,
    ClassGroupSettings,
)
```

在 `__all__` 列表的 Group Collaboration 部分添加 `"ClassGroupSettings"`。

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/group.py backend/app/models/__init__.py
git commit -m "feat: add ClassGroupSettings model for per-class group member limit"
```

---

### Task 2: CRUD 函数 — 小组设置读写

**Files:**
- Modify: `backend/app/crud/group.py` — 添加 3 个函数
- Modify: `backend/app/crud/__init__.py` — 导出新函数
- Test: `tests/unit/crud/test_groups.py` — 添加 3 个测试

- [ ] **Step 1: 写失败测试**

在 `tests/unit/crud/test_groups.py` 末尾追加：

```python
from app.models.group import ClassGroupSettings


def test_get_or_create_class_group_settings_creates_default(session: Session):
    settings = get_or_create_class_group_settings(session, "一班")
    assert settings.class_name == "一班"
    assert settings.max_members_per_group == 5


def test_get_or_create_class_group_settings_returns_existing(session: Session):
    settings1 = get_or_create_class_group_settings(session, "一班")
    settings2 = get_or_create_class_group_settings(session, "一班")
    assert settings1.class_name == settings2.class_name
    assert settings2.max_members_per_group == 5


def test_update_class_group_settings(session: Session):
    get_or_create_class_group_settings(session, "一班")
    updated = update_class_group_settings(session, "一班", 8)
    assert updated.max_members_per_group == 8
```

在文件顶部 import 区域添加：

```python
from app.crud import get_or_create_class_group_settings, update_class_group_settings
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/yufeng/student-manager/.worktrees/feature-group-collaboration && conda run -n student-manage pytest tests/unit/crud/test_groups.py -v -k "class_group_settings"`
Expected: FAIL — ImportError

- [ ] **Step 3: 在 `backend/app/crud/group.py` 中实现 3 个函数**

在文件顶部 import 行添加 `ClassGroupSettings`：

```python
from app.models.group import (
    Group, GroupMember, GroupMembershipRequest,
    GroupDissolutionRequest, ClassGroupSettings
)
```

在文件末尾（`auto_assign_unassigned_students` 之后）添加：

```python
def get_class_group_settings(session: Session, class_name: str) -> Optional[ClassGroupSettings]:
    return session.get(ClassGroupSettings, class_name)


def get_or_create_class_group_settings(session: Session, class_name: str) -> ClassGroupSettings:
    settings = session.get(ClassGroupSettings, class_name)
    if not settings:
        settings = ClassGroupSettings(class_name=class_name)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def update_class_group_settings(session: Session, class_name: str, max_members: int) -> ClassGroupSettings:
    settings = get_or_create_class_group_settings(session, class_name)
    settings.max_members_per_group = max_members
    settings.updated_at = get_now()
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings
```

- [ ] **Step 4: 在 `backend/app/crud/__init__.py` 中导出**

在 group 的 import 块和 `__all__` 中添加 `get_class_group_settings`, `get_or_create_class_group_settings`, `update_class_group_settings`。

- [ ] **Step 5: 运行测试验证通过**

Run: `conda run -n student-manage pytest tests/unit/crud/test_groups.py -v`
Expected: ALL PASS

- [ ] **Step 6: 提交**

```bash
git add backend/app/crud/group.py backend/app/crud/__init__.py tests/unit/crud/test_groups.py
git commit -m "feat: add CRUD for ClassGroupSettings with tests"
```

---

### Task 3: 后端 API — 教师设置端点

**Files:**
- Modify: `backend/app/api/routes/groups.py` — 添加 2 个端点
- Test: `tests/integration/test_groups_api.py` — 添加 2 个测试

- [ ] **Step 1: 写失败测试**

在 `tests/integration/test_groups_api.py` 末尾追加：

```python
def test_teacher_get_class_group_settings_default(teacher_client: TestClient):
    resp = teacher_client.get("/api/v1/teacher/class-group-settings?class_name=一班")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["max_members_per_group"] == 5


def test_teacher_update_class_group_settings(teacher_client: TestClient):
    resp = teacher_client.put("/api/v1/teacher/class-group-settings", json={
        "class_name": "一班",
        "max_members_per_group": 6,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["max_members_per_group"] == 6
```

- [ ] **Step 2: 运行测试验证失败**

Run: `conda run -n student-manage pytest tests/integration/test_groups_api.py -v -k "class_group_settings"`
Expected: FAIL — 404 Not Found

- [ ] **Step 3: 在 `backend/app/api/routes/groups.py` 中添加端点**

首先在文件顶部 import 区域添加新 CRUD 函数：

```python
from app.crud import (
    ...existing imports...,
    get_class_group_settings, get_or_create_class_group_settings,
    update_class_group_settings,
)
```

添加请求模型（在 `AutoAssignRequest` 类之后）：

```python
class UpdateClassGroupSettingsRequest(BaseModel):
    class_name: str = Field(..., min_length=1)
    max_members_per_group: int = Field(..., ge=2, le=10)
```

添加两个端点（在 `api_auto_assign` 端点之后）：

```python
@router.get("/teacher/class-group-settings", response_model=ApiResponse[dict])
async def api_get_class_group_settings(
    class_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    settings = get_class_group_settings(session, class_name)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "class_name": class_name,
            "max_members_per_group": settings.max_members_per_group if settings else 5,
        },
    }


@router.put("/teacher/class-group-settings", response_model=ApiResponse[dict])
async def api_update_class_group_settings(
    data: UpdateClassGroupSettingsRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    # 校验：新上限 >= 该班所有小组中当前最大成员数
    groups = get_groups_by_class(session, data.class_name)
    max_current = 0
    for g in groups:
        count = len(get_group_members(session, g.id))
        if count > max_current:
            max_current = count
    if data.max_members_per_group < max_current:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"当前有小组已有 {max_current} 人，上限不能小于此值",
        )
    settings = update_class_group_settings(session, data.class_name, data.max_members_per_group)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "class_name": settings.class_name,
            "max_members_per_group": settings.max_members_per_group,
        },
    }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `conda run -n student-manage pytest tests/integration/test_groups_api.py -v`
Expected: ALL PASS

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/groups.py tests/integration/test_groups_api.py
git commit -m "feat: add teacher API endpoints for class group member limit"
```

---

### Task 4: 后端 — 加入/审批时的上限强制校验

**Files:**
- Modify: `backend/app/crud/group.py` — `approve_membership_request` 增加上限检查
- Modify: `backend/app/api/routes/groups.py` — `api_create_join_request` 增加上限检查
- Modify: `backend/app/api/routes/groups.py` — `api_student_groups` 增加 `max_members` 和 `is_full`
- Test: `tests/unit/crud/test_groups.py` — 审批满员测试
- Test: `tests/integration/test_groups_api.py` — 加入满员组测试

- [ ] **Step 1: 写失败测试**

在 `tests/unit/crud/test_groups.py` 末尾追加：

```python
def test_approve_membership_request_rejects_full_group(session: Session):
    from app.crud import get_or_create_class_group_settings
    g = create_group(session, "一班", "满员组", "stu_001")
    # 加入第2人
    session.add(GroupMember(group_id=g.id, student_id="stu_002"))
    session.commit()
    # 设置上限为2
    get_or_create_class_group_settings(session, "一班")
    update_class_group_settings(session, "一班", 2)
    # 第3人申请加入
    req = create_membership_request(session, g.id, "stu_003")
    with pytest.raises(ValueError, match="已满"):
        approve_membership_request(session, req.id)
```

在顶部 import 区域添加 `update_class_group_settings`（`get_or_create_class_group_settings` 已在 Task 2 中添加）。

- [ ] **Step 2: 运行测试验证失败**

Run: `conda run -n student-manage pytest tests/unit/crud/test_groups.py -v -k "full_group"`
Expected: FAIL — `approve_membership_request` does not raise ValueError

- [ ] **Step 3: 修改 `approve_membership_request` 函数**

在 `backend/app/crud/group.py` 的 `approve_membership_request` 函数中，在 `req.status = "approved"` 之后、`_remove_student_from_class_groups` 之前，添加上限检查：

```python
def approve_membership_request(session: Session, request_id: int) -> Optional[GroupMember]:
    req = session.get(GroupMembershipRequest, request_id)
    if not req or req.status != "pending":
        return None
    group = session.get(Group, req.group_id)
    if not group or not group.is_active:
        return None
    # 上限检查
    settings = get_class_group_settings(session, group.class_name)
    if settings:
        current_count = len(get_group_members(session, group.id))
        if current_count >= settings.max_members_per_group:
            raise ValueError("该小组已满")
    req.status = "approved"
    req.resolved_at = get_now()
    # 先退出旧组
    _remove_student_from_class_groups(session, req.student_id, group.class_name)
    # 加入新组
    member = GroupMember(group_id=group.id, student_id=req.student_id)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member
```

- [ ] **Step 4: 运行单元测试验证通过**

Run: `conda run -n student-manage pytest tests/unit/crud/test_groups.py -v`
Expected: ALL PASS

- [ ] **Step 5: 修改学生申请加入端点 `api_create_join_request`**

在 `backend/app/api/routes/groups.py` 的 `api_create_join_request` 函数中，在 `_check_class_not_evaluating` 之后、`existing` 检查之前，添加：

```python
    # 上限检查
    settings = get_class_group_settings(session, group.class_name)
    if settings:
        members = get_group_members(session, group.id)
        if len(members) >= settings.max_members_per_group:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="该小组已满")
```

- [ ] **Step 6: 修改学生小组列表端点 `api_student_groups`**

在 `api_student_groups` 函数中，获取班级设置，并给每个组增加 `max_members` 和 `is_full`：

```python
@router.get("/student/groups", response_model=ApiResponse[list])
async def api_student_groups(
    class_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    settings = get_class_group_settings(session, class_name)
    max_members = settings.max_members_per_group if settings else None
    groups = get_groups_by_class(session, class_name)
    result = []
    for g in groups:
        members = get_group_members(session, g.id)
        count = len(members)
        result.append({
            "id": g.id,
            "name": g.name,
            "leader_student_id": g.leader_student_id,
            "member_count": count,
            "max_members": max_members,
            "is_full": max_members is not None and count >= max_members,
        })
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: result}
```

- [ ] **Step 7: 修改 `auto_assign` 端点使用班级设置**

在 `api_auto_assign` 函数中，在调用 `auto_assign_unassigned_students` 之前读取班级设置：

```python
@router.post("/teacher/groups/auto-assign", response_model=ApiResponse[list])
async def api_auto_assign(
    data: AutoAssignRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    settings = get_class_group_settings(session, data.class_name)
    group_size = settings.max_members_per_group if settings else data.group_size
    new_groups = auto_assign_unassigned_students(session, data.class_name, group_size)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [{"id": g.id, "name": g.name} for g in new_groups],
    }
```

- [ ] **Step 8: 写集成测试**

在 `tests/integration/test_groups_api.py` 末尾追加：

```python
def test_student_cannot_join_full_group(teacher_client: TestClient, student_client: TestClient):
    # 教师设置上限为 1
    teacher_client.put("/api/v1/teacher/class-group-settings", json={
        "class_name": "一班",
        "max_members_per_group": 1,
    })
    # 学生创建小组（已有1人=组长）
    student_client.post("/api/v1/student/groups", json={
        "class_name": "一班",
        "name": "满员组",
    })
    # 获取小组列表，验证 is_full
    resp = student_client.get("/api/v1/student/groups?class_name=一班")
    data = resp.json()
    assert data["data"][0]["is_full"] is True
    assert data["data"][0]["max_members"] == 1
```

- [ ] **Step 9: 运行全部测试验证通过**

Run: `conda run -n student-manage pytest tests/ -v -k "group" --timeout=30`
Expected: ALL PASS

- [ ] **Step 10: 提交**

```bash
git add backend/app/crud/group.py backend/app/api/routes/groups.py tests/unit/crud/test_groups.py tests/integration/test_groups_api.py
git commit -m "feat: enforce group member limit on join/approve, add max_members/is_full to API"
```

---

### Task 5: 前端 API + Composable

**Files:**
- Modify: `frontend-v3/src/api/groups.ts` — 添加 2 个 API 函数
- Create: `frontend-v3/src/features/group-collaboration/composables/useGroupSettings.ts`
- Modify: `frontend-v3/src/features/group-collaboration/index.ts` — 导出新 composable

- [ ] **Step 1: 在 `frontend-v3/src/api/groups.ts` 中添加 API 函数**

在 `groupsApi` 对象末尾、`getMyGroup` 之后添加：

```typescript
  getClassGroupSettings: (className: string): Promise<{ class_name: string; max_members_per_group: number }> =>
    get('/teacher/class-group-settings', { class_name: className }),
  updateClassGroupSettings: (data: { class_name: string; max_members_per_group: number }): Promise<{ class_name: string; max_members_per_group: number }> =>
    put('/teacher/class-group-settings', data),
```

需要在顶部 import 中添加 `put`（当前只 import 了 `get, post`）：

```typescript
import { get, post, put } from '@/lib/api'
```

- [ ] **Step 2: 创建 `frontend-v3/src/features/group-collaboration/composables/useGroupSettings.ts`**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { groupsApi } from '@/api'
import { toValue, type MaybeRefOrGetter } from 'vue'

export function useClassGroupSettings(className: MaybeRefOrGetter<string>) {
  return useQuery({
    queryKey: ['class-group-settings', className],
    queryFn: () => groupsApi.getClassGroupSettings(toValue(className)),
    enabled: () => !!toValue(className),
  })
}

export function useUpdateClassGroupSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: groupsApi.updateClassGroupSettings,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['class-group-settings', variables.class_name] })
    },
  })
}
```

- [ ] **Step 3: 在 `frontend-v3/src/features/group-collaboration/index.ts` 中导出**

追加一行：

```typescript
export { useClassGroupSettings, useUpdateClassGroupSettings } from './composables/useGroupSettings'
```

- [ ] **Step 4: 更新 Group 类型**

在 `frontend-v3/src/api/groups.ts` 中修改 `Group` 接口：

```typescript
export interface Group {
  id: number
  name: string
  leader_student_id: string
  member_count?: number
  max_members?: number | null
  is_full?: boolean
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend-v3/src/api/groups.ts frontend-v3/src/features/group-collaboration/composables/useGroupSettings.ts frontend-v3/src/features/group-collaboration/index.ts
git commit -m "feat: add frontend API + composable for class group settings"
```

---

### Task 6: 前端教师页 — 上限设置控件

**Files:**
- Modify: `frontend-v3/src/views/teacher/Groups.vue` — 添加设置区
- Test: `frontend-v3/test/views/teacher/Groups.spec.ts` — 更新 mock

- [ ] **Step 1: 修改 Groups.vue script 区域**

在 import 区域添加：

```typescript
import {
  useTeacherGroups,
  useAutoAssign,
  useClassGroupSettings,
  useUpdateClassGroupSettings,
} from '@/features/group-collaboration'
```

在 `handleAutoAssign` 函数之后添加：

```typescript
// 小组人数上限设置
const { data: groupSettings } = useClassGroupSettings(selectedClass)
const { mutateAsync: updateSettings, isPending: savingSettings } = useUpdateClassGroupSettings()
const maxMembers = ref(5)

watch(groupSettings, (s) => {
  if (s) maxMembers.value = s.max_members_per_group
})

async function handleSaveSettings() {
  if (!selectedClass.value) return
  try {
    await updateSettings({ class_name: selectedClass.value, max_members_per_group: maxMembers.value })
    toastSuccess('已更新小组人数上限')
  } catch (err) {
    toastError(getErrorMessage(err) || '更新失败')
  }
}
```

需要在顶部添加 `ref` 和 `watch` import（`ref` 已有，添加 `watch`）：

```typescript
import { ref, computed, watch } from 'vue'
```

（`watch` 已经存在，无需修改。）

- [ ] **Step 2: 修改 Groups.vue template — 在班级选择器旁添加设置**

将现有的 header 区域：

```vue
<div class="flex flex-wrap items-center justify-between gap-3 mb-4">
  <div class="flex items-center gap-3">
    <Select v-model="selectedClass" :options="classOptions" class="w-48" />
    <Button
      :loading="autoAssigning"
      @click="handleAutoAssign"
    >
      <Shuffle class="h-4 w-4 mr-1" />
      自动分组
    </Button>
  </div>
  <span class="text-sm text-[#737373]">
    共 {{ (groups || []).length }} 个小组
  </span>
</div>
```

替换为：

```vue
<div class="flex flex-wrap items-center justify-between gap-3 mb-4">
  <div class="flex items-center gap-3">
    <Select v-model="selectedClass" :options="classOptions" class="w-48" />
    <Button
      :loading="autoAssigning"
      @click="handleAutoAssign"
    >
      <Shuffle class="h-4 w-4 mr-1" />
      自动分组
    </Button>
  </div>
  <div class="flex items-center gap-2">
    <span class="text-sm text-[#737373]">每组上限</span>
    <input
      v-model.number="maxMembers"
      type="number"
      :min="2"
      :max="10"
      class="w-16 rounded-full border border-[#e5e5e5] bg-white px-3 py-1 text-sm text-black text-center focus:outline-none focus:ring-2 focus:ring-[#3b82f6]/50"
    >
    <span class="text-sm text-[#737373]">人</span>
    <Button size="sm" :loading="savingSettings" @click="handleSaveSettings">
      保存
    </Button>
  </div>
</div>
```

同时修改小组卡片的成员数显示，添加上限：

```vue
<div class="mt-1 flex items-center gap-2 text-xs text-[#737373]">
  <Users class="h-3.5 w-3.5" />
  {{ g.member_count || (g.members ? g.members.length : 0) }}{{ groupSettings?.max_members_per_group ? ` / ${groupSettings.max_members_per_group}` : '' }} 人
</div>
```

- [ ] **Step 3: 更新测试 `frontend-v3/test/views/teacher/Groups.spec.ts`**

更新 `@/features/group-collaboration` mock 添加新的 composable：

```typescript
vi.mock('@/features/group-collaboration', () => ({
  useTeacherGroups: () => ({ data: ref([]), isPending: ref(false) }),
  useAutoAssign: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
  useClassGroupSettings: () => ({ data: ref({ class_name: '计算机1班', max_members_per_group: 5 }) }),
  useUpdateClassGroupSettings: () => ({ mutateAsync: vi.fn(), isPending: ref(false) }),
}))
```

- [ ] **Step 4: 运行前端测试**

Run: `cd frontend-v3 && pnpm test:run`
Expected: 175+ PASS

- [ ] **Step 5: 提交**

```bash
git add frontend-v3/src/views/teacher/Groups.vue frontend-v3/test/views/teacher/Groups.spec.ts
git commit -m "feat: add group member limit setting to teacher Groups page"
```

---

### Task 7: 前端学生页 — 容量展示 + 已满标记

**Files:**
- Modify: `frontend-v3/src/views/student/MyGroup.vue` — 成员数和按钮状态
- Test: `frontend-v3/test/views/student/MyGroup.spec.ts` — 更新 mock

- [ ] **Step 1: 修改学生页可加入小组列表的成员数显示**

将 MyGroup.vue 模板中的成员数显示：

```vue
{{ g.member_count }} 人 · 组长 {{ g.leader_student_id }}
```

替换为：

```vue
{{ g.member_count }}{{ g.max_members ? ` / ${g.max_members}` : '' }} 人 · 组长 {{ g.leader_student_id }}
```

- [ ] **Step 2: 修改"申请加入"按钮支持满员状态**

将按钮：

```vue
<Button
  size="sm"
  :loading="joining"
  @click="handleJoin(g.id)"
>
  <LogIn class="h-3.5 w-3.5 mr-1" />
  申请加入
</Button>
```

替换为：

```vue
<Button
  size="sm"
  :disabled="g.is_full"
  :loading="joining"
  @click="handleJoin(g.id)"
>
  <LogIn class="h-3.5 w-3.5 mr-1" />
  {{ g.is_full ? '已满' : '申请加入' }}
</Button>
```

- [ ] **Step 3: 更新测试 `frontend-v3/test/views/student/MyGroup.spec.ts`**

在 `useStudentGroups` mock 中添加 `max_members` 和 `is_full` 字段：

```typescript
useStudentGroups: () => ({
  data: ref([
    { id: 2, name: '第二组', leader_student_id: '2021002', member_count: 3, max_members: 5, is_full: false },
    { id: 3, name: '满员组', leader_student_id: '2021003', member_count: 5, max_members: 5, is_full: true },
  ]),
  isPending: ref(false),
}),
```

添加一个测试用例验证已满状态：

```typescript
it('shows full status for groups at capacity', () => {
  setActivePinia(createPinia())
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const wrapper = mount(MyGroup, {
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      stubs,
    },
  })
  // 满员组应显示"已满"文本
  expect(wrapper.text()).toContain('已满')
})
```

- [ ] **Step 4: 运行前端测试**

Run: `cd frontend-v3 && pnpm test:run`
Expected: ALL PASS

- [ ] **Step 5: 提交**

```bash
git add frontend-v3/src/views/student/MyGroup.vue frontend-v3/test/views/student/MyGroup.spec.ts
git commit -m "feat: show group capacity and full status on student MyGroup page"
```

---

## 自检结果

**Spec coverage:**
- 数据模型 → Task 1 ✅
- CRUD 函数 → Task 2 ✅
- 教师设置 API → Task 3 ✅
- 加入/审批上限校验 → Task 4 ✅
- 学生列表增加 max_members/is_full → Task 4 ✅
- 自动分组使用班级设置 → Task 4 ✅
- 前端 API + composable → Task 5 ✅
- 教师页设置控件 → Task 6 ✅
- 学生页容量展示 → Task 7 ✅

**Placeholder scan:** 无 TBD/TODO，所有代码块完整。

**Type consistency:** `ClassGroupSettings`, `get_or_create_class_group_settings`, `update_class_group_settings` 在 Task 1-4 中命名一致。前端 `Group` 接口的 `max_members`/`is_full` 在 Task 5-7 中一致。
