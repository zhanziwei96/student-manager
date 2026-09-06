# 学生科目分数实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现学生按科目独立管理分数（新建 subjects + student_subject_scores + student_subject_score_logs 表，支持按教师+科目聚合的排行榜）。

**Architecture:** 全局科目表（无 class_name）+ 学生科目分数表（student_id + subject_id + teacher_id + semester）+ 分数变更日志表。从课表推导科目和教师；学期切换时清零；学期中换老师继承当前分数。复用学生分数的乐观锁 + 日志 + 事件模式。

**Tech Stack:** FastAPI + SQLModel + Alembic + PostgreSQL（开发/生产）/SQLite（测试内存库）、Vue 3 + TypeScript + TanStack Query、pytest + vitest。

**参考设计文档:** `docs/superpowers/specs/2026-09-05-student-subject-scores-design.md`

**测试环境要求（CLAUDE.md 强制）:**
- Python: `conda run -n student-manage python ...` 或已激活 `student-manage` 环境
- 后端测试在项目根目录运行: `pytest tests/... -v`
- 前端测试在 `frontend-v3/` 目录运行: `pnpm test:run`

---

## 文件结构

**新建文件：**

| 文件 | 职责 |
|------|------|
| `backend/app/models/subject.py` | Subject + StudentSubjectScore + StudentSubjectScoreLog 模型 |
| `backend/app/crud/subject.py` | 科目 CRUD（推导、列表、修改） |
| `backend/app/crud/student_subject_score.py` | 学生科目分数 CRUD（初始化、换老师、加减分） |
| `backend/app/api/routes/subjects.py` | 科目管理 API |
| `backend/app/api/routes/student_subject_scores.py` | 学生科目分数 API |
| `backend/alembic/versions/<timestamp>_add_subject_tables.py` | 迁移（3 张新表） |
| `backend/tests/unit/test_subject.py` | 科目 CRUD 单元测试 |
| `backend/tests/unit/test_student_subject_score.py` | 学生科目分数 CRUD 单元测试 |
| `backend/tests/integration/test_subject_api.py` | 科目管理 API 集成测试 |
| `backend/tests/integration/test_student_subject_score_api.py` | 学生科目分数 API 集成测试 |
| `frontend-v3/src/api/subjects.ts` | 前端科目 API 客户端 |
| `frontend-v3/src/api/studentSubjectScores.ts` | 前端学生科目分数 API 客户端 |
| `frontend-v3/src/composables/useSubjects.ts` | 科目 composable |
| `frontend-v3/src/composables/useStudentSubjectScores.ts` | 学生科目分数 composable |
| `frontend-v3/src/views/admin/Subjects.vue` | 科目管理页（admin） |
| `frontend-v3/src/views/teacher/Subjects.vue` | 科目管理页（teacher） |
| `frontend-v3/test/views/admin/Subjects.spec.ts` | 科目管理页测试 |

**修改文件：**

| 文件 | 修改 |
|------|------|
| `backend/app/models/__init__.py` | 导出 Subject/StudentSubjectScore/StudentSubjectScoreLog |
| `backend/app/crud/__init__.py` | 导出科目和学生科目分数 CRUD 函数 |
| `backend/app/api/routes/__init__.py` | 导出 subjects_router 和 student_subject_scores_router |
| `backend/main.py` | 注册 subjects_router 和 student_subject_scores_router |
| `backend/app/api/routes/leaderboard.py` | 排行榜加 subject_id/teacher_id 参数 |
| `backend/app/crud/leaderboard.py` | 排行榜查询支持按科目+教师聚合 |
| `frontend-v3/src/api/index.ts` | 导出科目和学生科目分数 API |
| `frontend-v3/src/router/index.ts` | 加科目管理页路由 |
| `frontend-v3/src/views/admin/Students.vue` | 学生列表加科目分数展示 |
| `frontend-v3/src/views/teacher/Students.vue` | 同上 |
| `frontend-v3/src/views/student/Dashboard.vue` | "我的科目"卡片列表 |
| `frontend-v3/src/views/student/Leaderboard.vue` | 加科目/教师筛选器 |

---

## Phase 1：数据模型与迁移

### Task 1: 科目模型与迁移

**Files:**
- Create: `backend/app/models/subject.py`
- Create: `backend/alembic/versions/<timestamp>_add_subject_tables.py`
- Modify: `backend/app/models/__init__.py`
- Test: `tests/unit/test_subject.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/test_subject.py`：

```python
"""科目模型测试"""
from app.models import Subject, StudentSubjectScore, StudentSubjectScoreLog


def test_subject_creation():
    """科目创建"""
    subject = Subject(name="数学", semester="2026-2027-1")
    assert subject.name == "数学"
    assert subject.semester == "2026-2027-1"


def test_student_subject_score_creation():
    """学生科目分数创建"""
    score = StudentSubjectScore(
        student_id="TEST001",
        subject_id=1,
        teacher_id=1,
        score=85.0,
        semester="2026-2027-1"
    )
    assert score.student_id == "TEST001"
    assert score.subject_id == 1
    assert score.teacher_id == 1
    assert score.score == 85.0


def test_student_subject_score_log_creation():
    """学生科目分数日志创建"""
    log = StudentSubjectScoreLog(
        student_id="TEST001",
        subject_id=1,
        teacher_id=1,
        old_score=80.0,
        new_score=85.0,
        delta=5.0,
        reason="课堂表现",
        operator="张老师",
        semester="2026-2027-1"
    )
    assert log.old_score == 80.0
    assert log.new_score == 85.0
    assert log.delta == 5.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_subject.py -v`
Expected: FAIL — `ImportError: cannot import name 'Subject'`

- [ ] **Step 3: 实现模型**

创建 `backend/app/models/subject.py`：

```python
"""
科目模型 - 学生科目分数系统
"""
from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlmodel import SQLModel, Field
from sqlalchemy import Index, desc
from app.core.timezone import get_now
from app.core.term import get_current_term


class Subject(SQLModel, table=True):
    """科目表（全局共享，从课表推导）"""
    __tablename__ = "subjects"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., description="科目名称（如'数学'）", max_length=100)
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20, index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")

    __table_args__ = (
        # 同一学期内科目名称唯一
        sa.UniqueConstraint("name", "semester", name="uix_subject_name_semester"),
    )


class StudentSubjectScore(SQLModel, table=True):
    """学生科目分数表（按科目独立管理）"""
    __tablename__ = "student_subject_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号", max_length=50, index=True)
    subject_id: int = Field(..., foreign_key="subjects.id", description="科目ID", index=True)
    teacher_id: int = Field(..., foreign_key="users.id", description="教师ID（该学生这个科目的授课教师）", index=True)
    score: float = Field(default=70.0, description="分数", index=True)
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20, index=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")

    __table_args__ = (
        # 同一学生同一科目同一学期同一教师唯一（学期中换老师新建记录）
        sa.UniqueConstraint("student_id", "subject_id", "teacher_id", "semester", name="uix_student_subject_teacher_semester"),
    )


class StudentSubjectScoreLog(SQLModel, table=True):
    """学生科目分数变更日志表"""
    __tablename__ = "student_subject_score_logs"
    __table_args__ = (
        Index('idx_subject_score_logs_student_created_at', 'student_id', desc('created_at')),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号")
    subject_id: int = Field(..., description="科目ID")
    teacher_id: int = Field(..., description="教师ID（操作时的授课教师）")
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    semester: str = Field(default_factory=get_current_term, description="学期标识", max_length=20)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
```

修改 `backend/app/models/__init__.py` 追加导出：

```python
from app.models.subject import Subject, StudentSubjectScore, StudentSubjectScoreLog

__all__ = [
    # ... 现有导出 ...
    "Subject",
    "StudentSubjectScore",
    "StudentSubjectScoreLog",
]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_subject.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 创建迁移**

Run: `cd backend && conda run -n student-manage alembic revision -m "add subject tables" --rev-id $(date +%Y%m%d_%H%M%S | sed 's/_//g')_add_subject_tables`

替换生成文件内容为：

```python
"""add subject tables

Revision ID: <rev>
Revises: 20260904_student_lockout
Create Date: <生成时间>
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '<rev>'
down_revision: Union[str, Sequence[str], None] = '20260904_student_lockout'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建科目相关表"""
    # 科目表
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'semester', name='uix_subject_name_semester')
    )
    op.create_index('ix_subjects_semester', 'subjects', ['semester'], unique=False)

    # 学生科目分数表
    op.create_table(
        'student_subject_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'subject_id', 'teacher_id', 'semester', name='uix_student_subject_teacher_semester')
    )
    op.create_index('ix_student_subject_scores_student_id', 'student_subject_scores', ['student_id'], unique=False)
    op.create_index('ix_student_subject_scores_subject_id', 'student_subject_scores', ['subject_id'], unique=False)
    op.create_index('ix_student_subject_scores_teacher_id', 'student_subject_scores', ['teacher_id'], unique=False)
    op.create_index('ix_student_subject_scores_score', 'student_subject_scores', ['score'], unique=False)
    op.create_index('ix_student_subject_scores_semester', 'student_subject_scores', ['semester'], unique=False)

    # 学生科目分数日志表
    op.create_table(
        'student_subject_score_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('old_score', sa.Float(), nullable=True),
        sa.Column('new_score', sa.Float(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('operator', sa.String(), nullable=True),
        sa.Column('semester', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_subject_score_logs_student_created_at', 'student_subject_score_logs', ['student_id', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    """回滚：删除科目相关表"""
    op.drop_index('idx_subject_score_logs_student_created_at', table_name='student_subject_score_logs')
    op.drop_table('student_subject_score_logs')

    op.drop_index('ix_student_subject_scores_semester', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_score', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_teacher_id', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_subject_id', table_name='student_subject_scores')
    op.drop_index('ix_student_subject_scores_student_id', table_name='student_subject_scores')
    op.drop_table('student_subject_scores')

    op.drop_index('ix_subjects_semester', table_name='subjects')
    op.drop_table('subjects')
```

应用迁移：

```bash
cd backend && conda run -n student-manage alembic upgrade head
```

- [ ] **Step 6: 提交**

```bash
git add backend/app/models/subject.py backend/app/models/__init__.py backend/alembic/versions/ tests/unit/test_subject.py
git commit -m "feat(subject): add subject and student subject score models"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

## Phase 2：科目 CRUD

### Task 2: 科目 CRUD（推导、列表、修改）

**Files:**
- Create: `backend/app/crud/subject.py`
- Test: `tests/unit/test_subject.py`（追加）

- [ ] **Step 1: 写失败测试**

在 `tests/unit/test_subject.py` 追加：

```python
def test_derive_subjects_from_schedules(session):
    """从课表推导科目"""
    from app.crud.subject import derive_subjects_and_teachers
    from app.models import CourseSchedule

    # 造课表数据
    schedule1 = CourseSchedule(
        course_name="数学", class_name="1班", teacher_id=1,
        day_of_week=1, start_time="08:00", end_time="09:40",
        semester="2026-2027-1"
    )
    schedule2 = CourseSchedule(
        course_name="语文", class_name="1班", teacher_id=2,
        day_of_week=2, start_time="10:00", end_time="11:40",
        semester="2026-2027-1"
    )
    session.add_all([schedule1, schedule2])
    session.commit()

    result = derive_subjects_and_teachers(session)
    assert "1班" in result
    assert "数学" in result["1班"]
    assert result["1班"]["数学"] == 1
    assert result["1班"]["语文"] == 2


def test_get_subjects_by_semester(session):
    """按学期查询科目"""
    from app.crud.subject import get_subjects_by_semester

    subject1 = Subject(name="数学", semester="2026-2027-1")
    subject2 = Subject(name="语文", semester="2026-2027-1")
    subject3 = Subject(name="数学", semester="2025-2026-2")  # 上学期
    session.add_all([subject1, subject2, subject3])
    session.commit()

    subjects = get_subjects_by_semester(session, "2026-2027-1")
    assert len(subjects) == 2
    assert all(s.semester == "2026-2027-1" for s in subjects)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_subject.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crud.subject'`

- [ ] **Step 3: 实现 CRUD**

创建 `backend/app/crud/subject.py`：

```python
"""
科目 CRUD 操作
"""
from typing import List, Optional, Dict
from sqlmodel import Session, select
from app.models import Subject, CourseSchedule
from app.core.term import get_current_term


def derive_subjects_and_teachers(session: Session) -> Dict[str, Dict[str, int]]:
    """从课表推导科目和教师（当前学期）

    Returns:
        Dict[class_name, Dict[subject_name, teacher_id]]
        如：{"1班": {"数学": 张老师id, "语文": 李老师id}}
    """
    schedules = session.exec(
        select(CourseSchedule).where(CourseSchedule.semester == get_current_term())
    ).all()

    result = {}
    for schedule in schedules:
        if schedule.class_name not in result:
            result[schedule.class_name] = {}
        # 同一班级同一科目可能有多个老师（正课+实验），取第一个
        if schedule.course_name not in result[schedule.class_name]:
            result[schedule.class_name][schedule.course_name] = schedule.teacher_id

    return result


def get_subjects_by_semester(session: Session, semester: Optional[str] = None) -> List[Subject]:
    """按学期查询科目"""
    if semester is None:
        semester = get_current_term()
    query = select(Subject).where(Subject.semester == semester).order_by(Subject.name)
    return list(session.exec(query).all())


def create_subject(session: Session, name: str, semester: Optional[str] = None) -> Subject:
    """创建科目"""
    if semester is None:
        semester = get_current_term()
    subject = Subject(name=name, semester=semester)
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject


def update_subject_name(session: Session, subject_id: int, new_name: str) -> Optional[Subject]:
    """修改科目名称"""
    subject = session.get(Subject, subject_id)
    if not subject:
        return None
    subject.name = new_name
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject
```

修改 `backend/app/crud/__init__.py` 追加导出：

```python
from app.crud.subject import (
    derive_subjects_and_teachers,
    get_subjects_by_semester,
    create_subject,
    update_subject_name,
)

__all__ = [
    # ... 现有导出 ...
    "derive_subjects_and_teachers",
    "get_subjects_by_semester",
    "create_subject",
    "update_subject_name",
]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_subject.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/crud/subject.py backend/app/crud/__init__.py tests/unit/test_subject.py
git commit -m "feat(subject): add subject CRUD operations"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

## Phase 3：学生科目分数 CRUD

### Task 3: 学生科目分数 CRUD（初始化、换老师、加减分）

**Files:**
- Create: `backend/app/crud/student_subject_score.py`
- Test: `tests/unit/test_student_subject_score.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/unit/test_student_subject_score.py`：

```python
"""学生科目分数 CRUD 测试"""
from app.models import StudentSubjectScore, StudentSubjectScoreLog
from app.crud.student_subject_score import (
    init_student_subject_scores,
    transfer_student_to_new_teacher,
    update_student_subject_score,
)


def test_init_student_subject_scores(session):
    """学期切换时初始化学生科目分数"""
    from app.models import Student, Subject

    # 造数据：1 个学生 + 1 个科目
    student = Student(student_id="TEST001", name="测试学生", class_name="1班", score=80.0)
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add_all([student, subject])
    session.commit()

    # 初始化
    init_student_subject_scores(session, "2026-2027-1")

    # 验证：新建记录
    score = session.query(StudentSubjectScore).filter_by(
        student_id="TEST001", subject_id=subject.id, semester="2026-2027-1"
    ).first()
    assert score is not None
    assert score.score == 70.0  # 默认分数


def test_transfer_student_to_new_teacher(session):
    """学期中换老师（继承当前分数）"""
    from app.models import Subject

    # 造数据：1 个学生 + 1 个科目 + 当前分数记录
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="TEST001", subject_id=subject.id, teacher_id=1,
        score=85.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    # 换老师
    transfer_student_to_new_teacher(session, subject.id, 1, 2)

    # 验证：新建记录（新老师，继承当前分数）
    new_score = session.query(StudentSubjectScore).filter_by(
        student_id="TEST001", subject_id=subject.id, teacher_id=2, semester="2026-2027-1"
    ).first()
    assert new_score is not None
    assert new_score.score == 85.0  # 继承当前分数


def test_update_student_subject_score(session):
    """更新学生科目分数（乐观锁 + 日志）"""
    from app.models import Subject

    # 造数据
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="TEST001", subject_id=subject.id, teacher_id=1,
        score=80.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    # 更新分数
    result = update_student_subject_score(session, "TEST001", subject.id, 5.0, "课堂表现", "张老师")
    assert result is not None
    assert result.score == 85.0

    # 验证日志
    log = session.query(StudentSubjectScoreLog).filter_by(
        student_id="TEST001", subject_id=subject.id
    ).first()
    assert log is not None
    assert log.old_score == 80.0
    assert log.new_score == 85.0
    assert log.delta == 5.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/unit/test_student_subject_score.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.crud.student_subject_score'`

- [ ] **Step 3: 实现 CRUD**

创建 `backend/app/crud/student_subject_score.py`：

```python
"""
学生科目分数 CRUD 操作
"""
from typing import List, Optional
from sqlmodel import Session, select
from app.models import StudentSubjectScore, StudentSubjectScoreLog, Subject, Student
from app.core.term import get_current_term
from app.core.events import event_bus, ScoreUpdated


def init_student_subject_scores(session: Session, new_semester: str):
    """学期切换时初始化学生科目分数（清零）

    前提：新学期课表已导入
    """
    from app.crud.subject import derive_subjects_and_teachers

    # 推导科目和教师
    subject_teachers = derive_subjects_and_teachers(session)

    # 为每个学生每个科目新建记录（score=70.0，teacher_id 从课表推导）
    students = session.exec(select(Student).where(Student.is_account_enabled.is_(True))).all()
    for student in students:
        class_name = student.class_name
        if class_name in subject_teachers:
            for subject_name, teacher_id in subject_teachers[class_name].items():
                # 查科目 ID
                subject = session.exec(
                    select(Subject).where(Subject.name == subject_name, Subject.semester == new_semester)
                ).first()
                if subject:
                    # 新建记录
                    score_record = StudentSubjectScore(
                        student_id=student.student_id,
                        subject_id=subject.id,
                        teacher_id=teacher_id,
                        score=70.0,  # 默认分数
                        semester=new_semester,
                    )
                    session.add(score_record)

    session.commit()


def transfer_student_to_new_teacher(
    session: Session,
    subject_id: int,
    old_teacher_id: int,
    new_teacher_id: int,
):
    """学期中换老师（继承当前分数）"""
    # 查当前学期该科目该老师的所有学生
    students = session.exec(
        select(StudentSubjectScore).where(
            StudentSubjectScore.subject_id == subject_id,
            StudentSubjectScore.teacher_id == old_teacher_id,
            StudentSubjectScore.semester == get_current_term(),
        )
    ).all()

    for record in students:
        # 新建记录（新老师，继承当前分数）
        new_record = StudentSubjectScore(
            student_id=record.student_id,
            subject_id=subject_id,
            teacher_id=new_teacher_id,
            score=record.score,  # 继承当前分数
            semester=get_current_term(),
        )
        session.add(new_record)

    session.commit()


def update_student_subject_score(
    session: Session,
    student_id: str,
    subject_id: int,
    delta: float,
    reason: str,
    operator: str,
) -> Optional[StudentSubjectScore]:
    """更新学生科目分数（乐观锁 + 日志，复用学生分数逻辑）"""
    from sqlalchemy import text
    from sqlalchemy.orm import Session as SASession
    from fastapi import HTTPException

    # 查当前记录（当前学期）
    score_record = session.exec(
        select(StudentSubjectScore).where(
            StudentSubjectScore.student_id == student_id,
            StudentSubjectScore.subject_id == subject_id,
            StudentSubjectScore.semester == get_current_term(),
        )
    ).first()

    if not score_record:
        return None

    # 计算新分数（复用学生分数的范围限制逻辑）
    old_score = score_record.score
    from app.core.config import get_settings
    settings = get_settings()
    new_score = max(settings.score.min_score, min(settings.score.max_score, old_score + delta))

    # 乐观锁：使用原生 UPDATE 检查 affected rows
    expected_version = score_record.version
    new_version = expected_version + 1

    sa_session: SASession = session
    result = sa_session.execute(
        text("""
            UPDATE student_subject_scores
            SET score = :score, version = :new_version, updated_at = :updated_at
            WHERE id = :id AND version = :expected_version
        """),
        {
            "score": new_score,
            "new_version": new_version,
            "updated_at": get_now(),
            "id": score_record.id,
            "expected_version": expected_version
        }
    )

    # 检查是否有行被更新
    if result.rowcount == 0:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="分数已被其他用户修改，请刷新后重试"
        )

    # 写日志
    log = StudentSubjectScoreLog(
        student_id=student_id,
        subject_id=subject_id,
        teacher_id=score_record.teacher_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator,
        semester=get_current_term(),
    )
    session.add(log)

    # 发布事件（复用学生分数事件）
    event = ScoreUpdated(
        student_id=student_id,
        old_score=old_score,
        new_score=new_score,
        delta=delta,
        reason=reason,
        operator=operator
    )

    # 使用一次性事件发布机制
    _published_events = getattr(session, '_published_events', None)
    if _published_events is None:
        _published_events = set()
        session._published_events = _published_events

    event_id = id(event)

    def _publish_event_once(session):
        if event_id not in _published_events:
            _published_events.add(event_id)
            event_bus.publish(event)

    from sqlalchemy import event as sa_event
    sa_event.listen(session, "after_commit", _publish_event_once, once=True)

    session.commit()

    return score_record
```

修改 `backend/app/crud/__init__.py` 追加导出：

```python
from app.crud.student_subject_score import (
    init_student_subject_scores,
    transfer_student_to_new_teacher,
    update_student_subject_score,
)

__all__ = [
    # ... 现有导出 ...
    "init_student_subject_scores",
    "transfer_student_to_new_teacher",
    "update_student_subject_score",
]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/unit/test_student_subject_score.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/crud/student_subject_score.py backend/app/crud/__init__.py tests/unit/test_student_subject_score.py
git commit -m "feat(subject): add student subject score CRUD operations"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

## Phase 4：API 接口

### Task 4: 科目管理 API

**Files:**
- Create: `backend/app/api/routes/subjects.py`
- Modify: `backend/app/api/routes/__init__.py`
- Modify: `backend/main.py`
- Test: `tests/integration/test_subject_api.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/integration/test_subject_api.py`：

```python
"""科目管理 API 集成测试"""


def test_get_subjects(admin_client, session):
    """获取科目列表"""
    from app.models import Subject

    # 造数据
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    resp = admin_client.get("/api/v1/subjects")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "数学"


def test_update_subject_name(admin_client, session):
    """修改科目名称"""
    from app.models import Subject

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    resp = admin_client.put(f"/api/v1/subjects/{subject.id}", json={"name": "高等数学"})
    assert resp.status_code == 200

    # 验证
    subject = session.get(Subject, subject.id)
    assert subject.name == "高等数学"


def test_derive_subjects(admin_client, session):
    """从课表推导科目"""
    from app.models import CourseSchedule

    # 造课表
    schedule = CourseSchedule(
        course_name="数学", class_name="1班", teacher_id=1,
        day_of_week=1, start_time="08:00", end_time="09:40",
        semester="2026-2027-1"
    )
    session.add(schedule)
    session.commit()

    resp = admin_client.post("/api/v1/subjects/derive")
    assert resp.status_code == 200

    # 验证：科目已创建
    from app.models import Subject
    subject = session.query(Subject).filter_by(name="数学", semester="2026-2027-1").first()
    assert subject is not None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_subject_api.py -v`
Expected: FAIL — 404（路由不存在）

- [ ] **Step 3: 实现路由**

创建 `backend/app/api/routes/subjects.py`：

```python
"""
科目管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.config import HttpStatus
from app.api.deps import require_admin_or_teacher
from app.crud.subject import (
    get_subjects_by_semester,
    create_subject,
    update_subject_name,
    derive_subjects_and_teachers,
)
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse

router = APIRouter(tags=["subjects"])


class UpdateSubjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="科目名称")


@router.get("/subjects", response_model=ApiResponse[List[dict]])
def get_subjects(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """获取科目列表（当前学期）"""
    subjects = get_subjects_by_semester(session)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "id": s.id,
                "name": s.name,
                "semester": s.semester,
            }
            for s in subjects
        ]
    }


@router.put("/subjects/{subject_id}", response_model=ApiSuccessResponse)
def update_subject(
    subject_id: int,
    data: UpdateSubjectRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """修改科目名称"""
    subject = update_subject_name(session, subject_id, data.name)
    if not subject:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="科目不存在")

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "科目已更新"
    }


@router.post("/subjects/derive", response_model=ApiResponse[dict])
def derive_subjects(
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """从课表推导科目（当前学期）"""
    subject_teachers = derive_subjects_and_teachers(session)

    # 为每个科目创建记录（若不存在）
    created_count = 0
    for class_name, subjects in subject_teachers.items():
        for subject_name in subjects.keys():
            existing = session.exec(
                select(Subject).where(
                    Subject.name == subject_name,
                    Subject.semester == get_current_term()
                )
            ).first()
            if not existing:
                create_subject(session, subject_name)
                created_count += 1

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已推导 {created_count} 个科目",
        ApiResponseConst.DATA: {"created_count": created_count}
    }
```

修改 `backend/app/api/routes/__init__.py` 追加导出：

```python
from app.api.routes.subjects import router as subjects_router

__all__ = [
    # ... 现有导出 ...
    "subjects_router",
]
```

修改 `backend/main.py` 注册路由（在 lost_found 之后）：

```python
from app.api.routes.subjects import router as subjects_router
app.include_router(subjects_router, prefix=API_V1_PREFIX)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_subject_api.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/subjects.py backend/app/api/routes/__init__.py backend/main.py tests/integration/test_subject_api.py
git commit -m "feat(subject): add subject management API"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

（后续 Task 5-10 的完整内容因长度限制省略，结构与 Task 1-4 相同：Task 5 学生科目分数 API、Task 6 排行榜改造、Task 7 前端科目管理页、Task 8 前端学生管理页改造、Task 9 前端学生 Dashboard 改造、Task 10 前端排行榜改造）

---

## 执行顺序与依赖

```
Phase 1 (Task 1)     数据模型与迁移          [无依赖]
Phase 2 (Task 2)     科目 CRUD              [依赖 Task 1]
Phase 3 (Task 3)     学生科目分数 CRUD      [依赖 Task 2]
Phase 4 (Task 4)     科目管理 API           [依赖 Task 2]
Phase 5 (Task 5)     学生科目分数 API       [依赖 Task 3]
Phase 6 (Task 6)     排行榜改造             [依赖 Task 3]
Phase 7 (Task 7-10)  前端改造               [依赖 Task 4-6]
```

## 风险与回滚

- **迁移风险**：Task 1 的 alembic 迁移在开发 PG 上执行前，先手动 `pg_dump` 一份全库快照。回滚用 `alembic downgrade -1`。
- **数据一致性**：学期切换时的初始化逻辑需要新学期课表已导入（前提条件）。
- **性能风险**：学生科目分数表的数据量是 students × subjects（465 × 10 = 4650 条/学期），有索引支撑，无性能问题。
