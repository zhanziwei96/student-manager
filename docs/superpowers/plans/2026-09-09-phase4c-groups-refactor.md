# Phase 4c 实施计划：小组系统重构（任务/互评废弃 + 科目维度迁移）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 小组从"任务式"重构为"科目式"：小组按课程（course_id）划分、持续一学期、累计分加减；废弃任务/互评流程（表/API/页面全部删除）；学生可在不同科目加入不同小组。

**Architecture:** 后端沿用既有路由模式；小组数据锚点 = `groups`（course_id + 班级 + 学期）+ `group_members` + `group_score_logs`（均已建表）。任务/互评 API 与页面直接删除（需求表 ❌ 已确认停用）。前端 Groups.vue/MyGroup.vue 在现有设计系统风格上重构，科目下拉数据源从旧 subjects 切换为 courses。

**Tech Stack:** FastAPI + SQLModel + PostgreSQL 12 + Alembic；Vue 3.5 + TypeScript + TanStack Query + Tailwind v4 + vitest（前端 261 测试基线，后端 880 测试基线）

**Spec:** [docs/REQUIREMENTS_BY_ROLE.md](../../docs/REQUIREMENTS_BY_ROLE.md)（TCH-05/06、STU-05）+ [docs/SEMESTER_COHORT_REFACTOR_PLAN.md](../../docs/SEMESTER_COHORT_REFACTOR_PLAN.md) v1.2（Phase 4 步骤 5）

## Context

Phase 4a/4b 已完成（管理端 + 教师/学生成绩主线，已合并 main 推 GitHub）。用户确认过："小组也是分各个科目的，因为每个科目每个学生可能会分成不同的组"——学生可同时在多科小组中。

**现状**：
- `groups` 表已含 `course_id` 字段（Phase 1 迁移），同时遗留 `subject_id`（旧科目表，本计划删除）
- 小组 API 已存在但科目维度是 subject_id：`POST /student/groups`（CreateGroupRequest.subject_id）、`GET /teacher/groups?class_name=`（响应 subject_name）、`GET /student/groups?class_name=`、`GET /student/groups/my-group`
- 小组分 API：`PUT /groups/{id}/score`（乐观锁）、`GET /groups/{id}/score-logs` 已可用
- 任务/互评 API 待删：`/teacher/group-tasks` 系列 9 个端点 + 学生任务端点（evaluations/scores/results）
- 旧小组排行榜 `GET /groups/leaderboard`（subject_id 参数）已被 Phase 4b 的 `GET /rankings?type=group` 取代，本计划删除
- 前端：Groups.vue（680 行，科目筛选用旧 useSubjects）、MyGroup.vue（325 行）、任务页 4 个（GroupTasks/GroupTaskResults/GroupTaskScore/GroupEvaluations）
- group-collaboration feature composables：useGroups.ts（小组）、useGroupSettings.ts（组设置）、useGroupTasks.ts（任务，删）、useEvaluations.ts（互评，删）

**范围外（Phase 4d）**：subjects/student_subject_scores 旧成绩体系清理（admin Students.vue 科目分数行）、Student.score/User.assigned_classes/业务表字符串列删除、审计学期过滤、.env TERM_CFG 清理。

## Global Constraints

- Python 命令必须用 `conda run -n student-manage`；前端在 frontend-v3/ 用 pnpm（`pnpm test:run`、`pnpm exec vue-tsc --noEmit`）
- 后端测试：项目根目录 `pytest tests/ -q`（xdist 4 分库并行）；迁移：`alembic upgrade head`（测试库靠 SQLModel.metadata 自动建表，迁移仅影响生产库，需同步修改 models）
- 分支：从 main 切 `feat/groups-refactor`；禁止直接改 main
- 代码质量五原则：架构与原有风格一致、原代码可改、不留冗余、不用 trick、实现统一优雅
- 前端约束：API 响应自动解包（lib/api.ts）；修改 queryKey 同步 invalidateQueries；JWT sub 字符串与 API id 数字比较前统一转换
- 后端 API 契约：ApiResponseConst 包装；教师权限从 `course_offerings.teacher_id` 派生；学生只能操作自己的数据
- 前端风格：设计系统白色极简，复用 ui/ 组件，图标 lucide-vue-next

---

### Task 1: 后端 — 小组 API 科目维度迁移（subject_id → course_id）

**Files:**
- Modify: `backend/app/api/routes/groups.py`（CreateGroupRequest、teacher groups 响应、student groups、新增教师建组端点）
- Modify: `backend/app/crud/group.py`（如存在）或小组相关 crud（create_group/get_student_active_group/get_groups_by_class 加 course_id）
- Modify: `backend/app/api/routes/group_scores.py`（删除旧 /groups/leaderboard 端点）
- Test: `tests/integration/test_groups_api.py`（如存在则更新；否则新建小组科目维度测试）

**Interfaces:**
- Consumes: `Course`/`Group`/`GroupMember` 模型、`require_teacher`/`get_current_user`
- Produces:
  - `POST /student/groups` body `{class_name, name, course_id}`（course_id 必填）
  - `POST /teacher/groups` body `{class_name, name, course_id}`（教师建组，TCH-06）
  - `GET /teacher/groups?class_name=&course_id=`（响应 course_id/course_name 替代 subject_id/subject_name）
  - `GET /student/groups?class_name=&course_id=`（可加入小组列表）
  - `GET /student/groups/my-group` → 返回学生本学期全部小组列表 `[{group_id, name, class_name, course_id, course_name, score, leader_name, is_leader}]`（替代旧单对象结构）

- [ ] **Step 1: 定位现有小组测试**（`ls tests/integration/ | grep -i group`；存在则更新断言，不存在则新建）

- [ ] **Step 2: 写失败测试**（tests/integration/test_groups_api.py 新建或更新）

```python
"""小组科目维度 API 集成测试：按课程建组/多科小组/教师建组/小组分"""
from datetime import date

import pytest
from sqlmodel import select

from app.models import Class_, Course, Semester, Student, User


@pytest.fixture
def seed_groups(session, teacher_user, student_user):
    """班/学期/课程基础数据（teacher1 + 学生 S001/S002）"""
    session.add(Class_(name="一班", cohort_year="2026"))
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                         total_weeks=20, is_current=True))
    math = Course(code="MATH1", name="高等数学")
    eng = Course(code="ENG1", name="大学英语")
    session.add(math)
    session.add(eng)
    session.commit()
    # S001 由 student_user fixture 提供；补 S002
    if session.get(Student, "S002") is None:
        session.add(Student(student_id="S002", name="学生2", class_name="一班"))
        session.commit()
    return {"math": math, "eng": eng}


def test_student_creates_group_with_course(student_client, seed_groups):
    """学生按课程建组：数学组创建成功，同科再建被拒，他科可再建"""
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班", "name": "数学一组",
        "course_id": seed_groups["math"].id,
    })
    assert resp.status_code == 200
    math_group_id = resp.json()["data"]["group_id"]

    # 同科目重复建组 → 400
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班", "name": "数学二组",
        "course_id": seed_groups["math"].id,
    })
    assert resp.status_code == 400

    # 不同科目可再建组（学生在不同科目属于不同小组）
    resp = student_client.post("/api/v1/student/groups", json={
        "class_name": "一班", "name": "英语一组",
        "course_id": seed_groups["eng"].id,
    })
    assert resp.status_code == 200

    # 我的小组列表含两个组
    resp = student_client.get("/api/v1/student/groups/my-group")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    courses = {g["course_id"] for g in data}
    assert courses == {seed_groups["math"].id, seed_groups["eng"].id}


def test_teacher_creates_group_and_lists_with_course(teacher_client, seed_groups):
    """教师建组 + 小组列表带课程信息"""
    resp = teacher_client.post("/api/v1/teacher/groups", json={
        "class_name": "一班", "name": "数学A组",
        "course_id": seed_groups["math"].id,
    })
    assert resp.status_code == 200

    resp = teacher_client.get("/api/v1/teacher/groups", params={
        "class_name": "一班", "course_id": seed_groups["math"].id,
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["course_name"] == "高等数学"
    assert "subject_id" not in data[0]


def test_group_score_update(teacher_client, seed_groups, session):
    """小组累计分加减（教师）+ 日志"""
    from app.models import Group
    session.add(Group(name="数学A组", class_name="一班", course_id=seed_groups["math"].id,
                      leader_student_id="S001", score=0.0, is_active=True))
    session.commit()
    g = session.exec(select(Group)).one()

    resp = teacher_client.put(f"/api/v1/groups/{g.id}/score", json={
        "score_change": 5.0, "reason": "课堂表现",
    })
    assert resp.status_code == 200

    resp = teacher_client.get(f"/api/v1/groups/{g.id}/score-logs")
    assert resp.status_code == 200
    logs = resp.json()["data"]
    assert len(logs) == 1
    assert logs[0]["delta"] == 5.0


def test_groups_leaderboard_removed(teacher_client):
    """旧小组排行榜端点已删除（新 /rankings?type=group 取代）→ 404"""
    resp = teacher_client.get("/api/v1/groups/leaderboard")
    assert resp.status_code == 404
```

- [ ] **Step 3: 运行确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_groups_api.py -q`
Expected: FAIL（course_id 参数缺失/404）

- [ ] **Step 4: 实现科目维度迁移**

groups.py 改动要点：

```python
class CreateGroupRequest(BaseModel):
    class_name: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    course_id: int = Field(..., description="课程ID（小组按科目划分）")
```

- `api_student_create_group`：校验 `session.get(Course, data.course_id)` 存在；`get_student_active_group(session, student_id, class_name, course_id=data.course_id)`（按科目查重）
- `api_teacher_groups`：加 `course_id: Optional[int] = Query(None)` 过滤；响应 `course_name`（join Course）替代 subject 字段
- `api_student_groups`：加 course_id 过滤
- `GET /student/groups/my-group`：改为返回列表（学生本学期全部小组 + 课程名 + 分数 + 是否组长）
- 新增 `POST /teacher/groups`（require_teacher，body 同 CreateGroupRequest，教师可代建）

crud 改动（`backend/app/crud/group.py` 或 crud/__init__.py 中定义处）：

```python
def get_student_active_group(session, student_id, class_name, course_id=None):
    """学生当前小组（按科目划分：同科目唯一）"""
    query = select(Group).where(
        Group.is_active.is_(True),
        Group.class_name == class_name,
        Group.course_id == course_id,
    ).where(
        Group.id.in_(
            select(GroupMember.group_id).where(GroupMember.student_id == student_id)
        )
    )
    return session.exec(query).first()
```

- 删除 group_scores.py 的 `/groups/leaderboard` 端点与 crud `get_group_leaderboard`（确认无其他引用后）

- [ ] **Step 5: 运行测试通过 + 集成回归 + Commit**

Run: `conda run -n student-manage pytest tests/integration/test_groups_api.py -q` → PASS
Commit: `feat(groups): course-based group API (subject_id -> course_id, teacher create group)`

---

### Task 2: 后端 — 任务/互评流程废弃（API/CRUD/表删除）

**Files:**
- Modify: `backend/app/api/routes/groups.py`（删除 group-tasks 系列 9 个端点 + 学生任务端点 + 相关请求模型）
- Modify: `backend/app/crud/__init__.py` 或小组 crud 文件（删除任务/互评 crud 函数）
- Modify: `backend/app/models/group.py`（删除 GroupTask/GroupTaskDimensions/EvaluationAssignment/GroupEvaluationScore 模型 + Group.subject_id 字段）
- Create: `migrations/versions/xxxx_remove_group_tasks_and_subject_id.py`（drop 4 张表 + Group.subject_id 列）
- Test: 删除/更新 `tests/integration/test_group_tasks*.py`、`tests/unit/` 中任务相关测试

**Interfaces:**
- Consumes: Task 1 产物
- Produces: 干净的科目式小组 API 面；前端 Task 3 可安全删除任务页面

- [ ] **Step 1: 定位任务/互评引用**（`grep -rn "group_tasks\|GroupTask\|evaluation" backend/app tests/ --include="*.py" -l`，逐个清理）

- [ ] **Step 2: 删除 API 端点**（groups.py 中 `/teacher/group-tasks` 全部端点、学生 `/student/group-tasks` 系列、CloneGroupTaskRequest/CreateGroupTaskRequest 等模型）

- [ ] **Step 3: 删除 crud 函数**（create_group_task/get_group_task/get_group_tasks_by_class/get_task_dimensions/start_group_task/close_group_task/submit_teacher_score/get_task_results/submit_student_scores/get_evaluation_assignments/clone_group_task/delete_group_task 等）

- [ ] **Step 4: 删除模型 + 迁移**

models/group.py 删除 4 个表模型与 Group.subject_id；迁移：

```python
"""remove group tasks/evaluations and group.subject_id"""
from alembic import op
import sqlalchemy as sa

revision = "<生成>"
down_revision = "<当前 head>"

def upgrade() -> None:
    op.drop_table("group_evaluation_scores")
    op.drop_table("evaluation_assignments")
    op.drop_table("group_task_dimensions")
    op.drop_table("group_tasks")
    op.drop_column("groups", "subject_id")

def downgrade() -> None:
    # 已停用功能不回滚数据：重建空表结构即可（或 raise NotImplementedError）
    raise NotImplementedError("group_tasks 已废弃，不回滚")
```

- [ ] **Step 5: 清理测试**（删除任务/互评集成与单元测试文件；grep 确认无残留引用）

- [ ] **Step 6: 后端全量回归 + Commit**

Run: `conda run -n student-manage pytest tests/ -q` → 全绿（任务测试删除后数量减少）
Commit: `refactor(groups): remove group tasks/evaluation flow (tables, APIs, crud)`

---

### Task 3: 前端 — 教师小组管理重构 + 任务页面删除

**Files:**
- Modify: `frontend-v3/src/api/groups.ts`（删任务方法/类型；getTeacherGroups 加 courseId；createGroup 改 courseId；教师建组方法）
- Modify: `frontend-v3/src/features/group-collaboration/composables/useGroups.ts`（科目参数贯穿；删 useGroupLeaderboard 引用处）
- Modify: `frontend-v3/src/views/teacher/Groups.vue`（课程下拉替代科目下拉；建组 Dialog；小组分入口；删排行榜内嵌）
- Delete: `frontend-v3/src/views/teacher/GroupTasks.vue`、`GroupTaskResults.vue`、`GroupTaskScore.vue`
- Delete: `frontend-v3/src/features/group-collaboration/composables/useGroupTasks.ts`、`useEvaluations.ts`（互评部分）
- Modify: `frontend-v3/src/router/index.ts`（删 group-tasks 路由）、`layouts/DashboardLayout.vue` + `MobileDrawer.vue`（教师导航删"合作项目"）
- Test: `frontend-v3/test/views/teacher/Groups.spec.ts` 更新或新建；删除任务页 spec

**Interfaces:**
- Consumes: Task 1/2 后端 API；`coursesApi.list()`（已有）
- Produces: 教师小组管理最终形态（建组/组员调整/解散审批/小组分）

- [ ] **Step 1: api/groups.ts 适配**

```ts
// 类型：Group.subject_id/course_id 迁移
export interface Group {
  id: number
  name: string
  leader_student_id: string
  leader_name: string
  course_id: number
  course_name: string
  score: number
  members: { student_id: string; name: string }[]
}

export const groupsApi = {
  // 教师
  getTeacherGroups: (className: string, courseId?: number): Promise<Group[]> =>
    get('/teacher/groups', courseId ? { class_name: className, course_id: courseId } : { class_name: className }),
  createTeacherGroup: (data: { class_name: string; name: string; course_id: number }): Promise<{ group_id: number; name: string }> =>
    post('/teacher/groups', data),
  // 学生
  createGroup: (className: string, name: string, courseId: number): Promise<{ group_id: number; name: string }> =>
    post('/student/groups', { class_name: className, name, course_id: courseId }),
  // ...（getGroups/requestJoin/approveJoin/rejectJoin/updateScore/getScoreLogs 保留，签名随 courseId 微调）
}
```

（删除 getTeacherTasks/createTask/startTask/closeTask/cloneTask/deleteTask/getTaskResults/getEvaluations/submitStudentScores 等方法与 GroupTask 系列类型）

- [ ] **Step 2: Groups.vue 重构**

- 课程下拉（`coursesApi.list()` → courseOptions）+ 班级下拉（保留 useClasses）
- `useTeacherGroups(selectedClass, selectedCourseId)`（course_id 过滤）
- 建组 Dialog：组名 + 课程下拉 → createTeacherGroup → invalidate ['teacher-groups']
- 小组卡片/表格保留现有：成员列表、组长转移、移除组员、解散（审批流程保留）
- 小组分：保留 useGroupScore 加减 Dialog + 日志展开
- 删除 useGroupLeaderboard 内嵌排行榜块（入口改为 router 跳 /teacher/rankings?course_id=）

- [ ] **Step 3: 删除任务页面与导航**

```bash
git rm src/views/teacher/GroupTasks.vue src/views/teacher/GroupTaskResults.vue src/views/teacher/GroupTaskScore.vue
git rm src/features/group-collaboration/composables/useGroupTasks.ts
```

- 路由删除 group-tasks/groups 相关任务路由（group-tasks、group-tasks/:id/results、group-tasks/:id/score——admin 与 teacher 两侧）
- 导航：教师组删"合作项目"（/teacher/group-tasks）；admin 组删 group-tasks 路由（管理员导航无此入口，仅路由）
- useEvaluations.ts：删任务/互评 composables（useStudentGroupTasks/useEvaluations/useSubmitStudentScores 在学生 Task 4 删页面后一并清理——本 Task 先删教师侧 useGroupTasks；学生侧 Task 4）

- [ ] **Step 4: 测试 + type-check + Commit**

Run: `pnpm exec vue-tsc --noEmit && pnpm test:run`
Commit: `feat(teacher-frontend): course-based group management (remove task flow)`

---

### Task 4: 前端 — 学生小组页重构 + MyGrades 补小组分 + 互评页删除

**Files:**
- Modify: `frontend-v3/src/views/student/MyGroup.vue`（重构：按科目查看/建组/入组/小组分）
- Modify: `frontend-v3/src/views/student/MyGrades.vue`（补小组分区块：GET /student/groups/my-group）
- Delete: `frontend-v3/src/views/student/GroupEvaluations.vue` + 路由
- Delete: `frontend-v3/src/features/group-collaboration/composables/useEvaluations.ts` 残余互评函数
- Modify: `frontend-v3/src/api/groups.ts`（getMyGroups 新方法：`GET /student/groups/my-group` 返回列表）
- Test: `frontend-v3/test/views/student/MyGroup.spec.ts` 更新；MyGrades.spec.ts 补小组分用例

**Interfaces:**
- Consumes: Task 1 后端（my-group 列表结构）、`coursesApi.list()`
- Produces: 学生小组最终形态（STU-05）

- [ ] **Step 1: MyGroup.vue 重构**

- 数据：`GET /student/groups/my-group`（我的小组列表：每科一个）+ 科目下拉（courses）
- 展示：所选科目我的小组卡片（组名/组长/分数/成员）或"未入组"空状态
- 未入组：建组 Dialog（组名）+ 加入小组列表（`GET /student/groups?class_name=&course_id=`，组员满员禁用）
- 入组申请：requestJoin → 组长在组内审批（approveJoin/rejectJoin，现有逻辑保留）
- 组长操作：审批入组申请列表

（现有 MyGroup.vue 结构保留可用部分，按上述数据流改造）

- [ ] **Step 2: MyGrades.vue 补小组分**

```ts
// 我的小组分（当前学期每科小组）
const { data: myGroupsData } = useQuery({
  queryKey: ['my-groups', studentId],
  queryFn: () => groupsApi.getMyGroups(),
  enabled: () => !!studentId.value,
})
```

页面加"小组成绩"区块（Card 表格：课程/小组名/小组分），与选课成绩表并列。

- [ ] **Step 3: 删除 GroupEvaluations.vue 与互评残余**

- `git rm src/views/student/GroupEvaluations.vue` + 路由 `/student/group-evaluations` 删除
- useEvaluations.ts 删除 useStudentGroupTasks/useEvaluations/useSubmitStudentScores（无引用后）
- 相关 spec 删除

- [ ] **Step 4: 测试 + type-check + Commit**

Run: `pnpm exec vue-tsc --noEmit && pnpm test:run`
Commit: `feat(student-frontend): course-based my groups + group scores in grades`

---

### Task 5: 全量回归（前后端）+ 合并推送

- [ ] **Step 1: 后端全量回归**

```bash
conda run -n student-manage pytest tests/ -q > /tmp/pytest_phase4c.log 2>&1
tail -3 /tmp/pytest_phase4c.log
```

- [ ] **Step 2: 前端全量 + type-check**

```bash
cd frontend-v3 && pnpm test:run && pnpm exec vue-tsc --noEmit
```

- [ ] **Step 3: finishing-a-development-branch 流程合并 main + 推送 GitHub**

---

## Self-Review

**Spec 覆盖检查**（对照需求表）：
- ✅ TCH-05 小组成绩管理（累计分加减 + 变更日志）→ 现有 API 保留 + Task 3 UI
- ✅ TCH-06 小组管理（建组/组员调整/解散审批，按科目持续一学期）→ Task 1 教师建组端点 + Task 3 Groups.vue
- ✅ STU-05 小组（创建/入组申请/退出/解散申请/查看小组分）→ Task 4 MyGroup.vue + MyGrades 小组分
- ✅ TCH 任务互评停用（需求表 ❌）→ Task 2 后端废弃 + Task 3/4 前端删除
- ✅ "每个科目每个学生可能会分成不同的组"（用户确认）→ Task 1 按 (student, class, course) 建组唯一性
- ⏳ 旧成绩体系（subjects/student_subject_scores）、旧字段删除 → Phase 4d

**占位符扫描**：无 TODO；小组分权限仍按行政班校验（verify_teacher_class_access），Phase 4d 统一迁移到授课维度（不引入两套逻辑）。

**类型一致性**：Group 类型 course_id/course_name 在 Task 3 定义；Task 4 getMyGroups 返回同结构复用；queryKey 约定 `['teacher-groups', className, courseId]`、`['my-groups', studentId]`，invalidate 同步。

## 分支与执行顺序

- 分支 `feat/groups-refactor`（从 main 切出，Task 1-5）
- 每个 Task 验证全绿再进下一 Task；完成后合并 main 并推送
- Phase 4d（旧成绩体系与字段清理）在本计划合并后另立计划
