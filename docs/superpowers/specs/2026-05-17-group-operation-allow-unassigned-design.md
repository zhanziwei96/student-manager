# 合作项目启动后允许未分配小组学生操作的设计文档

**文档版本**: v1.0
**创建日期**: 2026-05-17
**状态**: 设计完成，待实现

---

## 1. 功能概述

### 1.1 需求背景

在合作项目中，当项目启动后，学生无法更改自己小组。需要修改为：当合作项目启动后，对于未分配小组的学生可以进行创建小组和加入小组。

### 1.2 用户故事

**作为** 未分配小组的学生，
**我希望** 能够在合作项目启动后创建小组和加入小组，
**以便** 参与合作项目。

### 1.3 设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 项目状态限制 | 仅在互评阶段限制 | 在准备和关闭阶段，学生可以自由操作 |
| 操作限制对象 | 已有小组的学生 | 未分配小组的学生需要参与项目 |
| 实现方式 | 修改后端 API 逻辑 | 前端不需要修改 |

---

## 2. 需求详情

### 2.1 项目状态与操作权限

| 项目状态 | 未分配小组学生 | 已有小组学生 |
|----------|----------------|--------------|
| preparing（准备中） | 可以创建小组、加入小组 | 可以退出小组、解散小组 |
| evaluating（互评中） | 可以创建小组、加入小组 | 不能进行任何操作 |
| closed（已关闭） | 可以创建小组、加入小组 | 可以退出小组、解散小组 |

### 2.2 操作说明

**创建小组：** 学生可以创建一个新的小组，并成为该小组的组长。

**加入小组：** 学生可以申请加入一个已存在的小组。

**退出小组：** 学生可以退出当前所在的小组（仅限非互评阶段）。

**解散小组：** 组长可以申请解散小组（仅限非互评阶段）。

---

## 3. 后端 API 修改

### 3.1 修改文件

- `backend/app/api/routes/groups.py`

### 3.2 修改内容

#### 3.2.1 修改 `_check_class_not_evaluating` 函数

**原逻辑：**
```python
def _check_class_not_evaluating(session: Session, class_name: str) -> None:
    """检查班级是否处于互评阶段，若是则拒绝组队操作"""
    evaluating_task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == class_name,
            GroupTask.status == "evaluating",
        )
    ).first()
    if evaluating_task:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="班级正在互评阶段，不可变更小组")
```

**新逻辑：**
```python
def _check_class_not_evaluating(session: Session, class_name: str, student_id: str = None) -> None:
    """检查班级是否处于互评阶段，若是则拒绝组队操作（允许未分配小组的学生创建和加入小组）"""
    evaluating_task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == class_name,
            GroupTask.status == "evaluating",
        )
    ).first()
    if evaluating_task:
        # 如果提供了学生ID，检查该学生是否已有小组
        if student_id:
            from app.crud.group import get_student_active_group
            existing_group = get_student_active_group(session, student_id, class_name)
            if not existing_group:
                # 未分配小组的学生，允许创建和加入小组
                return
        # 已有小组的学生或未提供学生ID，禁止操作
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="班级正在互评阶段，不可变更小组")
```

#### 3.2.2 修改创建小组 API

**修改内容：** 在调用 `_check_class_not_evaluating` 时传入学生ID。

```python
@router.post("/student/groups", response_model=ApiResponse[dict])
async def api_create_group(
    data: CreateGroupRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生创建小组"""
    _check_class_not_evaluating(session, data.class_name, user.get("sub"))
    student_id = user.get("sub", "")
    existing = get_student_active_group(session, student_id, data.class_name)
    if existing:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已在一个小组中")
    group = create_group(session, data.class_name, data.name, student_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"group_id": group.id, "name": group.name},
    }
```

#### 3.2.3 修改加入小组 API

**修改内容：** 在调用 `_check_class_not_evaluating` 时传入学生ID。

```python
@router.post("/student/groups/{group_id}/join", response_model=ApiResponse[dict])
async def api_request_join(
    group_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生申请加入小组"""
    group = get_group(session, group_id)
    if not group or not group.is_active:
        raise HTTPException(status_code=404, detail="小组不存在")
    _check_class_not_evaluating(session, group.class_name, user.get("sub"))
    # 检查小组是否已满
    settings = get_class_group_settings(session, group.class_name)
    if settings:
        current_count = len(get_group_members(session, group.id))
        if current_count >= settings.max_members_per_group:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="小组已满")
    student_id = user.get("sub", "")
    existing = get_student_active_group(session, student_id, group.class_name)
    if existing:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已在一个小组中")
    req = create_membership_request(session, group_id, student_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"request_id": req.id},
    }
```

#### 3.2.4 修改退出小组 API

**修改内容：** 在退出小组时检查是否处于互评阶段。

```python
@router.post("/student/groups/leave", response_model=ApiResponse)
async def api_leave_group(
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生退出小组"""
    student_id = user.get("sub", "")
    # 获取学生当前小组
    from app.models import Student
    student = session.exec(select(Student).where(Student.student_id == student_id)).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 检查是否处于互评阶段
    evaluating_task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == student.class_name,
            GroupTask.status == "evaluating",
        )
    ).first()
    if evaluating_task:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="班级正在互评阶段，不可退出小组")
    
    # 退出小组
    from app.crud.group import get_student_active_group, _remove_student_from_class_groups
    group = get_student_active_group(session, student_id, student.class_name)
    if not group:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="退出失败，可能不在任何小组中")
    _remove_student_from_class_groups(session, student_id, student.class_name)
    
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "已退出小组",
    }
```

#### 3.2.5 修改解散小组 API

**修改内容：** 在解散小组时检查是否处于互评阶段。

```python
@router.post("/student/groups/dissolution-request", response_model=ApiResponse[dict])
async def api_request_dissolution(
    data: DissolutionRequestCreate,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """学生申请解散小组"""
    student_id = user.get("sub", "")
    # 获取学生当前小组
    from app.models import Student
    student = session.exec(select(Student).where(Student.student_id == student_id)).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    
    # 检查是否处于互评阶段
    evaluating_task = session.exec(
        select(GroupTask).where(
            GroupTask.class_name == student.class_name,
            GroupTask.status == "evaluating",
        )
    ).first()
    if evaluating_task:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="班级正在互评阶段，不可解散小组")
    
    # 检查是否是组长
    group = get_student_active_group(session, student_id, student.class_name)
    if not group or group.leader_student_id != student_id:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="只有组长可以申请解散")
    
    # 创建解散申请
    req = create_dissolution_request(session, group.id, data.reason)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"request_id": req.id},
    }
```

---

## 4. 前端修改

**无需修改前端代码**。前端已经根据 API 响应显示相应的操作按钮。

---

## 5. 测试策略

### 5.1 后端测试

**单元测试：**
- `tests/unit/crud/test_group.py` - 测试 CRUD 函数
  - `test_check_class_not_evaluating_with_unassigned_student` - 测试未分配小组学生在互评阶段可以创建和加入小组
  - `test_check_class_not_evaluating_with_assigned_student` - 测试已有小组学生在互评阶段不能进行操作

**集成测试：**
- `tests/integration/test_groups_api.py` - 测试 API 端点
  - `test_create_group_during_evaluation` - 测试互评阶段创建小组
  - `test_join_group_during_evaluation` - 测试互评阶段加入小组
  - `test_leave_group_during_evaluation` - 测试互评阶段退出小组
  - `test_dissolve_group_during_evaluation` - 测试互评阶段解散小组

---

## 6. 实现计划

### 6.1 后端实现

1. **修改 `_check_class_not_evaluating` 函数** - 允许未分配小组的学生创建和加入小组
2. **修改创建小组 API** - 传入学生ID
3. **修改加入小组 API** - 传入学生ID
4. **修改退出小组 API** - 检查是否处于互评阶段
5. **修改解散小组 API** - 检查是否处于互评阶段
6. **编写测试** - 单元测试和集成测试

### 6.2 验证

1. 运行后端测试: `pytest tests/unit/crud/test_group.py -v`
2. 运行集成测试: `pytest tests/integration/test_groups_api.py -v`
3. 手动测试功能

---

## 7. 设计约束

### 7.1 业务约束

- 仅在互评阶段限制已有小组学生的操作
- 未分配小组的学生在任何阶段都可以创建和加入小组
- 已有小组的学生在互评阶段不能进行任何操作

### 7.2 技术约束

- 遵循现有的 API 响应格式
- 遵循现有的测试规范

---

## 8. 附录

### 8.1 相关文件

**后端：**
- `backend/app/api/routes/groups.py` - 小组 API 路由
- `backend/app/crud/group.py` - 小组 CRUD 操作
- `backend/app/models/group.py` - 小组数据模型

**测试：**
- `tests/unit/crud/test_group.py` - 后端单元测试
- `tests/integration/test_groups_api.py` - 后端集成测试

### 8.2 变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-05-17 | v1.0 | 初始设计文档 |
