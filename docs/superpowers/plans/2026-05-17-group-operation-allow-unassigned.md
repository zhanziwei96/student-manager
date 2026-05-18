# 合作项目启动后允许未分配小组学生操作实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修改后端 API 逻辑，允许未分配小组的学生在互评阶段创建小组和加入小组

**Architecture:** 修改 `_check_class_not_evaluating` 函数，增加学生ID参数，检查学生是否已有小组；修改退出和解散小组 API，禁止已有小组学生在互评阶段操作

**Tech Stack:** FastAPI, SQLModel, PostgreSQL

---

## 文件结构

**后端修改：**
- `backend/app/api/routes/groups.py` - 修改 `_check_class_not_evaluating` 函数和相关 API
- `tests/unit/crud/test_group.py` - 新增单元测试
- `tests/integration/test_groups_api.py` - 新增集成测试

---

## Task 1: 修改 `_check_class_not_evaluating` 函数

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/unit/crud/test_group.py`

- [ ] **Step 1: 编写测试 - 未分配小组学生在互评阶段可以创建小组**

```python
# tests/unit/crud/test_group.py
def test_check_class_not_evaluating_allows_unassigned_student(session, evaluating_task, unassigned_student):
    """测试未分配小组学生在互评阶段可以创建和加入小组"""
    from app.api.routes.groups import _check_class_not_evaluating
    
    # 不应抛出异常
    _check_class_not_evaluating(session, evaluating_task.class_name, unassigned_student.student_id)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_check_class_not_evaluating_allows_unassigned_student -v
```

预期输出：FAIL - `_check_class_not_evaluating() takes 2 positional arguments but 3 were given`

- [ ] **Step 3: 修改 `_check_class_not_evaluating` 函数**

```python
# backend/app/api/routes/groups.py
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

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/unit/crud/test_group.py::test_check_class_not_evaluating_allows_unassigned_student -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py tests/unit/crud/test_group.py
git commit -m "feat(backend): modify _check_class_not_evaluating to allow unassigned students"
```

---

## Task 2: 修改创建小组 API

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写测试 - 互评阶段未分配学生可以创建小组**

```python
# tests/integration/test_groups_api.py
def test_create_group_during_evaluation(client, student_token, evaluating_task, unassigned_student):
    """测试互评阶段未分配学生可以创建小组"""
    response = client.post(
        "/student/groups",
        json={"class_name": evaluating_task.class_name, "name": "新小组"},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "group_id" in data["data"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_create_group_during_evaluation -v
```

预期输出：FAIL - `班级正在互评阶段，不可变更小组`

- [ ] **Step 3: 修改创建小组 API**

```python
# backend/app/api/routes/groups.py
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

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_create_group_during_evaluation -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py
git commit -m "feat(backend): modify create group API to pass student ID"
```

---

## Task 3: 修改加入小组 API

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写测试 - 互评阶段未分配学生可以加入小组**

```python
# tests/integration/test_groups_api.py
def test_join_group_during_evaluation(client, student_token, evaluating_task, test_group, unassigned_student):
    """测试互评阶段未分配学生可以加入小组"""
    response = client.post(
        f"/student/groups/{test_group.id}/join",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "request_id" in data["data"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_join_group_during_evaluation -v
```

预期输出：FAIL - `班级正在互评阶段，不可变更小组`

- [ ] **Step 3: 修改加入小组 API**

```python
# backend/app/api/routes/groups.py
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

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_join_group_during_evaluation -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py
git commit -m "feat(backend): modify join group API to pass student ID"
```

---

## Task 4: 修改退出小组 API

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写测试 - 互评阶段已有小组学生不能退出小组**

```python
# tests/integration/test_groups_api.py
def test_leave_group_during_evaluation(client, student_token, evaluating_task, test_group, assigned_student):
    """测试互评阶段已有小组学生不能退出小组"""
    response = client.post(
        "/student/groups/leave",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "班级正在互评阶段，不可退出小组" in data["detail"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_leave_group_during_evaluation -v
```

预期输出：FAIL - `404 Not Found` (API 不存在)

- [ ] **Step 3: 添加退出小组 API**

```python
# backend/app/api/routes/groups.py
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

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_leave_group_during_evaluation -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py
git commit -m "feat(backend): add leave group API with evaluation check"
```

---

## Task 5: 修改解散小组 API

**Files:**
- Modify: `backend/app/api/routes/groups.py`
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写测试 - 互评阶段已有小组学生不能解散小组**

```python
# tests/integration/test_groups_api.py
def test_dissolve_group_during_evaluation(client, student_token, evaluating_task, test_group, assigned_student):
    """测试互评阶段已有小组学生不能解散小组"""
    response = client.post(
        "/student/groups/dissolution-request",
        json={"reason": "测试解散"},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "班级正在互评阶段，不可解散小组" in data["detail"]
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_dissolve_group_during_evaluation -v
```

预期输出：FAIL - `班级正在互评阶段，不可解散小组` (预期的错误信息不匹配)

- [ ] **Step 3: 修改解散小组 API**

```python
# backend/app/api/routes/groups.py
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

- [ ] **Step 4: 运行测试验证通过**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_dissolve_group_during_evaluation -v
```

预期输出：PASS

- [ ] **Step 5: 提交代码**

```bash
git add backend/app/api/routes/groups.py
git commit -m "feat(backend): modify dissolve group API with evaluation check"
```

---

## Task 6: 集成测试 - 完整功能验证

**Files:**
- Test: `tests/integration/test_groups_api.py`

- [ ] **Step 1: 编写完整的集成测试**

```python
# tests/integration/test_groups_api.py
def test_group_operation_during_evaluation_flow(client, student_token, evaluating_task, test_group, unassigned_student, assigned_student):
    """测试互评阶段小组操作完整流程"""
    
    # 1. 未分配学生可以创建小组
    response = client.post(
        "/student/groups",
        json={"class_name": evaluating_task.class_name, "name": "新小组"},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # 2. 未分配学生可以加入小组
    response = client.post(
        f"/student/groups/{test_group.id}/join",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # 3. 已有小组学生不能退出小组
    response = client.post(
        "/student/groups/leave",
        headers={"Authorization": f"Bearer {assigned_student_token}"}
    )
    assert response.status_code == 400
    assert "班级正在互评阶段，不可退出小组" in response.json()["detail"]
    
    # 4. 已有小组学生不能解散小组
    response = client.post(
        "/student/groups/dissolution-request",
        json={"reason": "测试解散"},
        headers={"Authorization": f"Bearer {assigned_student_token}"}
    )
    assert response.status_code == 400
    assert "班级正在互评阶段，不可解散小组" in response.json()["detail"]
```

- [ ] **Step 2: 运行集成测试**

```bash
cd /home/yufeng/student-manager
conda run -n student-manage pytest tests/integration/test_groups_api.py::test_group_operation_during_evaluation_flow -v
```

预期输出：PASS

- [ ] **Step 3: 提交代码**

```bash
git add tests/integration/test_groups_api.py
git commit -m "test: add integration test for group operation during evaluation"
```

---

## 自我审查

**1. Spec 覆盖检查：**
- ✅ 修改 `_check_class_not_evaluating` 函数 - Task 1
- ✅ 修改创建小组 API - Task 2
- ✅ 修改加入小组 API - Task 3
- ✅ 修改退出小组 API - Task 4
- ✅ 修改解散小组 API - Task 5
- ✅ 集成测试 - Task 6

**2. 占位符扫描：**
- ✅ 无 "TBD", "TODO", "implement later"
- ✅ 所有步骤都包含实际代码
- ✅ 所有命令都包含预期输出

**3. 类型一致性检查：**
- ✅ 函数名与 API 端点一致
- ✅ 测试断言与实现逻辑一致

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-17-group-operation-allow-unassigned.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - 我为每个任务分发一个新的 subagent，任务之间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中执行任务，批量执行并设置检查点

**Which approach?**
