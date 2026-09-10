# Phase 4b 实施计划：教师端重构 + 学生成绩与排行榜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 教师端从"管班"迁移到"授课"（我的教学班 + 按科目成绩录入 + 4 种排行榜），学生端新增"我的成绩"与"本班科目排行榜"。

**Architecture:** 后端沿用既有路由模式（内联请求模型 + ApiResponseConst + offerings.teacher_id 派生权限）。成绩与排行榜统一以 `enrollments`（个人/期末）与 `groups`（小组累计分，科目维度 course_id）为数据源，废弃旧综合分（Student.score）与旧科目表（subjects）逻辑。前端严格遵循设计系统（白色极简）与 TanStack Query 模式，教师/学生导航同步重构。

**Tech Stack:** FastAPI + SQLModel + PostgreSQL 12；Vue 3.5 + TypeScript + TanStack Query + Tailwind v4 + vitest（前端 260 测试基线）

**Spec:** [docs/REQUIREMENTS_BY_ROLE.md](../../docs/REQUIREMENTS_BY_ROLE.md)（TCH-01/03/04/07、STU-03/04）+ [docs/SEMESTER_COHORT_REFACTOR_PLAN.md](../../docs/SEMESTER_COHORT_REFACTOR_PLAN.md) v1.2

## Context

Phase 4a 已完成（管理端 API + 前端，已合并 main 推 GitHub，后端 872 测试/前端 260 测试全绿）。本计划为 Phase 4b：教师端与成绩/排行榜主线。

**后端现状**（已实现，直接复用）：
- `PUT /enrollments/{id}/score`（个人成绩加减分，乐观锁）与 `PUT /enrollments/{id}/final-score`（期末试卷个人分）已实现，授课教师校验 `offering.teacher_id` ✓
- `PUT /offerings/{id}/final-scores/group`（期末任务小组同分）已实现 ✓
- `GET /students/{id}/enrollments`（我的成绩：课程名/教师名/score/final_score）已实现 ✓
- `groups` 表已是科目式（course_id + score 累计分），`GET /teacher/groups?class_name=` 返回组与成员（小组管理 UI 重构留 Phase 4c）
- 旧排行榜（crud/leaderboard.py）基于废弃的 `Student.score` 综合分，**本计划以新实现替换**

**范围外（后续计划）**：Phase 4c = 小组系统重构（任务/互评流程废弃、科目式小组管理 UI、STU-05）；Phase 4d = 清理（旧字段/废弃表/审计学期过滤/.env 配置）。

## Global Constraints

- Python 命令必须用 `conda run -n student-manage`；前端在 frontend-v3/ 用 pnpm（`pnpm test:run`、`pnpm exec vue-tsc --noEmit`）
- 后端测试：项目根目录 `pytest tests/ -q`（pytest.ini 已含 `-n 4` xdist 分库并行）；前端测试在 frontend-v3/test/
- 分支：从 main 切 `feat/teacher-grades`；禁止直接改 main
- 代码质量五原则：架构与原有风格一致、原代码可改、不留冗余、不用 trick、实现统一优雅
- 前端约束：API 响应只访问 `res.data`（lib/api.ts 已自动解包）；修改 queryKey 同步检查 invalidateQueries；JWT sub 字符串与 API id 数字比较前统一转换
- 后端 API 契约：ApiResponseConst 包装；权限从 `course_offerings.teacher_id` 派生；排行榜排名采用标准竞赛排名（并列同分名次相同，后续名次跳过）
- 前端风格：设计系统白色极简（bg-[#fafafa]、边框 #e5e5e5、文字黑/#737373/#a3a3a3），复用 ui/ 组件（Card/Button/Badge/Dialog/Input/Select/DataContainer），图标 lucide-vue-next

---

### Task 1: 后端 — 教师教学班 API + 成绩排行榜 API + 权限修复

**Files:**
- Create: `backend/app/api/routes/rankings.py`（排行榜新端点）
- Create: `backend/app/crud/ranking.py`（个人/小组榜查询）
- Modify: `backend/app/api/routes/course_offerings.py`（教师教学班列表 + 名单权限修复）
- Modify: `backend/app/api/routes/__init__.py`（注册 rankings_router）
- Modify: `backend/main.py`（注册）
- Test: `tests/integration/test_rankings_api.py`（新建）、`tests/integration/test_admin_management_api.py`（补权限用例）

**Interfaces:**
- Consumes: `get_current_semester_id(session)`（app/core/term.py）、`get_teacher_accessible_classes(user, session)`（app/api/deps.py）、Group/GroupMember/Enrollment/CourseOffering/Course 模型
- Produces:
  - `GET /teacher/offerings` → `[{id, course_id, course_name, course_code, class_scope, capacity, status, enrolled_count, semester_label}]`
  - `GET /rankings`（query: `type=individual|group`, `course_id`, `scope=class|all`, `class_name?`）→ `{type, scope, course_name, classes: [str], entries: [...], my_rank: {...}|null}`
  - `crud/ranking.py::get_individual_ranking(session, course_id, scope, class_name, current_semester_id, limit)` / `get_group_ranking(session, course_id, scope, class_name, current_semester_id, limit)`

- [ ] **Step 1: 写失败测试**（tests/integration/test_rankings_api.py）

```python
"""成绩排行榜 API 集成测试：教师教学班/权限修复/4 榜/学生本班榜"""
from datetime import date

import pytest
from sqlmodel import select

from app.models import Class_, Course, CourseOffering, Enrollment, Semester, Student, User


@pytest.fixture
def seed_rankings(session, teacher_user):
    """届/班/学期/课程/教学班/选课基础数据（teacher1 授两个数学教学班）"""
    session.add(Class_(name="一班", cohort_year="2026"))
    session.add(Class_(name="二班", cohort_year="2026"))
    session.add(Semester(label="2026-2027-1", start_date=date(2026, 9, 7),
                         total_weeks=20, is_current=True))
    math = Course(code="MATH1", name="高等数学")
    eng = Course(code="ENG1", name="大学英语")
    session.add(math)
    session.add(eng)
    other = User(username="t2", name="李老师", password_hash="x", role="teacher")
    session.add(other)
    session.commit()
    sem = session.exec(select(Semester)).one()
    t1 = teacher_user  # conftest fixture（teacher1）
    m1 = CourseOffering(course_id=math.id, semester_id=sem.id, teacher_id=t1.id,
                        teacher_name=t1.name, class_scope="一班", status="active")
    m2 = CourseOffering(course_id=math.id, semester_id=sem.id, teacher_id=t1.id,
                        teacher_name=t1.name, class_scope="二班", status="active")
    e1 = CourseOffering(course_id=eng.id, semester_id=sem.id, teacher_id=other.id,
                        teacher_name="李老师", class_scope="一班", status="active")
    session.add_all([m1, m2, e1])
    session.commit()
    # S001 可能已由 conftest 的 student_user fixture 创建（学生视角用例），get-or-create
    s1 = session.get(Student, "S001")
    if s1 is None:
        s1 = Student(student_id="S001", name="学生1", class_name="一班")
        session.add(s1)
    session.add_all([
        Student(student_id="S002", name="学生2", class_name="一班"),
        Student(student_id="S003", name="学生3", class_name="二班"),
    ])
    session.commit()
    session.add_all([
        Enrollment(student_id="S001", offering_id=m1.id, semester_id=sem.id,
                   score=90.0, status="enrolled"),
        Enrollment(student_id="S002", offering_id=m1.id, semester_id=sem.id,
                   score=80.0, status="enrolled"),
        Enrollment(student_id="S003", offering_id=m2.id, semester_id=sem.id,
                   score=85.0, status="enrolled"),
        Enrollment(student_id="S001", offering_id=e1.id, semester_id=sem.id,
                   score=70.0, status="enrolled"),
    ])
    session.commit()
    return {"math": math, "m1": m1, "m2": m2, "e1": e1}


def test_teacher_offerings_list_only_own(teacher_client, seed_rankings):
    """教师教学班列表：仅本人授课，含课程信息与选课人数"""
    resp = teacher_client.get("/api/v1/teacher/offerings")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2  # teacher1 的两个数学教学班（李老师的英语班不在内）
    assert all(o["course_code"] == "MATH1" for o in data)
    by_scope = {o["class_scope"]: o for o in data}
    assert by_scope["一班"]["enrolled_count"] == 2
    assert by_scope["二班"]["enrolled_count"] == 1


def test_teacher_cannot_list_other_teacher_enrollments(teacher_client, seed_rankings):
    """教师不能查看他人教学班名单 → 403"""
    resp = teacher_client.get(f"/api/v1/offerings/{seed_rankings['e1'].id}/enrollments")
    assert resp.status_code == 403


def test_teacher_can_list_own_enrollments(teacher_client, seed_rankings):
    """教师可查看自己教学班名单 → 200"""
    resp = teacher_client.get(f"/api/v1/offerings/{seed_rankings['m1'].id}/enrollments")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 2


def test_individual_ranking_class_scope(teacher_client, seed_rankings):
    """个人榜·班内：按行政班过滤并按分数降序排名"""
    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["math"].id,
        "scope": "class", "class_name": "一班",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["course_name"] == "高等数学"
    assert data["classes"] == ["一班"]
    assert [e["student_id"] for e in data["entries"]] == ["S001", "S002"]
    assert data["entries"][0]["score"] == 90.0
    assert data["entries"][0]["rank"] == 1


def test_individual_ranking_all_scope(teacher_client, seed_rankings):
    """个人榜·跨班：教师该科目全部教学班合并排名"""
    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["math"].id, "scope": "all",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [e["student_id"] for e in data["entries"]] == ["S001", "S003", "S002"]
    assert sorted(data["classes"]) == ["一班", "二班"]


def test_ranking_teacher_cannot_query_other_course(teacher_client, seed_rankings):
    """教师不能查非本人授课科目排行榜 → 403"""
    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["e1"].course_id, "scope": "all",
    })
    assert resp.status_code == 403


def test_student_ranking_forced_own_class(student_client, seed_rankings):
    """学生排行榜：scope 强制 class 且班取学生自己（S001 在一班）"""
    resp = student_client.get("/api/v1/rankings", params={
        "type": "individual", "course_id": seed_rankings["math"].id, "scope": "all",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["scope"] == "class"
    assert [e["student_id"] for e in data["entries"]] == ["S001", "S002"]  # 只含一班
    assert data["my_rank"]["student_id"] == "S001"
    assert data["my_rank"]["rank"] == 1


def test_group_ranking(teacher_client, seed_rankings, session):
    """小组榜：按科目+班级取小组累计分排名，含成员名单"""
    from app.models import Group, GroupMember

    sem = session.exec(select(Semester)).one()
    g1 = Group(name="第一组", class_name="一班", course_id=seed_rankings["math"].id,
               semester_id=sem.id, leader_student_id="S001", score=95.0, is_active=True)
    g2 = Group(name="第二组", class_name="一班", course_id=seed_rankings["math"].id,
               semester_id=sem.id, leader_student_id="S003", score=88.0, is_active=True)
    session.add_all([g1, g2])
    session.commit()
    session.add_all([
        GroupMember(group_id=g1.id, student_id="S001", student_name="学生1"),
        GroupMember(group_id=g2.id, student_id="S003", student_name="学生3"),
    ])
    session.commit()

    resp = teacher_client.get("/api/v1/rankings", params={
        "type": "group", "course_id": seed_rankings["math"].id,
        "scope": "class", "class_name": "一班",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [e["name"] for e in data["entries"]] == ["第一组", "第二组"]
    assert data["entries"][0]["score"] == 95.0
    assert data["entries"][0]["members"] == ["学生1"]
```

> 注：GroupMember 字段以 `backend/app/models/group.py` 实际定义为准（group_id/student_id/student_name），若字段名有差异执行时同步修正。

- [ ] **Step 2: 运行确认失败**

- [ ] **Step 2: 运行确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_rankings_api.py -q`
Expected: FAIL（路由不存在 404）

- [ ] **Step 3: 实现 crud/ranking.py**

```python
"""成绩排行榜查询 — 个人榜（enrollments.score）/ 小组榜（groups.score），按科目"""
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select
from app.models import CourseOffering, Enrollment, Group, GroupMember, Student


def _rank(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """标准竞赛排名：并列同分名次相同，后续名次跳过"""
    if not entries:
        return []
    entries.sort(key=lambda e: e["score"], reverse=True)
    rank, prev_score, i = 0, None, 0
    for entry in entries:
        i += 1
        if prev_score is None or entry["score"] != prev_score:
            rank = i
        entry["rank"] = rank
        prev_score = entry["score"]
    return entries


def get_individual_ranking(
    session: Session,
    course_id: int,
    scope: str,
    class_name: Optional[str],
    semester_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """个人成绩榜：按科目聚合 enrollments（scope=class 时按行政班过滤）"""
    query = (
        select(Enrollment.student_id, Enrollment.score, Student.name, Student.class_name)
        .join(Student, Enrollment.student_id == Student.student_id)
        .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
        .where(
            CourseOffering.course_id == course_id,
            Enrollment.semester_id == semester_id,
            Enrollment.status == "enrolled",
        )
    )
    if scope == "class" and class_name:
        query = query.where(Student.class_name == class_name)
    rows = session.exec(query).all()
    entries = [
        {"student_id": sid, "name": name, "class_name": cls_name, "score": score}
        for sid, score, name, cls_name in rows
    ]
    return _rank(entries)[:limit]


def get_group_ranking(
    session: Session,
    course_id: int,
    scope: str,
    class_name: Optional[str],
    semester_id: int,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """小组成绩榜：按科目聚合 groups（小组累计分）"""
    query = select(Group).where(
        Group.course_id == course_id,
        Group.semester_id == semester_id,
        Group.is_active.is_(True),
    )
    if scope == "class" and class_name:
        query = query.where(Group.class_name == class_name)
    groups = session.exec(query).all()
    member_rows = session.exec(select(GroupMember).where(
        GroupMember.group_id.in_([g.id for g in groups]),
    )).all()
    members: Dict[int, List[str]] = {}
    for m in member_rows:
        members.setdefault(m.group_id, []).append(m.student_name)
    entries = [
        {"group_id": g.id, "name": g.name, "class_name": g.class_name,
         "score": g.score, "members": members.get(g.id, [])}
        for g in groups
    ]
    return _rank(entries)[:limit]
```

- [ ] **Step 4: 实现 routes/rankings.py**

```python
"""
成绩排行榜 API — 教师 4 榜（个人/小组 × 班内/跨班）+ 学生本班科目榜
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.config import HttpStatus
from app.core.db import get_session
from app.core.jwt import get_current_user
from app.core.term import get_current_semester_id
from app.crud.ranking import get_individual_ranking, get_group_ranking
from app.models import Course, CourseOffering, Student
from app.models.constants import ApiResponseConst, ApiResponse

router = APIRouter(tags=["rankings"])


@router.get("/rankings", response_model=ApiResponse[dict])
def get_rankings(
    type: str = Query(..., pattern="^(individual|group)$", description="个人/小组"),
    course_id: int = Query(..., description="课程ID（科目）"),
    scope: str = Query("class", pattern="^(class|all)$", description="班内/跨班"),
    class_name: Optional[str] = Query(None, description="行政班名（教师 scope=class 时）"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    """成绩排行榜

    教师：可查自己授课科目的个人/小组榜；scope=class 需指定行政班。
    学生：只能查本班（class_name 强制取学生自己的行政班，scope 强制 class）。
    """
    role = user.get("role", "")
    course = session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课程不存在")

    if role == "teacher":
        offering = session.exec(select(CourseOffering).where(
            CourseOffering.course_id == course_id,
            CourseOffering.teacher_id == int(user.get("sub")),
        ).limit(1)).first()
        if offering is None:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="只能查看自己授课科目的排行榜")
    elif role == "student":
        student = session.get(Student, user.get("sub"))
        if student is None:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
        scope = "class"  # 学生只能看班内榜
        class_name = student.class_name
        # 学生只能看自己选过的课
        from app.models import Enrollment
        enrolled = session.exec(select(Enrollment).join(CourseOffering).where(
            Enrollment.student_id == student.student_id,
            CourseOffering.course_id == course_id,
        ).limit(1)).first()
        if enrolled is None:
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="只能查看自己已选课程的排行榜")

    semester_id = get_current_semester_id(session)
    if semester_id is None:
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="当前学期未设置")

    if type == "individual":
        entries = get_individual_ranking(session, course_id, scope, class_name, semester_id)
    else:
        entries = get_group_ranking(session, course_id, scope, class_name, semester_id)

    # 教师 scope=class 时的班级下拉选项：该科目名单中的行政班
    classes = sorted({e["class_name"] for e in entries}) if role == "teacher" else ([class_name] if class_name else [])

    my_rank = None
    if role == "student" and type == "individual":
        my_rank = next((e for e in entries if e["student_id"] == user.get("sub")), None)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "type": type, "scope": scope, "course_name": course.name,
            "classes": classes, "entries": entries, "my_rank": my_rank,
        },
    }
```

- [ ] **Step 5: 实现 GET /teacher/offerings + 权限修复（course_offerings.py）**

在 course_offerings.py 追加（教师教学班端点）：

```python
@router.get("/teacher/offerings", response_model=ApiResponse[list])
def list_teacher_offerings(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher),
):
    """我的教学班：本学期本人授课列表（含课程信息与选课人数）"""
    from app.core.term import get_current_semester_id
    from app.models import Course, User

    user_id = int(user.get("sub"))
    query = select(CourseOffering, Course, func.count(Enrollment.id)).join(
        Course, CourseOffering.course_id == Course.id,
    ).outerjoin(Enrollment, (Enrollment.offering_id == CourseOffering.id)
                & (Enrollment.status == "enrolled")).group_by(CourseOffering.id, Course.id)
    if user.get("role") != "admin":
        query = query.where(CourseOffering.teacher_id == user_id)
    semester_id = get_current_semester_id(session)
    if semester_id is not None:
        query = query.where(CourseOffering.semester_id == semester_id)
    rows = session.exec(query.order_by(Course.name)).all()
    return {ApiResponseConst.SUCCESS: True, ApiResponseConst.DATA: [
        {
            "id": o.id, "course_id": o.course_id, "course_name": c.name,
            "course_code": c.code, "teacher_name": o.teacher_name,
            "class_scope": o.class_scope, "capacity": o.capacity,
            "status": o.status, "enrolled_count": cnt,
        }
        for o, c, cnt in rows
    ]}
```

权限修复（list_offerings_enrollments 教师归属校验）：在 `list_offering_enrollments` 中加：

```python
    if user.get("role") != "admin" and offering.teacher_id != int(user.get("sub")):
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权查看该教学班名单")
```

- [ ] **Step 6: 注册路由**（`routes/__init__.py` 加 `rankings_router`，`main.py` 注册）

- [ ] **Step 7: 运行测试通过**

Run: `conda run -n student-manage pytest tests/integration/test_rankings_api.py tests/integration/test_admin_management_api.py -q`
Expected: PASS

- [ ] **Step 8: 后端相关回归 + Commit**

Run: `conda run -n student-manage pytest tests/integration -q`
Commit: `feat(api): teacher offerings + rankings API (individual/group x class/all)`

---

### Task 2: 前端 — 教师端「我的教学班」+ 成绩录入页面

**Files:**
- Create: `frontend-v3/src/api/rankings.ts`（排行榜 API 模块 + RankingData/RankingEntry 类型）
- Modify: `frontend-v3/src/api/offerings.ts`（加 teacherOfferings 方法）
- Create: `frontend-v3/src/views/teacher/MyOfferings.vue`（我的教学班）
- Create: `frontend-v3/src/views/teacher/OfferingGrades.vue`（成绩录入：个人加减分 + 期末试卷分 + 期末任务同分）
- Modify: `frontend-v3/src/router/index.ts`（`/teacher/my-offerings`、`/teacher/offerings/:id/grades` 路由）
- Modify: `frontend-v3/src/layouts/DashboardLayout.vue` + `components/ui/MobileDrawer.vue`（教师导航：我的教学班替换"我的班级"）
- Test: `frontend-v3/test/views/MyOfferings.spec.ts`、`frontend-v3/test/views/OfferingGrades.spec.ts`

**Interfaces:**
- Consumes: `offeringsApi`（Task 1 后端）、`GET /students/{id}/enrollments` 模式（enrollments API 已有）、`GET /teacher/groups?class_name=`（期末任务同分小组下拉，现有端点）
- Produces: `rankingsApi.getRankings(params)` 供 Task 3/4 使用；`GET /teacher/offerings` 前端方法 `offeringsApi.listMine()`

- [ ] **Step 1: api/rankings.ts**

```ts
import { get } from '@/lib/api'

/** 排行榜查询参数 - 对应后端 /rankings */
export interface RankingParams {
  type: 'individual' | 'group'
  course_id: number
  scope: 'class' | 'all'
  class_name?: string
}

/** 个人榜条目 */
export interface RankingStudentEntry {
  rank: number
  student_id: string
  name: string
  class_name: string
  score: number
}

/** 小组榜条目 */
export interface RankingGroupEntry {
  rank: number
  group_id: number
  name: string
  class_name: string
  score: number
  members: string[]
}

export interface RankingData {
  type: 'individual' | 'group'
  scope: 'class' | 'all'
  course_name: string
  classes: string[]
  entries: (RankingStudentEntry | RankingGroupEntry)[]
  my_rank: RankingStudentEntry | null
}

/**
 * 成绩排行榜 API - 教师 4 榜 / 学生本班榜
 *
 * 后端路由: backend/app/api/routes/rankings.py
 */
export const rankingsApi = {
  getRankings: (params: RankingParams): Promise<RankingData> =>
    get('/rankings', params as unknown as Record<string, unknown>),
}
```

- [ ] **Step 2: offeringsApi 补 listMine**

```ts
  /** 我的教学班（教师：本学期本人授课；管理员：全部） */
  listMine: (): Promise<CourseOffering[]> =>
    get('/teacher/offerings'),
```

- [ ] **Step 3: MyOfferings.vue**（模式照 admin/Offerings.vue 简化：header + 表格 + 操作列）

表格列：课程（course_name + course_code）/ 面向范围 / 选课人数 / 容量 / 状态 Badge / 操作（成绩录入 → 跳转 OfferingGrades、排行榜 → 跳转 TeacherRankings 带 course_id query）。空状态提示"本学期暂无授课任务"。

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { Card, Button, Badge } from '@/components/ui'
import { Loader2, ClipboardList, Trophy, Presentation } from 'lucide-vue-next'
import { offeringsApi } from '@/api/offerings'

const router = useRouter()

const { data: offeringsData, isPending } = useQuery({
  queryKey: ['teacher-offerings'],
  queryFn: () => offeringsApi.listMine(),
})
const offerings = computed(() => offeringsData.value ?? [])

const goGrades = (offeringId: number) => router.push(`/teacher/offerings/${offeringId}/grades`)
const goRankings = (courseId: number) => router.push({ path: '/teacher/rankings', query: { course_id: String(courseId) } })
</script>
```

（template 结构：Header 标题"我的教学班"/副标题"本学期授课任务与成绩管理"；Card 内 table；行操作两按钮。样式照 admin/Offerings.vue）

- [ ] **Step 4: OfferingGrades.vue（成绩录入）**

结构：
- 路由 param `:id`（offeringId）；header 显示课程名（从 listMine 中匹配）+ 返回按钮
- 名单表格（`GET /offerings/{id}/enrollments` 现有端点）：学号/姓名/班级/平时分/期末分/操作（加减分、期末分）
- 加减分 Dialog：score_change（number）+ reason → `PUT /enrollments/{id}/score` → invalidate 名单 + toast
- 期末分 Dialog：final_score（number）→ `PUT /enrollments/{id}/final-score` → invalidate + toast
- 期末任务同分 Dialog：小组下拉（`GET /teacher/groups?class_name=`——从名单学生 class_name 取 distinct 传第一个，或提供班级下拉）+ final_score → `PUT /offerings/{id}/final-scores/group` → invalidate + toast
- mutations 全部走 useMutation + queryClient.invalidateQueries({ queryKey: ['offerings', 'enrollments', offeringId] })

（小组下拉数据源：`groupsApi` 现有 getGroupsByClass（api/groups.ts 已存在，Phase 4c 重构 UI）；班级选择：名单学生 class_name distinct）

- [ ] **Step 5: 导航与路由**

DashboardLayout 教师组替换：

```ts
{ name: '我的教学班', path: '/teacher/my-offerings', icon: Presentation },
{ name: '排行榜', path: '/teacher/rankings', icon: Trophy },
```

移除旧项 `我的班级`（/teacher/my-classes）。路由 children 加：

```ts
{ path: 'my-offerings', name: 'TeacherMyOfferings', component: () => import('@/views/teacher/MyOfferings.vue') },
{ path: 'offerings/:id/grades', name: 'TeacherOfferingGrades', component: () => import('@/views/teacher/OfferingGrades.vue') },
```

（/teacher/rankings 路由在 Task 3 建页面时注册——先注册 MyOfferings/OfferingGrades，rankings 导航项与路由在 Task 3 一起落地。注意：vue-tsc 会校验 lazy import 路径存在，导航静态配置不校验路径，Task 3 提交前 type-check 全绿即可）

- [ ] **Step 6: 页面测试**（MyOfferings.spec.ts：列表渲染/空状态/操作按钮跳转 mock；OfferingGrades.spec.ts：名单渲染/加减分弹窗调用 API——模式照 test/views/Offerings.spec.ts 的 stub 方案）

- [ ] **Step 7: type-check + 前端测试 + Commit**

Run: `pnpm exec vue-tsc --noEmit && pnpm test:run`
Commit: `feat(teacher-frontend): my offerings + grade entry pages`

---

### Task 3: 前端 — 教师端排行榜页面（4 榜）

**Files:**
- Create: `frontend-v3/src/views/teacher/TeacherRankings.vue`
- Modify: `frontend-v3/src/router/index.ts`（/teacher/rankings 路由）
- Test: `frontend-v3/test/views/TeacherRankings.spec.ts`

**Interfaces:**
- Consumes: `rankingsApi.getRankings`（Task 2）、教师授课科目列表（MyOfferings 的 listMine 派生 course_id/name）
- Produces: 无（教师端排行榜最终形态）

- [ ] **Step 1: TeacherRankings.vue**

页面结构（自上而下）：
1. 科目选择：Select（选项 = listMine() 去重 course_id/course_name；从路由 query `course_id` 初始化）
2. 类型切换：两个 Button（个人成绩/小组成绩，选中态 `bg-[#e5e5e5] text-black`）
3. 范围切换：两个 Button（班内/跨班）；scope=class 时显示班级 Select（选项 = 响应 `classes` 数组）
4. 榜单 Card 表格：排名/姓名（或组名+成员 chips）/班级/分数；个人榜第 1 名高亮（`text-[#f59e0b]` 或 Badge）
5. 查询：useQuery `['rankings', { type, courseId, scope, className }]`

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRoute } from 'vue-router'
import { Card, Button, Select } from '@/components/ui'
import { Loader2, Trophy } from 'lucide-vue-next'
import { rankingsApi } from '@/api/rankings'
import { offeringsApi } from '@/api/offerings'

const route = useRoute()

// 授课科目（去重）
const { data: mine } = useQuery({
  queryKey: ['teacher-offerings'],
  queryFn: () => offeringsApi.listMine(),
})
const courseOptions = computed(() => {
  const seen = new Map<number, string>()
  for (const o of mine.value ?? []) seen.set(o.course_id, o.course_name)
  return [...seen.entries()].map(([value, label]) => ({ value, label }))
})

const courseId = ref<number | ''>(route.query.course_id ? Number(route.query.course_id) : '')
const type = ref<'individual' | 'group'>('individual')
const scope = ref<'class' | 'all'>('class')
const className = ref('')

const params = computed(() =>
  courseId.value === '' ? null : {
    type: type.value,
    course_id: courseId.value,
    scope: scope.value,
    class_name: scope.value === 'class' && className.value ? className.value : undefined,
  },
)

const { data, isPending } = useQuery({
  queryKey: ['rankings', params],
  queryFn: () => rankingsApi.getRankings(params.value!),
  enabled: () => params.value !== null,
})

// 班级下拉：响应 classes；选中第一个后自动填入
const classes = computed(() => data.value?.classes ?? [])
// watch classes → className = classes[0]（若为空）
</script>
```

（template 照上述结构，样式沿用白色极简；小组榜条目渲染 `entry.members.join('、')` 成员名单）

- [ ] **Step 2: 路由注册 + 测试**

TeacherRankings.spec.ts：mock rankingsApi/offeringsApi，断言科目切换触发查询、榜单渲染、小组榜显示成员。

- [ ] **Step 3: type-check + 前端测试 + Commit**

Commit: `feat(teacher-frontend): 4-way rankings page`

---

### Task 4: 前端 — 学生端「我的成绩」+ 本班科目排行榜

**Files:**
- Create: `frontend-v3/src/views/student/MyGrades.vue`
- Create: `frontend-v3/src/views/student/StudentRankings.vue`（替代旧 Leaderboard.vue）
- Modify: `frontend-v3/src/router/index.ts`（/student/grades、/student/rankings 路由；移除旧 /student/leaderboard、/student/group-results 路由）
- Modify: `frontend-v3/src/layouts/DashboardLayout.vue` + `components/ui/MobileDrawer.vue`（学生导航：我的成绩、排行榜；移除"组间互评/成绩单"）
- Delete: `frontend-v3/src/views/student/Leaderboard.vue`、`frontend-v3/src/views/student/GroupResults.vue`（旧综合分/任务成绩单，被新页替代）
- Modify: `frontend-v3/src/api/leaderboard.ts` 处理：旧模块在 Leaderboard.vue 删除后无引用 → 一并删除（检查 useLeaderboard.ts composable 引用后清理）
- Test: `frontend-v3/test/views/MyGrades.spec.ts`、`frontend-v3/test/views/StudentRankings.spec.ts`；`frontend-v3/test/views/Leaderboard.spec.ts` 删除或重写为新页测试

**Interfaces:**
- Consumes: `GET /students/{id}/enrollments`（我的成绩）、`rankingsApi.getRankings`（本班榜，后端强制学生 scope=class 自己班）
- Produces: 学生端最终形态

- [ ] **Step 1: MyGrades.vue（STU-03）**

- 当前学期选课列表：`GET /students/{id}/enrollments`（student_id = authStore.user.sub 字符串，注意类型一致：JWT sub 是字符串）
- 表格/卡片：课程名/教师名/范围/平时成绩（score）/期末成绩（final_score ?? '未公布'）/状态（enrolled/dropped）
- 顶部小计卡片（Card + StatCard 模式）：已选课程数
- 小组分展示：**Phase 4c 小组重构后补充**（本期页面预留空状态文案"小组分功能即将上线"？不——不留占位文案。本期仅展示个人+期末成绩；小组分在 Phase 4c 重构学生小组页面时并入本页）
- queryKey `['my-enrollments', studentId]`

- [ ] **Step 2: StudentRankings.vue（STU-04）**

- 科目下拉：选项 = 我的选课课程（从 MyGrades 同一数据源 `GET /students/{id}/enrollments` 派生 course 列表——注意 enrollments 响应无 course_id！**后端 Task 1 的 /rankings 学生权限校验只查 enrolled，前端科目下拉需要 course_id**）

> ⚠️ 接口缺口：`get_student_enrollments` 响应缺 `course_id`/`offering_id`。本任务在其返回 dict 中补 `"offering_id": e.offering_id` 与 `"course_id"`（join Course 已有——查询已 select Course.name，改为同时取 Course.id 更优雅：调整 crud/enrollment.py::get_student_enrollments 的 select 列，加 Course.id，返回加 `"course_id": course_id`）。集成测试 `tests/integration/test_enrollments_api.py`（如存在）断言补充。

- 榜单：调 rankingsApi.getRankings({ type: 'individual', course_id, scope: 'class' })——后端学生强制本班
- 展示：排名表格 + 我的排名高亮（响应 my_rank）
- queryKey `['rankings', params]`（与教师页同 key 结构，缓存共享）

- [ ] **Step 3: 导航/路由改造**

学生导航：`我的成绩`（/student/grades，图标 GraduationCap）、`排行榜`（/student/rankings，图标 Trophy）；移除 `组间互评`（/student/group-evaluations——旧互评流程，Phase 4c 删除页面）与 `成绩单`（/student/group-results）。group-evaluations 页面本轮保留路由但移出导航？**不**——旧互评流程页面本轮不删（Phase 4c 小组重构时删），导航移除即可，路由暂留（页面不可达但无碍，Phase 4c 删除）。

- [ ] **Step 4: 清理旧文件**

- Delete `views/student/Leaderboard.vue`、`views/student/GroupResults.vue`
- 检查 `api/leaderboard.ts`、`composables/useLeaderboard.ts` 引用（`grep -rn "useLeaderboard\|leaderboardApi" src/`）→ 无引用后删除两文件与对应 test（test/views/Leaderboard.spec.ts）
- composables/index.ts 移除 useLeaderboard 导出

- [ ] **Step 5: 页面测试**（MyGrades.spec.ts：列表渲染/未公布期末分显示；StudentRankings.spec.ts：科目下拉/榜单渲染/my_rank 高亮——mock rankingsApi 与学生 enrollments API）

- [ ] **Step 6: type-check + 前端测试 + Commit**

Run: `pnpm exec vue-tsc --noEmit && pnpm test:run`
Commit: `feat(student-frontend): my grades + class course rankings`

---

### Task 5: 全量回归（前后端）+ 合并推送

- [ ] **Step 1: 后端全量回归**

```bash
conda run -n student-manage pytest tests/ -q > /tmp/pytest_phase4b.log 2>&1
tail -3 /tmp/pytest_phase4b.log   # 期望: N passed, 0 failed
```

- [ ] **Step 2: 前端全量 + type-check**

```bash
cd frontend-v3 && pnpm test:run && pnpm exec vue-tsc --noEmit
```

- [ ] **Step 3: finishing-a-development-branch 流程合并 main + 推送 GitHub**

（历史流程：checkout main → merge --no-ff feat/teacher-grades → push origin main）

---

## Self-Review

**Spec 覆盖检查**（对照需求表）：
- ✅ TCH-01 我的教学班 → Task 1 `/teacher/offerings` + Task 2 MyOfferings.vue
- ✅ TCH-03 课程成绩录入 → Task 2 OfferingGrades.vue（后端已有，复用）
- ✅ TCH-04 期末成绩登记/修改（试卷个人/任务小组同分）→ Task 2 OfferingGrades.vue
- ✅ TCH-07 排行榜 4 榜 → Task 1 /rankings + Task 3 TeacherRankings.vue
- ✅ STU-03 我的成绩查看（个人+期末；小组分 Phase 4c 补）→ Task 4 MyGrades.vue
- ✅ STU-04 学生排行榜（本班科目个人榜）→ Task 4 StudentRankings.vue
- ⏳ TCH-02 签到适配 / TCH-05/06 小组 / STU-05 → Phase 4c
- ⏳ ADM-13 审计学期过滤 / 清理 → Phase 4d

**接口缺口闭环**：学生科目下拉需要 course_id → Task 4 Step 2 明确改 `crud/enrollment.py::get_student_enrollments` 返回补 `course_id`（含集成测试断言更新）。

**占位符扫描**：无 TODO/TBD；小组分延期明确标注 Phase 4c，不在本计划留占位代码。

**类型一致性**：RankingData/entries 联合类型在 Task 2 定义，Task 3/4 引用；queryKey 约定 `['teacher-offerings']`、`['rankings', params]`、`['my-enrollments', studentId]`，invalidate 时同步（Task 2 名单失效 key `['offerings', 'enrollments', offeringId]` 与 admin Offerings 页一致）。

## 分支与执行顺序

- 分支 `feat/teacher-grades`（从 main 切出，Task 1-5）
- 每个 Task 验证全绿再进下一 Task；完成后合并 main 并推送
- Phase 4c（小组系统重构）与 Phase 4d（清理）在本计划合并后另立计划
