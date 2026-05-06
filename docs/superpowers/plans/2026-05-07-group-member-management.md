# 小组成员管理功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现教师端小组管理功能，包括查看小组成员、踢出成员、解散小组

**Architecture:** 后端新增 3 个 API 端点（获取小组详情、踢出成员、解散小组），前端扩展现有小组管理页面，添加展开/收起成员列表、踢出成员、解散小组功能

**Tech Stack:** FastAPI, SQLModel, Vue 3, TypeScript, TanStack Query, Vitest

---

## 文件结构

**后端修改：**
- `backend/app/crud/group.py` - 新增 CRUD 函数
- `backend/app/api/routes/groups.py` - 新增 API 端点
- `tests/unit/crud/test_group.py` - 新增单元测试
- `tests/integration/test_groups_api.py` - 新增集成测试

**前端修改：**
- `frontend-v3/src/api/groups.ts` - 新增 API 函数
- `frontend-v3/src/types/api.ts` - 新增类型定义
- `frontend-v3/src/views/teacher/Groups.vue` - 修改小组管理页面
- `frontend-v3/test/views/teacher/Groups.spec.ts` - 新增组件测试

---

## Task 1: 后端 CRUD 层 - 获取小组详情

**Files:**
- Modify: `backend/app/crud/group.py`
- Test: `tests/unit/crud/test_group.py`

- [ ] **Step 1: 编写获取小组详情的失败测试**

```python
# tests/unit/crud/test_group.py
def test_get_group_with_members(session, test_group, test_students):
    """测试获取小组详情，包含成员列表和学生姓名"""
    from app.crud.group import get_group_with_members
    
    result = get_group_with_members(session, test_group.id)
    
    assert result is not None
    assert result["id"] == test_group.id
    assert result["name"] == test_group.name
    assert result["class_name"] == test_group.class_name
    assert result["leader_student_id"] == test_group.leader_student_id
    assert "members" in result
    assert len(result["members"]) > 0
    
    # 验证成员信息包含学生姓名
    member = result["members"][0]
    assert "student_id" in member
    assert "student_name" in member
    assert "joined_at" in member
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_get_group_with_members -v
```

预期输出：FAIL - `ImportError: cannot import name 'get_group_with_members'`

- [ ] **Step 3: 实现获取小组详情函数**

```python
# backend/app/crud/group.py
def get_group_with_members(session: Session, group_id: int) -> Optional[dict]:
    """获取小组详情，包含成员列表和学生姓名"""
    from app.models import Student
    
    group = session.get(Group, group_id)
    if not group:
        return None
    
    # 查询成员
    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == group_id)
    ).all()
    
    # 关联学生姓名
    member_list = []
    for member in members:
        student = session.exec(
            select(Student).where(Student.student_id == member.student_id)
        ).first()
        member_list.append({
            "student_id": member.student_id,
            "student_name": student.name if student else "未知",
            "joined_at": member.joined_at
        })
    
    return {
        "id": group.id,
        "class_name": group.class_name,
        "name": group.name,
        "leader_student_id": group.leader_student_id,
        "is_active": group.is_active,
        "created_at": group.created_at,
        "members": member_list
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_get_group_with_members -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/crud/group.py tests/unit/crud/test_group.py
git commit -m "feat(backend): add get_group_with_members CRUD function"
```

---

## Task 2: 后端 CRUD 层 - 踢出成员

**Files:**
- Modify: `backend/app/crud/group.py`
- Test: `tests/unit/crud/test_group.py`

- [ ] **Step 1: 编写踢出成员的失败测试**

```python
# tests/unit/crud/test_group.py
def test_remove_group_member(session, test_group, test_students):
    """测试踢出小组成员"""
    from app.crud.group import remove_group_member
    
    # 获取一个非组长成员
    member = test_students[1]  # 假设第二个学生是普通成员
    
    result = remove_group_member(session, test_group.id, member.student_id)
    
    assert result is True
    
    # 验证成员已被移除
    remaining_members = session.exec(
        select(GroupMember).where(GroupMember.group_id == test_group.id)
    ).all()
    assert len(remaining_members) == 1  # 只剩组长
    assert remaining_members[0].student_id == test_group.leader_student_id
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_remove_group_member -v
```

预期输出：FAIL - `ImportError: cannot import name 'remove_group_member'`

- [ ] **Step 3: 实现踢出成员函数**

```python
# backend/app/crud/group.py
def remove_group_member(session: Session, group_id: int, student_id: str) -> bool:
    """踢出小组成员，如果踢出组长则自动转让"""
    group = session.get(Group, group_id)
    if not group or not group.is_active:
        return False
    
    # 查询成员
    member = session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.student_id == student_id
        )
    ).first()
    if not member:
        return False
    
    # 如果踢出的是组长
    if group.leader_student_id == student_id:
        # 查询其他成员
        other_members = session.exec(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.student_id != student_id
            )
        ).all()
        
        if other_members:
            # 转让组长给第一个成员
            group.leader_student_id = other_members[0].student_id
            session.add(group)
        else:
            # 没有其他成员，解散小组
            group.is_active = False
            session.add(group)
    
    # 删除成员
    session.delete(member)
    session.commit()
    return True
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_remove_group_member -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/crud/group.py
git commit -m "feat(backend): add remove_group_member CRUD function"
```

---

## Task 3: 后端 CRUD 层 - 解散小组

**Files:**
- Modify: `backend/app/crud/group.py`
- Test: `tests/unit/crud/test_group.py`

- [ ] **Step 1: 编写解散小组的失败测试**

```python
# tests/unit/crud/test_group.py
def test_dissolve_group(session, test_group):
    """测试解散小组"""
    from app.crud.group import dissolve_group
    
    result = dissolve_group(session, test_group.id)
    
    assert result is True
    
    # 验证小组已标记为非活跃
    group = session.get(Group, test_group.id)
    assert group.is_active is False
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_dissolve_group -v
```

预期输出：FAIL - `ImportError: cannot import name 'dissolve_group'`

- [ ] **Step 3: 实现解散小组函数**

```python
# backend/app/crud/group.py
def dissolve_group(session: Session, group_id: int) -> bool:
    """解散小组（标记为非活跃）"""
    from app.models.group import GroupTask
    
    group = session.get(Group, group_id)
    if not group or not group.is_active:
        return False
    
    # 检查是否处于互评阶段
    evaluating_task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == group.class_name,
            GroupTask.status == "evaluating"
        )
    ).first()
    if evaluating_task:
        raise ValueError("班级正在互评阶段，不可解散小组")
    
    # 标记为非活跃
    group.is_active = False
    session.add(group)
    session.commit()
    return True
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_dissolve_group -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/crud/group.py
git commit -m "feat(backend): add dissolve_group CRUD function"
```

---

## Task 4: 后端 API 层 - 获取小组详情

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写获取小组详情 API 的失败测试**

```python
# tests/integration/test_groups_api.py
def test_get_group_detail(client, teacher_token, test_group):
    """测试获取小组详情 API"""
    response = client.get(
        f"/teacher/groups/{test_group.id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == test_group.id
    assert data["data"]["name"] == test_group.name
    assert "members" in data["data"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_get_group_detail -v
```

预期输出：FAIL - `404 Not Found`

- [ ] **Step 3: 实现获取小组详情 API**

```python
# backend/app/api/routes/groups.py
@router.get("/teacher/groups/{group_id}", response_model=ApiResponse[dict])
async def api_get_group_detail(
    group_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """获取小组详情，包含成员列表"""
    from app.crud.group import get_group_with_members
    
    group_data = get_group_with_members(session, group_id)
    if not group_data:
        raise HTTPException(status_code=404, detail="小组不存在")
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: group_data,
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_get_group_detail -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py tests/integration/test_groups_api.py
git commit -m "feat(backend): add get_group_detail API endpoint"
```

---

## Task 5: 后端 API 层 - 踢出成员

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写踢出成员 API 的失败测试**

```python
# tests/integration/test_groups_api.py
def test_remove_member(client, teacher_token, test_group, test_students):
    """测试踢出成员 API"""
    member = test_students[1]
    
    response = client.delete(
        f"/teacher/groups/{test_group.id}/members/{member.student_id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "成员已踢出"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_remove_member -v
```

预期输出：FAIL - `405 Method Not Allowed`

- [ ] **Step 3: 实现踢出成员 API**

```python
# backend/app/api/routes/groups.py
@router.delete("/teacher/groups/{group_id}/members/{student_id}", response_model=ApiResponse)
async def api_remove_member(
    group_id: int,
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """踢出小组成员"""
    from app.crud.group import remove_group_member
    
    success = remove_group_member(session, group_id, student_id)
    if not success:
        raise HTTPException(status_code=400, detail="踢出失败，成员可能不存在")
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "成员已踢出",
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_remove_member -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py
git commit -m "feat(backend): add remove_member API endpoint"
```

---

## Task 6: 后端 API 层 - 解散小组

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写解散小组 API 的失败测试**

```python
# tests/integration/test_groups_api.py
def test_dissolve_group(client, teacher_token, test_group):
    """测试解散小组 API"""
    response = client.delete(
        f"/teacher/groups/{test_group.id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "小组已解散"
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_dissolve_group -v
```

预期输出：FAIL - `405 Method Not Allowed`

- [ ] **Step 3: 实现解散小组 API**

```python
# backend/app/api/routes/groups.py
@router.delete("/teacher/groups/{group_id}", response_model=ApiResponse)
async def api_dissolve_group(
    group_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_teacher),
):
    """解散小组"""
    from app.crud.group import dissolve_group
    
    try:
        success = dissolve_group(session, group_id)
        if not success:
            raise HTTPException(status_code=404, detail="小组不存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "小组已解散",
    }
```

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_dissolve_group -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py
git commit -m "feat(backend): add dissolve_group API endpoint"
```

---

## Task 7: 前端 API 层 - 新增类型和 API 函数

**Files:**
- Modify: `frontend-v3/src/types/api.ts`
- Modify: `frontend-v3/src/api/groups.ts`

- [ ] **Step 1: 新增类型定义**

```typescript
// frontend-v3/src/types/api.ts
export interface GroupMember {
  student_id: string
  student_name: string
  joined_at: string
}

export interface GroupDetail {
  id: number
  class_name: string
  name: string
  leader_student_id: string
  is_active: boolean
  created_at: string
  members: GroupMember[]
}
```

- [ ] **Step 2: 新增 API 函数**

```typescript
// frontend-v3/src/api/groups.ts
import type { GroupDetail } from '@/types/api'

export const groupsApi = {
  // ... 现有函数
  
  getGroupDetail: (groupId: number): Promise<GroupDetail> =>
    get(`/teacher/groups/${groupId}`),
  
  removeMember: (groupId: number, studentId: string): Promise<void> =>
    delete(`/teacher/groups/${groupId}/members/${studentId}`),
  
  dissolveGroup: (groupId: number): Promise<void> =>
    delete(`/teacher/groups/${groupId}`),
}
```

- [ ] **Step 3: 提交代码**

```bash
git add frontend-v3/src/types/api.ts frontend-v3/src/api/groups.ts
git commit -m "feat(frontend): add group detail API types and functions"
```

---

## Task 8: 前端组件 - 修改小组管理页面

**Files:**
- Modify: `frontend-v3/src/views/teacher/Groups.vue`
- Test: `frontend-v3/test/views/teacher/Groups.spec.ts`

- [ ] **Step 1: 编写展开显示成员的失败测试**

```typescript
// frontend-v3/test/views/teacher/Groups.spec.ts
it('shows members when group card is expanded', async () => {
  // Mock API 返回小组详情
  const mockGroupDetail = {
    id: 1,
    class_name: '计算机1班',
    name: '第一组',
    leader_student_id: '2024001',
    is_active: true,
    created_at: '2026-05-07T10:00:00',
    members: [
      { student_id: '2024001', student_name: '张三', joined_at: '2026-05-07T10:00:00' },
      { student_id: '2024002', student_name: '李四', joined_at: '2026-05-07T10:00:00' }
    ]
  }
  
  // 模拟点击展开
  const groupCard = wrapper.find('[data-testid="group-card-1"]')
  await groupCard.trigger('click')
  
  // 验证成员列表显示
  expect(wrapper.text()).toContain('张三')
  expect(wrapper.text()).toContain('李四')
})
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager/frontend-v3
pnpm test:run test/views/teacher/Groups.spec.ts
```

预期输出：FAIL - 找不到 `[data-testid="group-card-1"]`

- [ ] **Step 3: 修改 Groups.vue 添加展开/收起功能**

```vue
<!-- frontend-v3/src/views/teacher/Groups.vue -->
<script setup lang="ts">
// ... 现有代码 ...

// 新增状态
const expandedGroupId = ref<number | null>(null)
const groupDetail = ref<GroupDetail | null>(null)
const loadingDetail = ref(false)

// 展开/收起小组
async function toggleGroup(groupId: number) {
  if (expandedGroupId.value === groupId) {
    expandedGroupId.value = null
    groupDetail.value = null
  } else {
    expandedGroupId.value = groupId
    loadingDetail.value = true
    try {
      groupDetail.value = await groupsApi.getGroupDetail(groupId)
    } catch (err) {
      toastError(getErrorMessage(err) || '获取小组详情失败')
    } finally {
      loadingDetail.value = false
    }
  }
}
</script>

<template>
  <!-- 现有代码 ... -->
  
  <!-- 修改小组卡片 -->
  <div
    v-for="g in groups"
    :key="g.id"
    class="rounded-xl border border-[#e5e5e5] bg-white p-4"
    :data-testid="`group-card-${g.id}`"
  >
    <!-- 现有卡片头部 -->
    <div 
      class="flex items-start justify-between cursor-pointer"
      @click="toggleGroup(g.id)"
    >
      <!-- ... 现有代码 ... -->
    </div>
    
    <!-- 新增：展开/收起按钮 -->
    <div class="mt-2 flex gap-2">
      <Button size="sm" variant="outline" @click="openTransfer(g.id)">
        转让组长
      </Button>
      <Button size="sm" variant="destructive" @click="confirmDissolve(g.id, g.name)">
        解散小组
      </Button>
    </div>
    
    <!-- 新增：成员列表（展开时显示） -->
    <div v-if="expandedGroupId === g.id" class="mt-3 border-t pt-3">
      <div v-if="loadingDetail" class="text-sm text-[#737373]">
        加载中...
      </div>
      <div v-else-if="groupDetail" class="space-y-2">
        <div 
          v-for="member in groupDetail.members" 
          :key="member.student_id"
          class="flex items-center justify-between"
        >
          <div class="flex items-center gap-2">
            <span class="text-sm">{{ member.student_name }}</span>
            <span v-if="member.student_id === g.leader_student_id" class="text-xs text-[#6366f1]">(组长)</span>
          </div>
          <Button 
            size="sm" 
            variant="ghost" 
            @click="handleRemoveMember(g.id, member.student_id)"
          >
            踢出
          </Button>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 新增：解散确认对话框 -->
  <Dialog v-model:open="showDissolveDialog" title="解散小组">
    <p>确定要解散小组「{{ dissolvingGroupName }}」吗？此操作不可撤销。</p>
    <template #footer>
      <div class="flex gap-2">
        <Button variant="outline" @click="showDissolveDialog = false">取消</Button>
        <Button variant="destructive" :loading="dissolving" @click="handleDissolve">确认解散</Button>
      </div>
    </template>
  </Dialog>
</template>
```

- [ ] **Step 4: 添加解散小组逻辑**

```vue
<!-- frontend-v3/src/views/teacher/Groups.vue -->
<script setup lang="ts">
// ... 现有代码 ...

// 新增状态
const showDissolveDialog = ref(false)
const dissolvingGroupId = ref<number | null>(null)
const dissolvingGroupName = ref('')
const dissolving = ref(false)

// 确认解散
function confirmDissolve(groupId: number, groupName: string) {
  dissolvingGroupId.value = groupId
  dissolvingGroupName.value = groupName
  showDissolveDialog.value = true
}

// 解散小组
async function handleDissolve() {
  if (!dissolvingGroupId.value) return
  try {
    dissolving.value = true
    await groupsApi.dissolveGroup(dissolvingGroupId.value)
    toastSuccess('小组已解散')
    showDissolveDialog.value = false
    queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
  } catch (err) {
    toastError(getErrorMessage(err) || '解散失败')
  } finally {
    dissolving.value = false
  }
}

// 踢出成员
async function handleRemoveMember(groupId: number, studentId: string) {
  try {
    await groupsApi.removeMember(groupId, studentId)
    toastSuccess('成员已踢出')
    // 刷新小组列表和详情
    queryClient.invalidateQueries({ queryKey: ['teacher-groups'] })
    if (expandedGroupId.value === groupId) {
      groupDetail.value = await groupsApi.getGroupDetail(groupId)
    }
  } catch (err) {
    toastError(getErrorMessage(err) || '踢出失败')
  }
}
</script>
```

- [ ] **Step 5: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager/frontend-v3
pnpm test:run test/views/teacher/Groups.spec.ts
```

预期输出：PASS

- [ ] **Step 6: 提交代码**

```bash
git add frontend-v3/src/views/teacher/Groups.vue frontend-v3/test/views/teacher/Groups.spec.ts
git commit -m "feat(frontend): add group member management UI"
```

---

## Task 9: 集成测试 - 完整功能验证

**Files:**
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写完整的集成测试**

```python
# tests/integration/test_groups_api.py
def test_group_member_management_flow(client, teacher_token, test_group, test_students):
    """测试完整的小组成员管理流程"""
    
    # 1. 获取小组详情
    response = client.get(
        f"/teacher/groups/{test_group.id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    group_data = response.json()["data"]
    assert len(group_data["members"]) == 2
    
    # 2. 踢出一个成员
    member = test_students[1]
    response = client.delete(
        f"/teacher/groups/{test_group.id}/members/{member.student_id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    
    # 3. 验证成员已减少
    response = client.get(
        f"/teacher/groups/{test_group.id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
    group_data = response.json()["data"]
    assert len(group_data["members"]) == 1
    
    # 4. 解散小组
    response = client.delete(
        f"/teacher/groups/{test_group.id}",
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert response.status_code == 200
```

- [ ] **Step 2: 运行集成测试**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_group_member_management_flow -v
```

预期输出：PASS

- [ ] **Step 3: 提交代码**

```bash
git add tests/integration/test_groups_api.py
git commit -m "test: add integration test for group member management"
```

---

## 自我审查

**1. Spec 覆盖检查：**
- ✅ 查看小组成员 - Task 1, 4, 8
- ✅ 踢出成员 - Task 2, 5, 8
- ✅ 解散小组 - Task 3, 6, 8
- ✅ 组长自动转让 - Task 2
- ✅ 互评阶段检查 - Task 3

**2. 占位符扫描：**
- ✅ 无 "TBD", "TODO", "implement later"
- ✅ 所有步骤都包含实际代码
- ✅ 所有命令都包含预期输出

**3. 类型一致性检查：**
- ✅ CRUD 函数名与 API 端点一致
- ✅ 前端类型定义与后端响应一致
- ✅ 测试断言与实现逻辑一致

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-07-group-member-management.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - 我为每个任务分发一个新的 subagent，任务之间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中执行任务，批量执行并设置检查点

**Which approach?**
