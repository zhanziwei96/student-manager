# 小组成员管理功能设计文档

**文档版本**: v1.0
**创建日期**: 2026-05-07
**状态**: 设计完成，待实现

---

## 1. 功能概述

### 1.1 需求背景

教师需要管理班级小组，包括：
- 查看小组内所有成员的名字
- 将某个同学踢出小组
- 直接解散某个小组

### 1.2 用户故事

**作为** 教师，
**我希望** 能够查看小组成员列表，并踢出成员或解散小组，
**以便** 更好地管理班级小组结构。

### 1.3 设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 成员列表展示方式 | 点击卡片展开/收起 | 直观、节省空间 |
| 踢出成员操作方式 | 成员旁按钮 | 操作便捷 |
| 解散小组操作方式 | 卡片按钮 + 确认对话框 | 防止误操作 |
| 组长被踢出处理 | 自动转让给其他成员 | 保持小组结构稳定 |
| API 设计 | 后端主导方案 | API 职责清晰 |

---

## 2. 后端 API 设计

### 2.1 新增 API

#### 2.1.1 获取小组详情

**端点**: `GET /teacher/groups/{group_id}`

**描述**: 获取小组详细信息，包括成员列表

**请求参数**:
- `group_id` (路径参数): 小组 ID

**响应格式**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "class_name": "计算机1班",
    "name": "第一组",
    "leader_student_id": "2024001",
    "is_active": true,
    "created_at": "2026-05-07T10:00:00",
    "members": [
      {
        "student_id": "2024001",
        "student_name": "张三",
        "joined_at": "2026-05-07T10:00:00"
      },
      {
        "student_id": "2024002",
        "student_name": "李四",
        "joined_at": "2026-05-07T10:00:00"
      }
    ]
  }
}
```

**业务逻辑**:
1. 验证教师权限
2. 查询小组信息
3. 查询小组成员列表
4. 关联学生姓名（从 Student 表查询）
5. 返回小组详情

#### 2.1.2 踢出成员

**端点**: `DELETE /teacher/groups/{group_id}/members/{student_id}`

**描述**: 将学生从小组中踢出

**请求参数**:
- `group_id` (路径参数): 小组 ID
- `student_id` (路径参数): 学生学号

**响应格式**:
```json
{
  "success": true,
  "message": "成员已踢出"
}
```

**业务逻辑**:
1. 验证教师权限
2. 查询小组是否存在
3. 查询学生是否是小组成员
4. 如果被踢出的是组长：
   - 查询小组其他成员
   - 如果有其他成员，自动转让组长给第一个成员
   - 如果没有其他成员，解散小组（标记为非活跃）
5. 删除成员记录
6. 返回成功响应

#### 2.1.3 解散小组

**端点**: `DELETE /teacher/groups/{group_id}`

**描述**: 解散小组

**请求参数**:
- `group_id` (路径参数): 小组 ID

**响应格式**:
```json
{
  "success": true,
  "message": "小组已解散"
}
```

**业务逻辑**:
1. 验证教师权限
2. 查询小组是否存在
3. 检查小组是否处于互评阶段（如果是，拒绝解散）
4. 标记小组为非活跃（`is_active = False`）
5. 返回成功响应

### 2.2 数据模型变更

**无需新增模型**，复用现有的 `Group` 和 `GroupMember` 模型。

### 2.3 CRUD 层新增函数

#### 2.3.1 获取小组详情（含成员）

```python
def get_group_with_members(session: Session, group_id: int) -> Optional[dict]:
    """获取小组详情，包含成员列表和学生姓名"""
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

#### 2.3.2 踢出成员

```python
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

#### 2.3.3 解散小组

```python
def dissolve_group(session: Session, group_id: int) -> bool:
    """解散小组（标记为非活跃）"""
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

---

## 3. 前端设计

### 3.1 组件结构

**修改文件**: `frontend-v3/src/views/teacher/Groups.vue`

**新增组件**: 无需新增组件，在现有小组卡片中扩展功能

### 3.2 UI 设计

#### 3.2.1 小组卡片扩展

**现有卡片结构**:
```
┌─────────────────────────────────────┐
│ 小组名称                    组长: 张三 │
│ 2 人                                │
│ [转让组长]                          │
└─────────────────────────────────────┘
```

**扩展后卡片结构**:
```
┌─────────────────────────────────────┐
│ 小组名称                    组长: 张三 │
│ 2 人                                │
│ [转让组长] [解散小组]                │
├─────────────────────────────────────┤
│ 成员列表 (展开/收起)                 │
│ ┌─────────────────────────────────┐ │
│ │ 张三 (组长)              [踢出] │ │
│ │ 李四                    [踢出] │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

#### 3.2.2 展开/收起逻辑

- 点击小组卡片头部区域（或展开按钮）展开/收起成员列表
- 展开时显示成员列表，每个成员名字旁有踢出按钮
- 收起时隐藏成员列表

#### 3.2.3 解散小组确认对话框

**对话框内容**:
- 标题: "解散小组"
- 内容: "确定要解散小组「{小组名称}」吗？此操作不可撤销。"
- 按钮: "取消" 和 "确认解散"

### 3.3 状态管理

**新增状态**:
- `expandedGroupId: ref<number | null>(null)` - 当前展开的小组 ID
- `dissolvingGroupId: ref<number | null>(null)` - 正在解散的小组 ID
- `removingMember: ref<{groupId: number, studentId: string} | null>(null)` - 正在踢出的成员

### 3.4 API 调用

**新增 API 函数**:

```typescript
// frontend-v3/src/api/groups.ts
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

**类型定义**:

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

### 3.5 交互流程

#### 3.5.1 展开成员列表

1. 教师点击小组卡片
2. 前端调用 `getGroupDetail` API 获取小组详情
3. 前端展开卡片，显示成员列表
4. 每个成员名字旁显示踢出按钮

#### 3.5.2 踢出成员

1. 教师点击成员旁的踢出按钮
2. 前端调用 `removeMember` API
3. 后端处理踢出逻辑（包括组长转让）
4. 前端刷新小组列表和成员列表
5. 显示成功提示

#### 3.5.3 解散小组

1. 教师点击小组卡片的解散按钮
2. 前端弹出确认对话框
3. 教师确认解散
4. 前端调用 `dissolveGroup` API
5. 后端标记小组为非活跃
6. 前端刷新小组列表
7. 显示成功提示

---

## 4. 错误处理

### 4.1 后端错误处理

| 错误场景 | HTTP 状态码 | 错误信息 |
|----------|-------------|----------|
| 小组不存在 | 404 | "小组不存在" |
| 学生不是小组成员 | 400 | "学生不是小组成员" |
| 班级正在互评阶段 | 400 | "班级正在互评阶段，不可解散小组" |
| 权限不足 | 403 | "权限不足" |

### 4.2 前端错误处理

- API 调用失败时显示错误提示
- 网络错误时显示通用错误信息
- 操作进行中显示加载状态

---

## 5. 测试策略

### 5.1 后端测试

**单元测试**:
- `tests/unit/crud/test_group.py` - 测试 CRUD 函数
  - `test_get_group_with_members` - 测试获取小组详情
  - `test_remove_group_member` - 测试踢出成员
  - `test_remove_group_leader` - 测试踢出组长
  - `test_dissolve_group` - 测试解散小组
  - `test_dissolve_group_during_evaluation` - 测试互评阶段解散

**集成测试**:
- `tests/integration/test_groups_api.py` - 测试 API 端点
  - `test_get_group_detail` - 测试获取小组详情 API
  - `test_remove_member` - 测试踢出成员 API
  - `test_dissolve_group` - 测试解散小组 API

### 5.2 前端测试

**组件测试**:
- `frontend-v3/test/views/teacher/Groups.spec.ts` - 测试小组管理页面
  - `test_expand_group_shows_members` - 测试展开显示成员
  - `test_remove_member_button` - 测试踢出成员按钮
  - `test_dissolve_group_button` - 测试解散小组按钮
  - `test_dissolve_confirmation_dialog` - 测试解散确认对话框

---

## 6. 实现计划

### 6.1 后端实现

1. **CRUD 层**: 新增 `get_group_with_members`, `remove_group_member`, `dissolve_group` 函数
2. **API 层**: 新增 3 个 API 端点
3. **测试**: 编写单元测试和集成测试

### 6.2 前端实现

1. **API 层**: 新增 `getGroupDetail`, `removeMember`, `dissolveGroup` 函数
2. **类型定义**: 新增 `GroupMember`, `GroupDetail` 接口
3. **组件**: 修改 `Groups.vue`，添加展开/收起、踢出、解散功能
4. **测试**: 编写组件测试

### 6.3 验证

1. 运行后端测试: `pytest tests/unit/crud/test_group.py -v`
2. 运行集成测试: `pytest tests/integration/test_groups_api.py -v`
3. 运行前端测试: `cd frontend-v3 && pnpm test:run`
4. 手动测试功能

---

## 7. 设计约束

### 7.1 业务约束

- 互评阶段不允许解散小组
- 踢出组长时自动转让给其他成员
- 解散小组时标记为非活跃（软删除）

### 7.2 技术约束

- 遵循现有的 API 响应格式
- 遵循现有的前端组件规范
- 遵循现有的测试规范

### 7.3 安全约束

- 所有 API 需要教师权限验证
- 防止 SQL 注入（使用参数化查询）
- 防止 XSS 攻击（前端输出转义）

---

## 8. 附录

### 8.1 相关文件

**后端**:
- `backend/app/models/group.py` - 小组数据模型
- `backend/app/crud/group.py` - 小组 CRUD 操作
- `backend/app/api/routes/groups.py` - 小组 API 路由

**前端**:
- `frontend-v3/src/views/teacher/Groups.vue` - 小组管理页面
- `frontend-v3/src/api/groups.ts` - 小组 API 函数
- `frontend-v3/src/types/api.ts` - 类型定义

**测试**:
- `tests/unit/crud/test_group.py` - 后端单元测试
- `tests/integration/test_groups_api.py` - 后端集成测试
- `frontend-v3/test/views/teacher/Groups.spec.ts` - 前端组件测试

### 8.2 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-05-07 | v1.0 | 初始设计文档 |
