# Phase 4d 实施计划：旧成绩体系与旧字段清理 + 审计学期过滤

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除旧成绩体系（subjects/student_subject_scores/Student.score/ScoreLog 与旧综合分排行榜）、删除 User.assigned_classes（教师权限唯一真源 = course_offerings.teacher_id）、补审计日志学期过滤（ADM-13）、移除 .env TERM_CFG 配置。

**Architecture:** 后端沿用既有删除模式（迁移 drop + 模型/CRUD/API 同步删 + 测试清理）；教师班级权限收敛为 offerings 派生单一路径；前端删除科目/分数/班级分配相关旧 UI 与 API 模块。业务表 class_name/semester 字符串冗余列**本轮保留**（过渡 filter 回退逻辑仍需要，作为可选后续单独清理）。

**Tech Stack:** FastAPI + SQLModel + PostgreSQL 12 + Alembic；Vue 3.5 + TypeScript + TanStack Query + vitest（前端 252 测试基线，后端 850 测试基线）

**Spec:** [docs/REQUIREMENTS_BY_ROLE.md](../../docs/REQUIREMENTS_BY_ROLE.md)（ADM-13）+ [docs/SEMESTER_COHORT_REFACTOR_PLAN.md](../../docs/SEMESTER_COHORT_REFACTOR_PLAN.md) v1.2（Phase 4 步骤 4-6）

## Context

Phase 4a/4b/4c 已完成（管理端/教师学生成绩主线/小组系统，已合并 main 推 GitHub）。新成绩体系（enrollments + groups）与权限体系（offerings 派生）已全面上线，旧体系成为死代码。

**现状**：
- 旧成绩：subjects/student_subject_scores/student_subject_score_logs 表 + Student.score 列 + ScoreLog 表；API：/subjects、/student-subject-scores、PUT /students/{id}/score、GET /students/{id}/scores、/students/leaderboard（旧综合分榜，前端已删）
- assigned_classes：User.assigned_classes JSON 列 + get_teacher_accessible_classes 双路径（assigned 优先 → offerings 派生）+ /teacher/classes API（教师自助管班）+ 前端 teacherClasses.ts/ManageClassesDialog
- 审计：AuditLog.semester_id 列已有，crud get_audit_logs 无学期过滤，无审计 API 路由暴露
- 配置：app/core/config.py TermSettings 读取 .env TERM_CFG__*（term.py 已从 semesters 表取当前学期）

**范围外**：业务表 class_name/semester 字符串冗余列删除（transition filter 回退逻辑，可选后续单独清理）。

## Global Constraints

- Python 命令必须用 `conda run -n student-manage`；前端在 frontend-v3/ 用 pnpm（`pnpm test:run`、`pnpm exec vue-tsc --noEmit`）
- 后端测试：项目根目录 `pytest tests/ -q`（xdist 4 分库并行）；测试库靠 SQLModel.metadata 建表，先删废弃表再 drop_all（Phase 4c 模式）
- 分支：从 main 切 `feat/legacy-cleanup`；禁止直接改 main
- 代码质量五原则；前端约束（res.data 自动解包、queryKey 一致性、类型一致性）
- 后端 API 契约：ApiResponseConst 包装；教师权限从 course_offerings.teacher_id 派生（唯一真源）

---

### Task 1: 后端 — 旧成绩体系删除

**Files:**
- Delete: `backend/app/models/subject.py`、`backend/app/crud/subject.py`、`backend/app/crud/student_subject_score.py`
- Delete: `backend/app/api/routes/subjects.py`、`backend/app/api/routes/student_subject_scores.py`、`backend/app/api/routes/leaderboard.py`
- Modify: `backend/app/models/student.py`（删 score 列）、`backend/app/models/checkin.py`（删 ScoreLog 模型）
- Modify: `backend/app/crud/student.py`（删 update_student_score/get_student_score_logs/score 默认值逻辑）
- Modify: `backend/app/crud/__init__.py`、`backend/app/api/routes/__init__.py`、`backend/main.py`（清理导出与注册）
- Modify: `backend/app/api/routes/students.py`（删 PUT /{id}/score、GET /{id}/scores；列表/详情响应删 score 字段）
- Modify: `backend/app/core/config.py`（删 score 配置项）
- Create: `backend/alembic/versions/20260909_remove_legacy_scores.py`（drop subjects/student_subject_scores/student_subject_score_logs/score_logs + students.score 列）
- Test: 删除 `tests/unit/test_subjects*.py`、`tests/integration/test_leaderboard_api.py` 等；更新引用 score 的测试

**Interfaces:**
- Consumes: 无
- Produces: 干净的 enrollments 成绩体系；Task 4 前端可删 score 相关类型

- [ ] **Step 1: 引用扫描**：`grep -rn "Subject\|student_subject\|ScoreLog\|\.score\b" backend/app tests/ --include="*.py"`（逐个清理，测试在 Step 5 统一处理）

- [ ] **Step 2: 删模型与迁移**

```python
# 迁移 20260909_remove_legacy_scores.py（down_revision = 20260909_remove_group_tasks_and_evaluations）
def upgrade() -> None:
    op.drop_table("student_subject_score_logs")
    op.drop_table("student_subject_scores")
    op.drop_table("subjects")
    op.drop_table("score_logs")
    op.drop_column("students", "score")
```

Student 模型删 `score` 字段；checkin.py 删 ScoreLog 类；subject.py/student_subject_score.py 模型文件删除；models/__init__.py 清理导出。

- [ ] **Step 3: 删 crud 与 API**

- crud/subject.py、crud/student_subject_score.py 删除；crud/student.py 删 update_student_score/get_student_score_logs 与 create_student 的 score 默认值（settings.score.default_score → 0 移除）
- routes/subjects.py、student_subject_scores.py、leaderboard.py 删除；students.py 删两个 score 端点与响应 score 字段（列表 student_dict、详情、创建响应的 'score' 键）
- config.py 删 ScoreSettings/score 配置段与 .env.example 对应行
- crud/__init__.py、routes/__init__.py、main.py 清理导出与注册

- [ ] **Step 4: 测试库 conftest 加废弃表清理**（Phase 4c 模式，drop_all 前）：

```python
conn.execute(text(
    "DROP TABLE IF EXISTS student_subject_score_logs, student_subject_scores, "
    "subjects, score_logs CASCADE"
))
```

- [ ] **Step 5: 测试清理与更新**

- 删除：test_leaderboard_api.py、test_subject*、test_student_subject_score*、test_score*（旧成绩）
- 更新：所有引用 `score=` 的 Student 构造（集成/单元测试中 Student(score=60.0) 等参数删除）、断言 score 字段的测试、settings 测试

- [ ] **Step 6: 后端回归 + Commit**（`pytest tests/ -q` 全绿）
Commit: `refactor(api): remove legacy score system (subjects/student_subject_scores/Student.score/ScoreLog)`

---

### Task 2: 后端 — assigned_classes 删除（教师权限纯 offerings 派生）

**Files:**
- Modify: `backend/app/models/user.py`（删 assigned_classes 字段与 get_assigned_classes 方法）
- Modify: `backend/app/api/deps.py`（get_teacher_accessible_classes 简化：纯 offerings.class_scope 派生）
- Delete: `backend/app/api/routes/teacher_classes.py`
- Modify: `backend/app/api/routes/users.py`（CreateTeacherRequest 等删 assigned_classes）
- Modify: `backend/app/api/routes/students.py`（教师分支用 get_teacher_accessible_classes 替代 user_obj.get_assigned_classes()）
- Create: 迁移（users 表 drop assigned_classes 列）
- Test: conftest teacher_user fixture 改 seed offerings；删除 teacher_classes 测试；更新权限测试

**Interfaces:**
- Consumes: Task 1 产物
- Produces: 教师班级权限唯一真源（offerings）；Task 4 前端删 teacherClasses.ts/ManageClassesDialog

- [ ] **Step 1: deps 简化**

```python
def get_teacher_accessible_classes(user: dict, session: Session):
    """教师可访问班级集合（唯一真源：course_offerings.teacher_id 的 class_scope 派生）

    - admin → None（表示不限范围）
    - teacher → 授课教学班 class_scope 逗号拆分的班级名集合
    - 其他角色/无效用户 → []（空集）
    """
    from app.models import CourseOffering, User

    role = user.get("role", "")
    if role == "admin":
        return None
    user_id = user.get("sub")
    if not user_id:
        return []
    user_obj = session.get(User, int(user_id))
    if user_obj is None or role != "teacher":
        return []
    offerings = session.exec(select(CourseOffering).where(
        CourseOffering.teacher_id == user_obj.id,
    )).all()
    classes = set()
    for offering in offerings:
        for name in offering.class_scope.split(","):
            name = name.strip()
            if name:
                classes.add(name)
    return sorted(classes)
```

- [ ] **Step 2: User 模型删 assigned_classes + get_assigned_classes**；迁移 drop 列；users.py 请求/响应模型删字段；students.py 教师分支改 `get_teacher_accessible_classes`；teacher_classes.py 删除（含路由注册）

- [ ] **Step 3: conftest teacher_user 改造**（关键：集成测试大量依赖 teacher1 权限覆盖一班/二班）

```python
@pytest.fixture
def teacher_user(test_engine):
    """创建教师用户（授课关系从 course_offerings 派生）"""
    with Session(_test_engine) as session:
        password_hash, salt = generate_password_hash("teacher123")
        user = User(
            username="teacher1",
            name="教师1",
            password_hash=password_hash,
            salt=salt,
            role=UserRoleConst.TEACHER,
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        # 授课教学班（权限唯一真源）：class_scope 覆盖一班/二班
        math = Course(code="MATH1", name="高等数学")
        session.add(math)
        session.commit()
        session.add(CourseOffering(
            course_id=math.id, semester_id=None, teacher_id=user.id,
            teacher_name=user.name, class_scope="一班,二班", status="active",
        ))
        session.commit()
        return user
```

> 注意：class_scope "一班,二班" 覆盖旧 assigned_classes 的 `["一班","二班"]`；无当前学期依赖（派生不限学期）。

- [ ] **Step 4: 测试更新**：删除 teacher_classes 相关测试；assigned_classes 断言测试更新（test_authorization_negative 等）；直接构造 `User(assigned_classes=...)` 的测试删字段

- [ ] **Step 5: 后端回归 + Commit**（全绿）
Commit: `refactor(api): remove User.assigned_classes (offerings as sole teacher permission source)`

---

### Task 3: 后端 — 审计日志学期过滤（ADM-13）+ TERM_CFG 清理

**Files:**
- Modify: `backend/app/crud/audit.py`（get_audit_logs 加 semester_id 过滤）
- Create: `backend/app/api/routes/audit.py`（GET /audit-logs?semester_id=&limit=&offset=，admin 专属）
- Modify: `backend/app/api/routes/__init__.py`、`backend/main.py`
- Modify: `backend/app/core/config.py`（删 TermSettings/TERM_CFG 读取）、`backend/app/core/term.py`（确认无残留引用）
- Modify: `backend/.env.example`（删 TERM_CFG 行）
- Test: `tests/integration/test_audit_api.py`（新建）

**Interfaces:**
- Consumes: `get_current_semester_id(session)`、AuditLog 模型
- Produces: `GET /audit-logs`（admin），前端审计页（如需）可复用

- [ ] **Step 1: 写失败测试**

```python
"""审计日志 API 集成测试：学期过滤 + admin 权限"""
import pytest
from sqlmodel import select
from app.models import AuditLog, Semester, User


def test_audit_logs_filtered_by_semester(admin_client, session):
    """按学期过滤审计日志（ADM-13）"""
    from datetime import date
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                         total_weeks=20, is_current=True))
    session.commit()
    sem = session.exec(select(Semester)).one()
    session.add(AuditLog(user_id=1, user_name="admin", role="admin",
                         action="测试", semester_id=sem.id))
    session.add(AuditLog(user_id=1, user_name="admin", role="admin",
                         action="无学期", semester_id=None))
    session.commit()

    resp = admin_client.get(f"/api/v1/audit-logs?semester_id={sem.id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(log["semester_id"] == sem.id for log in data)

    resp = admin_client.get("/api/v1/audit-logs")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 2


def test_audit_logs_require_admin(teacher_client):
    """非管理员 403"""
    resp = teacher_client.get("/api/v1/audit-logs")
    assert resp.status_code == 403
```

- [ ] **Step 2: 实现 crud 过滤 + 路由**

```python
# crud/audit.py
def get_audit_logs(session, limit=100, offset=0, semester_id=None):
    """获取审计日志列表（可按学期过滤）"""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if semester_id is not None:
        query = query.where(AuditLog.semester_id == semester_id)
    return list(session.exec(query.offset(offset).limit(limit)).all())

# routes/audit.py
@router.get("/audit-logs", response_model=ApiResponse[list])
def list_audit_logs(
    semester_id: Optional[int] = Query(None, description="按学期过滤"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin),
):
    """审计日志列表（仅管理员，支持学期过滤）"""
    logs = get_audit_logs(session, limit=limit, offset=offset, semester_id=semester_id)
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [
        {
            "id": log.id, "user_id": log.user_id, "user_name": log.user_name,
            "role": log.role, "action": log.action, "resource": log.resource,
            "method": log.method, "status_code": log.status_code,
            "semester_id": log.semester_id, "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]}
```

- [ ] **Step 3: TERM_CFG 清理**：config.py 删 TermSettings 类与 `term_cfg` 属性；term.py 若引用 settings.term_cfg 则删除（get_current_term 已从 semesters 表）；.env.example 删 TERM_CFG__* 行

- [ ] **Step 4: 注册路由 + 运行测试 + Commit**
Commit: `feat(api): audit logs semester filter (ADM-13) + remove TERM_CFG config`

---

### Task 4: 前端 — 旧科目/分数/班级分配清理

**Files:**
- Delete: `frontend-v3/src/api/subjects.ts`、`frontend-v3/src/api/teacherClasses.ts`
- Delete: `frontend-v3/src/composables/useSubjects.ts`、`frontend-v3/src/composables/useStudentScoreLogs.ts`
- Delete: `frontend-v3/src/views/teacher/Subjects.vue`、`frontend-v3/src/components/admin/ManageClassesDialog.vue`
- Modify: `frontend-v3/src/views/admin/Students.vue`（删科目分数展开行/调整弹窗与 score 列）
- Modify: `frontend-v3/src/views/teacher/Students.vue`（删平均分/科目分数操作，分数列移除）
- Modify: `frontend-v3/src/views/student/Dashboard.vue`（删综合分展示）
- Modify: `frontend-v3/src/types/api.ts`（删 Subject/StudentSubjectScore/ScoreLog/Student.score/StatsData.average_score 等）
- Modify: `frontend-v3/src/api/index.ts`、`composables/index.ts`、`router/index.ts`、`layouts/DashboardLayout.vue`、`MobileDrawer.vue`（导航删"科目管理"）
- Modify: `frontend-v3/src/views/admin/Teachers.vue`（删"管理班级"按钮与弹窗）
- Test: 删除对应 spec（Subjects/ManageClassesDialog/Leaderboard 已删等），更新引用 score 的 spec

**Interfaces:**
- Consumes: Task 1/2 后端产物
- Produces: 前端最终形态（无旧成绩 UI）

- [ ] **Step 1: 删除文件与导航**（subjects/teacherClasses/Subjects.vue/ManageClassesDialog + 路由 subjects（admin/teacher）+ 导航"科目管理"两处）

- [ ] **Step 2: admin Students.vue 清理**（删：科目分数展开行、subject-scores query、调整科目分数 Dialog、桌面表格"分数"列、移动端分数显示——学籍/转班保留）

- [ ] **Step 3: teacher Students.vue 清理**（删：平均分统计、科目分数下拉/更新逻辑与 UI）

- [ ] **Step 4: student Dashboard/useStats/类型清理**（综合分展示删除；StatsData 若仅剩 total_students/classes 则同步精简后端 stats？——stats API 的 average_score 计算涉及 Student.score 聚合：后端 stats 端点需同步清理，纳入 Task 1 收尾检查）

- [ ] **Step 5: 测试更新 + type-check + 前端全量 + Commit**
Commit: `refactor(frontend): remove legacy subject/score/class-assignment UI`

---

### Task 5: 全量回归（前后端）+ 合并推送

- [ ] **Step 1: 后端全量** `conda run -n student-manage pytest tests/ -q` → 全绿
- [ ] **Step 2: 前端全量** `cd frontend-v3 && pnpm test:run && pnpm exec vue-tsc --noEmit`
- [ ] **Step 3: finishing-a-development-branch 合并 main + 推送 GitHub**

---

## Self-Review

**Spec 覆盖检查**：
- ✅ 重构计划 Phase 4 步骤 4（审计按学期过滤 ADM-13）→ Task 3
- ✅ 重构计划 Phase 4 步骤 5 部分（Student.score/User.assigned_classes/废弃表 subjects 系列）→ Task 1/2
- ✅ 重构计划 Phase 4 步骤 6（.env TERM_CFG）→ Task 3
- ⏳ 业务表 class_name/semester 字符串列删除（步骤 5 剩余部分）→ 可选后续（transition filter 回退逻辑，不影响功能）
- ✅ 前端旧 UI 清理 → Task 4

**占位符扫描**：无 TODO；stats API 的 average_score 后端清理并入 Task 1 收尾检查（在 Task 4 Step 4 提示同步）。

**类型一致性**：Student 类型删 score 后，filteredStudents 相关 spec 同步；queryKey ['student-subjects'] 删除与 invalidate 同步。

## 分支与执行顺序

- 分支 `feat/legacy-cleanup`（从 main 切出，Task 1-5）
- 每个 Task 验证全绿再进下一 Task；完成后合并 main 并推送
