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

## Phase 5：学生科目分数 API

### Task 5: 学生科目分数 API

**Files:**
- Create: `backend/app/api/routes/student_subject_scores.py`
- Modify: `backend/app/api/routes/__init__.py`
- Modify: `backend/main.py`
- Test: `tests/integration/test_student_subject_score_api.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/integration/test_student_subject_score_api.py`：

```python
"""学生科目分数 API 集成测试"""


def test_get_student_subjects(student_client, session):
    """学生获取自己所有科目分数"""
    from app.models import Subject, StudentSubjectScore

    # 造数据
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="S001", subject_id=subject.id, teacher_id=1,
        score=85.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    resp = student_client.get("/api/v1/students/S001/subjects")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["subject_name"] == "数学"
    assert data[0]["score"] == 85.0


def test_update_student_subject_score(teacher_client, session):
    """教师给学生某科目加减分"""
    from app.models import Subject, StudentSubjectScore

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score = StudentSubjectScore(
        student_id="S001", subject_id=subject.id, teacher_id=1,
        score=80.0, semester="2026-2027-1"
    )
    session.add(score)
    session.commit()

    resp = teacher_client.put(
        f"/api/v1/students/S001/subjects/{subject.id}/score",
        json={"score_change": 5, "reason": "课堂表现"}
    )
    assert resp.status_code == 200

    # 验证分数已更新
    session.refresh(score)
    assert score.score == 85.0


def test_get_student_subject_score_logs(student_client, session):
    """学生查看自己某科目分数历史"""
    from app.models import Subject, StudentSubjectScoreLog

    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    log = StudentSubjectScoreLog(
        student_id="S001", subject_id=subject.id, teacher_id=1,
        old_score=80.0, new_score=85.0, delta=5.0,
        reason="课堂表现", operator="张老师", semester="2026-2027-1"
    )
    session.add(log)
    session.commit()

    resp = student_client.get(f"/api/v1/students/S001/subjects/{subject.id}/logs")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["old_score"] == 80.0
    assert data[0]["new_score"] == 85.0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_student_subject_score_api.py -v`
Expected: FAIL — 404（路由不存在）

- [ ] **Step 3: 实现路由**

创建 `backend/app/api/routes/student_subject_scores.py`：

```python
"""
学生科目分数 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.term import get_current_term
from app.api.deps import get_current_user, require_admin_or_teacher, verify_teacher_class_access
from app.crud.student_subject_score import update_student_subject_score
from app.models import StudentSubjectScore, StudentSubjectScoreLog, Subject, Student, User
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse

router = APIRouter(tags=["student-subject-scores"])


class UpdateScoreRequest(BaseModel):
    score_change: float = Field(..., description="分数变化值（正数加分，负数扣分）")
    reason: str = Field(..., min_length=1, max_length=200, description="原因")


@router.get("/students/{student_id}/subjects", response_model=ApiResponse[List[dict]])
def get_student_subjects(
    student_id: str,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生所有科目分数（学生只能看自己，教师看自己班）"""
    # 权限校验
    role = user.get("role", "")
    if role == "student":
        if student_id != user.get("sub", ""):
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权查看其他学生信息")
    elif role == "teacher":
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
        verify_teacher_class_access(user, student.class_name, session)

    # 查询当前学期的所有科目分数
    scores = session.exec(
        select(StudentSubjectScore, Subject, User)
        .join(Subject, StudentSubjectScore.subject_id == Subject.id)
        .join(User, StudentSubjectScore.teacher_id == User.id)
        .where(
            StudentSubjectScore.student_id == student_id,
            StudentSubjectScore.semester == get_current_term(),
        )
    ).all()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "subject_id": score.subject_id,
                "subject_name": subject.name,
                "teacher_id": score.teacher_id,
                "teacher_name": teacher.name,
                "score": score.score,
            }
            for score, subject, teacher in scores
        ]
    }


@router.put("/students/{student_id}/subjects/{subject_id}/score", response_model=ApiSuccessResponse)
def update_score(
    student_id: str,
    subject_id: int,
    data: UpdateScoreRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin_or_teacher)
):
    """更新学生科目分数（admin 或负责该班的教师）"""
    # 权限校验
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
    verify_teacher_class_access(user, student.class_name, session)

    # 更新分数
    username = user.get("username", "")
    result = update_student_subject_score(session, student_id, subject_id, data.score_change, data.reason, username)
    if not result:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生科目分数记录不存在")

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "分数已更新"
    }


@router.get("/students/{student_id}/subjects/{subject_id}/logs", response_model=ApiResponse[List[dict]])
def get_student_subject_score_logs(
    student_id: str,
    subject_id: int,
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生某科目分数历史（学生只能看自己，教师看自己班）"""
    # 权限校验
    role = user.get("role", "")
    if role == "student":
        if student_id != user.get("sub", ""):
            raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权查看其他学生信息")
    elif role == "teacher":
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="学生不存在")
        verify_teacher_class_access(user, student.class_name, session)

    # 查询日志
    logs = session.exec(
        select(StudentSubjectScoreLog)
        .where(
            StudentSubjectScoreLog.student_id == student_id,
            StudentSubjectScoreLog.subject_id == subject_id,
            StudentSubjectScoreLog.semester == get_current_term(),
        )
        .order_by(StudentSubjectScoreLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "old_score": log.old_score,
                "new_score": log.new_score,
                "delta": log.delta,
                "reason": log.reason,
                "operator": log.operator,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    }
```

修改 `backend/app/api/routes/__init__.py` 追加导出：

```python
from app.api.routes.student_subject_scores import router as student_subject_scores_router

__all__ = [
    # ... 现有导出 ...
    "student_subject_scores_router",
]
```

修改 `backend/main.py` 注册路由（在 subjects_router 之后）：

```python
from app.api.routes.student_subject_scores import router as student_subject_scores_router
app.include_router(student_subject_scores_router, prefix=API_V1_PREFIX)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_student_subject_score_api.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/student_subject_scores.py backend/app/api/routes/__init__.py backend/main.py tests/integration/test_student_subject_score_api.py
git commit -m "feat(subject): add student subject score API"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

## Phase 6：排行榜改造

### Task 6: 排行榜按教师+科目聚合

**Files:**
- Modify: `backend/app/api/routes/leaderboard.py`
- Modify: `backend/app/crud/leaderboard.py`
- Test: `tests/integration/test_leaderboard_api.py`（追加）

- [ ] **Step 1: 写失败测试**

在 `tests/integration/test_leaderboard_api.py` 追加：

```python
def test_leaderboard_by_subject_and_teacher(student_client, session):
    """按教师+科目聚合排行榜"""
    from app.models import Subject, StudentSubjectScore

    # 造数据：2 个学生，同一科目，不同老师
    subject = Subject(name="数学", semester="2026-2027-1")
    session.add(subject)
    session.commit()

    score1 = StudentSubjectScore(student_id="S001", subject_id=subject.id, teacher_id=1, score=85.0, semester="2026-2027-1")
    score2 = StudentSubjectScore(student_id="S002", subject_id=subject.id, teacher_id=2, score=90.0, semester="2026-2027-1")
    session.add_all([score1, score2])
    session.commit()

    # 按教师+科目排
    resp = student_client.get(f"/api/v1/students/leaderboard?subject_id={subject.id}&teacher_id=1")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["students"]) == 1
    assert data["students"][0]["student_id"] == "S001"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n student-manage pytest tests/integration/test_leaderboard_api.py::test_leaderboard_by_subject_and_teacher -v`
Expected: FAIL — 参数不存在或行为不符合

- [ ] **Step 3: 实现改造**

修改 `backend/app/api/routes/leaderboard.py` 的 `get_student_leaderboard`：

```python
@router.get("/students/leaderboard", response_model=LeaderboardResponse)
def get_student_leaderboard(
    scope: str = Query("class", description="范围: class 或 school"),
    class_name: Optional[str] = Query(None, description="班级名称（scope=class 时）"),
    subject_id: Optional[int] = Query(None, description="科目ID"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取学生排行榜（支持按教师+科目聚合）

    - subject_id + teacher_id：按教师+科目排（如"张老师的数学"）
    - 只有 subject_id：按科目排（全校数学排名）
    - 只有 teacher_id：按教师排（张老师教的所有科目）
    - 都不传：按 scope/class_name 排（现有逻辑）
    """
    # ... 现有逻辑 ...

    # 如果有 subject_id 或 teacher_id，按科目分数排
    if subject_id or teacher_id:
        data = get_subject_leaderboard(
            session,
            subject_id=subject_id,
            teacher_id=teacher_id,
            limit=limit,
            current_student_id=current_student_id
        )
    else:
        # 现有逻辑（按总分排）
        data = get_leaderboard(...)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: data
    }
```

修改 `backend/app/crud/leaderboard.py` 加新函数：

```python
def get_subject_leaderboard(
    session: Session,
    subject_id: Optional[int] = None,
    teacher_id: Optional[int] = None,
    limit: int = 50,
    current_student_id: Optional[str] = None
) -> Dict[str, Any]:
    """按教师+科目聚合排行榜"""
    # 查询学生科目分数
    query = select(StudentSubjectScore, Student, Subject, User).join(
        Student, StudentSubjectScore.student_id == Student.student_id
    ).join(
        Subject, StudentSubjectScore.subject_id == Subject.id
    ).join(
        User, StudentSubjectScore.teacher_id == User.id
    ).where(
        StudentSubjectScore.semester == get_current_term(),
        Student.is_account_enabled.is_(True)
    )

    if subject_id:
        query = query.where(StudentSubjectScore.subject_id == subject_id)
    if teacher_id:
        query = query.where(StudentSubjectScore.teacher_id == teacher_id)

    # 按分数降序排序
    query = query.order_by(StudentSubjectScore.score.desc())

    # 获取前 limit 条
    results = session.exec(query.limit(limit)).all()

    # 计算排名
    ranked_students = []
    for i, (score_record, student, subject, teacher) in enumerate(results):
        ranked_students.append({
            "rank": i + 1,
            "student_id": student.student_id,
            "name": student.name,
            "class_name": student.class_name,
            "subject_name": subject.name,
            "teacher_name": teacher.name,
            "score": score_record.score
        })

    # 获取当前学生的排名
    my_rank = None
    if current_student_id:
        # ... 类似现有逻辑 ...

    return {
        "students": ranked_students,
        "total": len(ranked_students),
        "my_rank": my_rank
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n student-manage pytest tests/integration/test_leaderboard_api.py -v`
Expected: PASS（全部通过）

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/routes/leaderboard.py backend/app/crud/leaderboard.py tests/integration/test_leaderboard_api.py
git commit -m "feat(leaderboard): support subject and teacher aggregation"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

## Phase 7-10：前端改造

### Task 7: 前端科目管理页

**Files:**
- Create: `frontend-v3/src/api/subjects.ts`
- Create: `frontend-v3/src/composables/useSubjects.ts`
- Create: `frontend-v3/src/views/admin/Subjects.vue`
- Create: `frontend-v3/src/views/teacher/Subjects.vue`
- Modify: `frontend-v3/src/api/index.ts`
- Modify: `frontend-v3/src/router/index.ts`
- Test: `frontend-v3/test/views/admin/Subjects.spec.ts`

- [ ] **Step 1: API 客户端**

创建 `frontend-v3/src/api/subjects.ts`：

```typescript
/**
 * 科目 API
 */
import { get, post, put } from '@/lib/api'

export interface Subject {
  id: number
  name: string
  semester: string
}

export const subjectsApi = {
  getAll: () => get<Subject[]>('/subjects'),
  update: (id: number, name: string) => put(`/subjects/${id}`, { name }),
  derive: () => post('/subjects/derive', {}),
}
```

修改 `frontend-v3/src/api/index.ts` 追加导出：

```typescript
export { subjectsApi } from './subjects'
export type { Subject } from './subjects'
```

- [ ] **Step 2: composable**

创建 `frontend-v3/src/composables/useSubjects.ts`：

```typescript
/**
 * 科目列表
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { subjectsApi } from '@/api'

export function useSubjects() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['subjects'],
    queryFn: () => subjectsApi.getAll(),
    staleTime: 5 * 60 * 1000, // 5 分钟
  })
  return { data, isPending, error, refetch }
}

export function useUpdateSubject() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      subjectsApi.update(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] })
    },
  })
  return { mutateAsync, isPending }
}

export function useDeriveSubjects() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending } = useMutation({
    mutationFn: () => subjectsApi.derive(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subjects'] })
    },
  })
  return { mutateAsync, isPending }
}
```

- [ ] **Step 3: 科目管理页**

创建 `frontend-v3/src/views/admin/Subjects.vue`（admin）和 `frontend-v3/src/views/teacher/Subjects.vue`（teacher，内容相同）：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useSubjects, useUpdateSubject, useDeriveSubjects } from '@/composables/useSubjects'
import { Button } from '@/components/ui'
import { Dialog } from '@/components/ui'
import { Input } from '@/components/ui'
import { useToast } from '@/composables/useToast'

const { data: subjects, isPending } = useSubjects()
const { mutateAsync: updateSubject } = useUpdateSubject()
const { mutateAsync: deriveSubjects } = useDeriveSubjects()
const { success, error: showError } = useToast()

const showEditDialog = ref(false)
const editingSubject = ref<{ id: number; name: string } | null>(null)
const newName = ref('')

function openEditDialog(subject: { id: number; name: string }) {
  editingSubject.value = subject
  newName.value = subject.name
  showEditDialog.value = true
}

async function handleUpdate() {
  if (!editingSubject.value || !newName.value.trim()) return
  try {
    await updateSubject({ id: editingSubject.value.id, name: newName.value.trim() })
    success('科目已更新')
    showEditDialog.value = false
  } catch (err) {
    showError('更新失败')
  }
}

async function handleDerive() {
  try {
    const result = await deriveSubjects()
    success(`已推导 ${result.created_count} 个科目`)
  } catch (err) {
    showError('推导失败')
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">科目管理</h1>
      <Button @click="handleDerive">从课表推导</Button>
    </div>

    <div v-if="isPending" class="text-center py-8">加载中...</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="subject in subjects"
        :key="subject.id"
        class="border rounded-lg p-4 hover:shadow-md transition-shadow"
      >
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-medium">{{ subject.name }}</h3>
          <Button variant="outline" size="sm" @click="openEditDialog(subject)">修改</Button>
        </div>
      </div>
    </div>

    <Dialog v-model:open="showEditDialog" title="修改科目名称">
      <div class="space-y-4">
        <Input v-model="newName" placeholder="科目名称" />
      </div>
      <template #footer>
        <Button variant="outline" @click="showEditDialog = false">取消</Button>
        <Button @click="handleUpdate">确认</Button>
      </template>
    </Dialog>
  </div>
</template>
```

修改 `frontend-v3/src/router/index.ts` 加路由：

```typescript
{
  path: 'subjects',
  name: 'AdminSubjects',
  component: () => import('@/views/admin/Subjects.vue'),
},
// teacher 路由同样加
```

- [ ] **Step 4: 测试**

创建 `frontend-v3/test/views/admin/Subjects.spec.ts`：

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import Subjects from '@/views/admin/Subjects.vue'

// Mock composables
vi.mock('@/composables/useSubjects', () => ({
  useSubjects: vi.fn(() => ({
    data: { value: [{ id: 1, name: '数学', semester: '2026-2027-1' }] },
    isPending: { value: false },
  })),
  useUpdateSubject: vi.fn(() => ({ mutateAsync: vi.fn() })),
  useDeriveSubjects: vi.fn(() => ({ mutateAsync: vi.fn() })),
}))

describe('Subjects', () => {
  it('renders subject list', () => {
    const wrapper = mount(Subjects)
    expect(wrapper.text()).toContain('数学')
  })

  it('opens edit dialog when clicking edit button', async () => {
    const wrapper = mount(Subjects)
    await wrapper.find('button').trigger('click')
    expect(wrapper.vm.showEditDialog).toBe(true)
  })
})
```

- [ ] **Step 5: 验证**

Run: `cd frontend-v3 && pnpm vitest run test/views/admin/Subjects.spec.ts 2>&1 | tail -3`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend-v3/src/api/subjects.ts frontend-v3/src/composables/useSubjects.ts frontend-v3/src/views/admin/Subjects.vue frontend-v3/src/views/teacher/Subjects.vue frontend-v3/src/api/index.ts frontend-v3/src/router/index.ts frontend-v3/test/views/admin/Subjects.spec.ts
git commit -m "feat(subject): add subject management page"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

### Task 8: 前端学生管理页改造

**Files:**
- Modify: `frontend-v3/src/views/admin/Students.vue`
- Modify: `frontend-v3/src/views/teacher/Students.vue`
- Modify: `frontend-v3/src/api/students.ts`
- Test: `frontend-v3/test/views/admin/Students.spec.ts`

- [ ] **Step 1: API 客户端加科目分数接口**

修改 `frontend-v3/src/api/students.ts` 追加：

```typescript
export interface StudentSubjectScore {
  subject_id: number
  subject_name: string
  teacher_id: number
  teacher_name: string
  score: number
}

export const studentsApi = {
  // ... 现有方法 ...
  getSubjects: (studentId: string) => get<StudentSubjectScore[]>(`/students/${studentId}/subjects`),
  updateSubjectScore: (studentId: string, subjectId: number, scoreChange: number, reason: string) =>
    put(`/students/${studentId}/subjects/${subjectId}/score`, { score_change: scoreChange, reason }),
}
```

- [ ] **Step 2: 学生管理页加科目分数展示**

修改 `frontend-v3/src/views/admin/Students.vue` 和 `teacher/Students.vue`：

1. 学生列表每行加"科目分数"展开按钮
2. 点击展开显示该学生所有科目分数（科目名 + 分数 + 教师名）
3. 分数管理改为按科目（下拉选科目 + 加减分）

参照现有页面的展开行模式（如失物招领的展开详情）。

- [ ] **Step 3: 测试**

在 `frontend-v3/test/views/admin/Students.spec.ts` 追加：

```typescript
it('shows subject scores when expanding student row', async () => {
  // 测试展开行显示科目分数
})
```

- [ ] **Step 4: 验证**

1. `cd frontend-v3 && pnpm test:run 2>&1 | tail -3`
2. `cd frontend-v3 && pnpm exec vue-tsc --noEmit 2>&1 | tail -2`

- [ ] **Step 5: 提交**

```bash
git add frontend-v3/src/views/admin/Students.vue frontend-v3/src/views/teacher/Students.vue frontend-v3/src/api/students.ts frontend-v3/test/views/admin/Students.spec.ts
git commit -m "feat(students): add subject scores display in student management"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

### Task 9: 前端学生 Dashboard 改造

**Files:**
- Modify: `frontend-v3/src/views/student/Dashboard.vue`
- Test: `frontend-v3/test/views/student/Dashboard.spec.ts`

- [ ] **Step 1: "我的科目"卡片列表**

修改 `frontend-v3/src/views/student/Dashboard.vue`：

1. 删除"我的排名"卡片（或改为按科目显示）
2. 加"我的科目"卡片列表（每个科目一张卡片：科目名 + 分数 + 排名）
3. 点击卡片进入科目详情页（该科目的分数历史）

- [ ] **Step 2: 测试**

在 `frontend-v3/test/views/student/Dashboard.spec.ts` 追加：

```typescript
it('shows subject cards', async () => {
  // 测试显示多个科目卡片
})
```

- [ ] **Step 3: 验证**

1. `cd frontend-v3 && pnpm test:run 2>&1 | tail -3`
2. `cd frontend-v3 && pnpm exec vue-tsc --noEmit 2>&1 | tail -2`

- [ ] **Step 4: 提交**

```bash
git add frontend-v3/src/views/student/Dashboard.vue frontend-v3/test/views/student/Dashboard.spec.ts
git commit -m "feat(dashboard): add subject cards for student"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

---

### Task 10: 前端排行榜改造

**Files:**
- Modify: `frontend-v3/src/views/student/Leaderboard.vue`
- Modify: `frontend-v3/src/composables/useLeaderboard.ts`
- Test: `frontend-v3/test/views/student/Leaderboard.spec.ts`

- [ ] **Step 1: 加科目/教师筛选器**

修改 `frontend-v3/src/views/student/Leaderboard.vue`：

1. 加科目筛选器（下拉选科目）
2. 加教师筛选器（下拉选教师）
3. 默认显示当前学期第一个科目

修改 `frontend-v3/src/composables/useLeaderboard.ts`：

```typescript
export function useLeaderboard(params: { scope?: string; subject_id?: number; teacher_id?: number }) {
  // ... 加 subject_id/teacher_id 参数
}
```

- [ ] **Step 2: 测试**

在 `frontend-v3/test/views/student/Leaderboard.spec.ts` 追加：

```typescript
it('filters by subject and teacher', async () => {
  // 测试科目/教师筛选器
})
```

- [ ] **Step 3: 验证**

1. `cd frontend-v3 && pnpm test:run 2>&1 | tail -3`
2. `cd frontend-v3 && pnpm exec vue-tsc --noEmit 2>&1 | tail -2`

- [ ] **Step 4: 提交**

```bash
git add frontend-v3/src/views/student/Leaderboard.vue frontend-v3/src/composables/useLeaderboard.ts frontend-v3/test/views/student/Leaderboard.spec.ts
git commit -m "feat(leaderboard): add subject and teacher filters"
```

（末尾加 Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>）

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
