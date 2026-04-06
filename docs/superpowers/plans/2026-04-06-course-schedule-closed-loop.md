# ClassHub 课程表闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 废弃 `class_session` 表，建立 `course_sessions` 作为单次上课实例主表，打通课表与签到闭环，支持调课/停课/补课。

**Architecture:** 新建 `course_sessions` 和 `schedule_adjustments` 表，将原 `ClassSession` 的职责迁移至 `CourseSession`，所有签到记录改关联新表。API 路由从 `/class-session/*` 迁移至 `/course-sessions/*`。

**Tech Stack:** FastAPI + SQLModel (backend), Vue 3 + TypeScript + TanStack Query (frontend), pytest + Vitest (testing)

---

## File Structure Overview

**Backend - New Files:**
- `backend/app/models/course_session.py` — CourseSession + ScheduleAdjustment 模型
- `backend/app/crud/course_session.py` — CourseSession CRUD 操作
- `backend/app/crud/schedule_adjustment.py` — 调课/停课/补课 CRUD
- `backend/app/api/routes/course_sessions.py` — 课堂实例 API（替换 checkin.py 的 class-session 部分）
- `backend/app/api/routes/schedule_adjustments.py` — 调课 API

**Backend - Modified Files:**
- `backend/app/models/checkin.py` — 移除 ClassSession，修改 CheckinRecord 外键
- `backend/app/models/course_schedule.py` — 增加 week_type 字段
- `backend/app/models/__init__.py` — 更新导出
- `backend/app/crud/checkin.py` — 重构活跃课堂查询逻辑到 CourseSession
- `backend/app/crud/__init__.py` — 更新导出
- `backend/app/api/routes/checkin.py` — 移除 class-session 路由，改为引用 course_sessions
- `backend/app/api/routes/schedules.py` — 增强 `/schedules/today` 接口
- `backend/app/api/routes/__init__.py` — 注册新路由

**Frontend - New Files:**
- `frontend-v3/src/api/courseSession.ts` — CourseSession API 客户端
- `frontend-v3/src/api/scheduleAdjustment.ts` — 调课 API 客户端
- `frontend-v3/src/composables/useCourseSessions.ts` — 替换 useClassSession.ts
- `frontend-v3/src/composables/useScheduleAdjustments.ts` — 调课相关 composables
- `frontend-v3/src/components/teacher/ScheduleAdjustmentDialog.vue` — 调课弹窗
- `frontend-v3/src/views/teacher/SessionsHistory.vue` — 历史课堂页面

**Frontend - Modified Files:**
- `frontend-v3/src/types/api.ts` — 增加 CourseSession, ScheduleAdjustment, TodaySchedule 类型
- `frontend-v3/src/api/index.ts` — 导出新 API 模块
- `frontend-v3/src/api/checkin.ts` — 移除 classSessionApi 相关，仅保留 checkin
- `frontend-v3/src/api/classSession.ts` — 废弃，内容迁移到 courseSession.ts
- `frontend-v3/src/router/index.ts` — 添加 `/teacher/sessions-history` 路由
- `frontend-v3/src/views/teacher/Dashboard.vue` — 增强今日课表卡片
- `frontend-v3/src/views/teacher/ClassSession.vue` — 支持快捷开课和课堂来源显示
- `frontend-v3/src/views/teacher/Schedules.vue` — 添加调课按钮

**Tests:**
- `tests/unit/crud/test_course_session.py` — CourseSession CRUD 单元测试
- `tests/unit/crud/test_schedule_adjustment.py` — 调课规则单元测试
- `tests/integration/test_course_session_api.py` — CourseSession API 集成测试
- `tests/integration/test_schedule_adjustment_api.py` — 调课 API 集成测试
- `tests/integration/test_checkin_api_enhanced.py` — 更新现有测试适配新表

---

## Phase 1: Backend Data Models

### Task 1.1: Create CourseSession and ScheduleAdjustment models

**Files:**
- Create: `backend/app/models/course_session.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write new model file**

Create `backend/app/models/course_session.py`:

```python
"""
课程会话模型 - 单次上课实例 + 课表调整记录
"""
from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field
from app.core.timezone import get_now


class CourseSessionBase(SQLModel):
    """课程会话基础模型"""
    schedule_id: Optional[int] = Field(
        default=None,
        foreign_key="course_schedules.id",
        description="关联的课表ID"
    )
    session_code: str = Field(..., description="课堂唯一代码", max_length=16)
    course_name: Optional[str] = Field(default=None, description="课程名称", max_length=100)
    class_name: str = Field(..., description="班级名称", max_length=100)
    classroom: Optional[str] = Field(default=None, description="教室", max_length=50)
    teacher_id: int = Field(..., description="教师ID")
    teacher_name: Optional[str] = Field(default=None, description="教师姓名", max_length=50)
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    week_number: Optional[int] = Field(default=None, description="教学周次")
    status: str = Field(default="active", description="课堂状态: active|ended|cancelled", max_length=20)
    source_type: str = Field(default="manual", description="来源类型: scheduled|manual|makeup", max_length=20)


class CourseSession(CourseSessionBase, table=True):
    """课程会话数据库模型"""
    __tablename__ = "course_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    updated_at: datetime = Field(default_factory=get_now, description="更新时间")


class CourseSessionResponse(CourseSessionBase):
    """课程会话响应模型"""
    id: int
    updated_at: str


class ScheduleAdjustmentBase(SQLModel):
    """课表调整基础模型"""
    schedule_id: int = Field(..., foreign_key="course_schedules.id", description="关联课表ID")
    week_number: int = Field(..., description="第几周")
    type: str = Field(..., description="调整类型: cancel|modify|makeup", max_length=20)
    new_date: Optional[date] = Field(default=None, description="新日期")
    new_start_time: Optional[str] = Field(default=None, description="新开始时间", max_length=10)
    new_end_time: Optional[str] = Field(default=None, description="新结束时间", max_length=10)
    new_classroom: Optional[str] = Field(default=None, description="新教室", max_length=50)
    generated_session_id: Optional[int] = Field(
        default=None,
        foreign_key="course_sessions.id",
        description="补课生成的课堂实例ID"
    )
    reason: Optional[str] = Field(default=None, description="调整原因", max_length=200)
    created_by: int = Field(..., description="操作人ID")


class ScheduleAdjustment(ScheduleAdjustmentBase, table=True):
    """课表调整记录数据库模型"""
    __tablename__ = "schedule_adjustments"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")


class ScheduleAdjustmentResponse(ScheduleAdjustmentBase):
    """课表调整响应模型"""
    id: int
    created_at: str
```

- [ ] **Step 2: Update `backend/app/models/__init__.py`**

Add to imports:

```python
from app.models.course_session import CourseSession, ScheduleAdjustment, CourseSessionResponse
```

Add to `__all__`:

```python
"CourseSession", "ScheduleAdjustment", "CourseSessionResponse",
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/course_session.py backend/app/models/__init__.py
git commit -m "feat(models): add CourseSession and ScheduleAdjustment models"
```

### Task 1.2: Refactor CheckinRecord and remove ClassSession

**Files:**
- Modify: `backend/app/models/checkin.py`

- [ ] **Step 1: Rewrite checkin.py**

Replace the entire `backend/app/models/checkin.py`:

```python
"""
签到相关模型 - SQLModel 版本
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.models.constants import CheckinTypeConst
from app.core.timezone import get_now


class CheckinRecord(SQLModel, table=True):
    """签到记录表"""
    __tablename__ = "checkin_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(
        default=None,
        foreign_key="course_sessions.id",
        description="课堂会话ID",
        index=True
    )
    student_id: str = Field(..., description="学号", index=True)
    student_name: Optional[str] = Field(default=None, description="学生姓名")
    class_name: Optional[str] = Field(default=None, description="班级", index=True)
    checkin_type: str = Field(default=CheckinTypeConst.SELF, description="签到类型")
    checkin_time: datetime = Field(default_factory=get_now, description="签到时间")
    device_id: Optional[str] = Field(default=None, description="设备指纹ID", index=True)
    device_info: Optional[str] = Field(default=None, description="设备信息JSON")


class ScoreLog(SQLModel, table=True):
    """分数变更日志表"""
    __tablename__ = "score_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(..., description="学号", index=True)
    old_score: Optional[float] = Field(default=None, description="旧分数")
    new_score: Optional[float] = Field(default=None, description="新分数")
    delta: Optional[float] = Field(default=None, description="变化值")
    reason: Optional[str] = Field(default=None, description="原因")
    operator: Optional[str] = Field(default=None, description="操作人")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
```

- [ ] **Step 2: Update `backend/app/models/__init__.py` to remove ClassSession references**

Change:
```python
from app.models.checkin import CheckinRecord, ClassSession, ScoreLog
```
to:
```python
from app.models.checkin import CheckinRecord, ScoreLog
```

Remove `"ClassSession"` from `__all__`.

- [ ] **Step 3: Verify backend can import without ClassSession**

Run:
```bash
cd /home/yufeng/student-manager/backend && conda run -n student-manage python -c "from app.models import CheckinRecord, ScoreLog, CourseSession, ScheduleAdjustment; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/checkin.py backend/app/models/__init__.py
git commit -m "refactor(models): remove ClassSession, migrate CheckinRecord to course_sessions"
```

### Task 1.3: Add week_type to CourseSchedule

**Files:**
- Modify: `backend/app/models/course_schedule.py`

- [ ] **Step 1: Add week_type field**

Add inside `CourseScheduleBase`:

```python
week_type: str = Field(default="all", description="周类型: all|odd|even|custom", max_length=20)
```

And add to `CourseScheduleImport`:

```python
week_type: Optional[str] = "all"
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/course_schedule.py
git commit -m "feat(models): add week_type to CourseSchedule"
```

---

## Phase 2: Backend CRUD Layer

### Task 2.1: Create CourseSession CRUD

**Files:**
- Create: `backend/app/crud/course_session.py`
- Modify: `backend/app/crud/__init__.py`

- [ ] **Step 1: Write course_session.py**

Create `backend/app/crud/course_session.py`:

```python
"""
CourseSession CRUD 操作
"""
from datetime import datetime, date
from typing import List, Optional
import uuid
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.models import CourseSession

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def get_course_session(session: Session, session_id: int) -> Optional[CourseSession]:
    """根据ID获取课程会话"""
    return session.get(CourseSession, session_id)


def get_active_course_session_by_class_name(session: Session, class_name: str) -> Optional[CourseSession]:
    """根据班级名称获取活跃课程会话"""
    query = select(CourseSession).where(
        CourseSession.class_name == class_name,
        CourseSession.status == "active"
    )
    return session.exec(query).first()


def get_teacher_active_course_sessions(session: Session, teacher_id: int) -> List[CourseSession]:
    """获取教师所有活跃课程会话"""
    query = select(CourseSession).where(
        CourseSession.teacher_id == teacher_id,
        CourseSession.status == "active"
    )
    return list(session.exec(query).all())


def get_course_sessions_by_schedule_and_week(
    session: Session, schedule_id: int, week_number: int
) -> Optional[CourseSession]:
    """根据课表ID和周次获取课程会话"""
    query = select(CourseSession).where(
        CourseSession.schedule_id == schedule_id,
        CourseSession.week_number == week_number
    )
    return session.exec(query).first()


def start_course_session(
    session: Session,
    class_name: str,
    teacher_id: int,
    teacher_name: Optional[str] = None,
    course_name: Optional[str] = None,
    schedule_id: Optional[int] = None,
    week_number: Optional[int] = None,
    classroom: Optional[str] = None,
    source_type: str = "manual"
) -> CourseSession:
    """开始上课 - 创建新的课程会话记录"""
    session_code = str(uuid.uuid4())[:8].upper()
    course_session = CourseSession(
        session_code=session_code,
        schedule_id=schedule_id,
        course_name=course_name,
        class_name=class_name,
        classroom=classroom,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        status="active",
        start_time=datetime.now(SHANGHAI_TZ),
        week_number=week_number,
        source_type=source_type,
    )
    session.add(course_session)
    session.commit()
    session.refresh(course_session)
    return course_session


def end_course_session(
    session: Session,
    teacher_id: int,
    class_name: Optional[str] = None
) -> List[CourseSession]:
    """结束上课"""
    query = select(CourseSession).where(
        CourseSession.teacher_id == teacher_id,
        CourseSession.status == "active"
    )
    if class_name:
        query = query.where(CourseSession.class_name == class_name)

    sessions = session.exec(query).all()
    ended_sessions = []
    for cs in sessions:
        cs.status = "ended"
        cs.end_time = datetime.now(SHANGHAI_TZ)
        cs.updated_at = datetime.now(SHANGHAI_TZ)
        session.add(cs)
        ended_sessions.append(cs)

    if ended_sessions:
        session.commit()

    return ended_sessions
```

- [ ] **Step 2: Update `backend/app/crud/__init__.py`**

Add imports:

```python
from app.crud.course_session import (
    get_course_session,
    get_active_course_session_by_class_name,
    get_teacher_active_course_sessions,
    get_course_sessions_by_schedule_and_week,
    start_course_session,
    end_course_session,
)
```

- [ ] **Step 3: Verify import**

Run:
```bash
cd /home/yufeng/student-manager/backend && conda run -n student-manage python -c "from app.crud.course_session import start_course_session; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/crud/course_session.py backend/app/crud/__init__.py
git commit -m "feat(crud): add CourseSession CRUD operations"
```

### Task 2.2: Create ScheduleAdjustment CRUD

**Files:**
- Create: `backend/app/crud/schedule_adjustment.py`
- Modify: `backend/app/crud/__init__.py`

- [ ] **Step 1: Write schedule_adjustment.py**

Create `backend/app/crud/schedule_adjustment.py`:

```python
"""
课表调整记录 CRUD 操作
"""
from datetime import date
from typing import List, Optional
from sqlmodel import Session, select
from app.models import ScheduleAdjustment, CourseSession


def get_adjustment(
    session: Session, schedule_id: int, week_number: int
) -> Optional[ScheduleAdjustment]:
    """获取指定课表和周次的调整记录"""
    query = select(ScheduleAdjustment).where(
        ScheduleAdjustment.schedule_id == schedule_id,
        ScheduleAdjustment.week_number == week_number
    )
    return session.exec(query).first()


def get_adjustments(
    session: Session,
    schedule_id: Optional[int] = None,
    week_number: Optional[int] = None,
    class_name: Optional[str] = None,
) -> List[ScheduleAdjustment]:
    """查询调整记录列表"""
    query = select(ScheduleAdjustment)
    if schedule_id is not None:
        query = query.where(ScheduleAdjustment.schedule_id == schedule_id)
    if week_number is not None:
        query = query.where(ScheduleAdjustment.week_number == week_number)
    if class_name is not None:
        from app.models import CourseSchedule
        query = query.join(CourseSchedule).where(CourseSchedule.class_name == class_name)
    return list(session.exec(query).order_by(ScheduleAdjustment.created_at.desc()).all())


def create_adjustment(
    session: Session,
    schedule_id: int,
    week_number: int,
    adjustment_type: str,
    created_by: int,
    reason: Optional[str] = None,
    new_date: Optional[date] = None,
    new_start_time: Optional[str] = None,
    new_end_time: Optional[str] = None,
    new_classroom: Optional[str] = None,
    generated_session_id: Optional[int] = None,
) -> ScheduleAdjustment:
    """创建调整记录"""
    adjustment = ScheduleAdjustment(
        schedule_id=schedule_id,
        week_number=week_number,
        type=adjustment_type,
        reason=reason,
        new_date=new_date,
        new_start_time=new_start_time,
        new_end_time=new_end_time,
        new_classroom=new_classroom,
        generated_session_id=generated_session_id,
        created_by=created_by,
    )
    session.add(adjustment)
    session.commit()
    session.refresh(adjustment)
    return adjustment


def has_active_session(
    session: Session, schedule_id: int, week_number: int
) -> bool:
    """检查指定课表和周次是否有活跃课堂"""
    from app.crud.course_session import get_course_sessions_by_schedule_and_week
    cs = get_course_sessions_by_schedule_and_week(session, schedule_id, week_number)
    return cs is not None and cs.status == "active"


def has_ended_session(
    session: Session, schedule_id: int, week_number: int
) -> bool:
    """检查指定课表和周次是否有已结束课堂"""
    from app.crud.course_session import get_course_sessions_by_schedule_and_week
    cs = get_course_sessions_by_schedule_and_week(session, schedule_id, week_number)
    return cs is not None and cs.status == "ended"
```

- [ ] **Step 2: Update `backend/app/crud/__init__.py`**

Add imports:

```python
from app.crud.schedule_adjustment import (
    get_adjustment,
    get_adjustments,
    create_adjustment,
    has_active_session,
    has_ended_session,
)
```

- [ ] **Step 3: Verify import**

Run:
```bash
cd /home/yufeng/student-manager/backend && conda run -n student-manage python -c "from app.crud.schedule_adjustment import create_adjustment; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/crud/schedule_adjustment.py backend/app/crud/__init__.py
git commit -m "feat(crud): add ScheduleAdjustment CRUD operations"
```

### Task 2.3: Refactor checkin CRUD to use CourseSession

**Files:**
- Modify: `backend/app/crud/checkin.py`

- [ ] **Step 1: Replace class_session references with course_session**

Rewrite `backend/app/crud/checkin.py` to remove old `ClassSession` based functions and import from `course_session.py`:

```python
"""
签到相关 CRUD 操作
"""
from datetime import datetime, date
from typing import List, Optional
from sqlmodel import Session, select, func
from app.models import CheckinRecord, ScoreLog
from app.core.timezone import get_now


def get_today_checkins(
    session: Session, class_name: Optional[str] = None, session_start: Optional[datetime] = None
) -> List[CheckinRecord]:
    """获取签到列表（支持按课堂开始时间筛选）"""
    from datetime import time

    if session_start:
        query_start = session_start
    else:
        query_start = datetime.combine(date.today(), time.min).replace(tzinfo=get_now().tzinfo)

    query = select(CheckinRecord).where(CheckinRecord.checkin_time >= query_start)
    if class_name:
        query = query.where(CheckinRecord.class_name == class_name)
    return list(session.exec(query).all())


def count_today_checkins(session: Session, class_name: Optional[str] = None) -> int:
    """使用 SQL COUNT 计算今日签到数"""
    from datetime import time

    today_start = datetime.combine(date.today(), time.min)

    query = select(func.count()).select_from(CheckinRecord).where(
        CheckinRecord.checkin_time >= today_start
    )
    if class_name:
        query = query.where(CheckinRecord.class_name == class_name)

    result = session.exec(query)
    return result.one()


def create_checkin(
    session: Session, student_id: str, student_name: str,
    class_name: str, session_id: int, checkin_type: Optional[str] = None,
    device_id: Optional[str] = None, device_info: Optional[str] = None
) -> CheckinRecord:
    """创建签到记录"""
    from app.models.constants import CheckinTypeConst
    if checkin_type is None:
        checkin_type = CheckinTypeConst.SELF
    checkin = CheckinRecord(
        session_id=session_id,
        student_id=student_id,
        student_name=student_name,
        class_name=class_name,
        checkin_type=checkin_type,
        device_id=device_id,
        device_info=device_info
    )
    session.add(checkin)
    session.commit()
    session.refresh(checkin)
    return checkin


def has_checked_in_session(session: Session, student_id: str, session_id: int) -> bool:
    """检查学生是否已在指定课堂签到"""
    query = select(CheckinRecord).where(
        CheckinRecord.student_id == student_id,
        CheckinRecord.session_id == session_id
    )
    return session.exec(query).first() is not None


def has_checked_in_today(
    session: Session, student_id: str, class_name: Optional[str] = None,
    session_start: Optional[datetime] = None
) -> bool:
    """检查是否已签到（支持按班级和课堂开始时间检查）- 兼容旧逻辑"""
    from datetime import time

    if session_start:
        query_start = session_start
    else:
        query_start = datetime.combine(date.today(), time.min).replace(tzinfo=get_now().tzinfo)

    query = select(CheckinRecord).where(
        CheckinRecord.student_id == student_id,
        CheckinRecord.checkin_time >= query_start
    )
    if class_name:
        query = query.where(CheckinRecord.class_name == class_name)
    return session.exec(query).first() is not None


def get_student_score_logs(session: Session, student_id: str, limit: Optional[int] = None) -> List[ScoreLog]:
    """获取学生分数日志"""
    if limit is None:
        from app.core.config import get_settings
        limit = get_settings().pagination.score_log_default_limit
    query = select(ScoreLog).where(ScoreLog.student_id == student_id).order_by(ScoreLog.created_at.desc()).limit(limit)
    return list(session.exec(query).all())


def is_device_checked_in_session(session: Session, device_id: str, session_id: int) -> bool:
    """检查设备是否已在指定课堂签到过"""
    if not device_id:
        return False
    query = select(CheckinRecord).where(
        CheckinRecord.device_id == device_id,
        CheckinRecord.session_id == session_id
    )
    return session.exec(query).first() is not None
```

- [ ] **Step 2: Update `backend/app/crud/__init__.py` to remove old checkin exports**

Remove old imports like `get_class_session`, `start_class`, `end_class`, etc. Keep only checkin-related ones.

- [ ] **Step 3: Verify import**

Run:
```bash
cd /home/yufeng/student-manager/backend && conda run -n student-manage python -c "from app.crud.checkin import create_checkin; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/crud/checkin.py backend/app/crud/__init__.py
git commit -m "refactor(crud): migrate checkin CRUD from ClassSession to CourseSession"
```

---

## Phase 3: Backend API Routes

### Task 3.1: Create CourseSession API route

**Files:**
- Create: `backend/app/api/routes/course_sessions.py`
- Modify: `backend/app/api/routes/__init__.py`

- [ ] **Step 1: Write course_sessions.py**

Create `backend/app/api/routes/course_sessions.py`:

```python
"""
课程会话 API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user
from app.models import CourseSession, CourseSchedule
from app.models.constants import ApiResponseConst, MessageConst, ApiResponse, ApiSuccessResponse
from app.crud.course_session import (
    get_teacher_active_course_sessions,
    get_active_course_session_by_class_name,
    start_course_session,
    end_course_session,
)
from app.crud.schedule_adjustment import get_adjustment

router = APIRouter(tags=["course_sessions"])


class StartCourseSessionRequest:
    class_name: str
    course_name: Optional[str] = None
    schedule_id: Optional[int] = None


from pydantic import BaseModel


class StartCourseSessionRequest(BaseModel):
    class_name: str
    course_name: Optional[str] = None
    schedule_id: Optional[int] = None


class EndCourseSessionRequest(BaseModel):
    class_name: Optional[str] = None


class CourseSessionData(BaseModel):
    id: int
    active: bool
    course_name: Optional[str] = None
    class_name: str
    start_time: Optional[datetime] = None
    status: str
    session_code: str
    schedule_id: Optional[int] = None
    week_number: Optional[int] = None
    source_type: str


class CourseSessionListResponse(ApiResponse[list[CourseSessionData]]):
    pass


class CourseSessionResponse(ApiResponse[CourseSessionData]):
    pass


@router.get("/course-sessions", response_model=CourseSessionListResponse)
def get_course_sessions(
    request: Request,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取当前教师的课程会话列表"""
    teacher_id = int(user.get("sub", 0))
    sessions = get_teacher_active_course_sessions(session, teacher_id)

    data = []
    for cs in sessions:
        data.append({
            "id": cs.id,
            "active": cs.status == "active",
            "course_name": cs.course_name,
            "class_name": cs.class_name,
            "start_time": cs.start_time,
            "status": cs.status,
            "session_code": cs.session_code,
            "schedule_id": cs.schedule_id,
            "week_number": cs.week_number,
            "source_type": cs.source_type,
        })

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: data
    }


@router.post("/course-sessions/start", response_model=CourseSessionResponse)
def begin_course_session(
    request: Request,
    data: StartCourseSessionRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """开始上课"""
    existing = get_active_course_session_by_class_name(session, data.class_name)
    if existing:
        teacher_name = existing.teacher_name or "其他教师"
        raise HTTPException(
            status_code=HttpStatus.CONFLICT,
            detail=f"该班级正在被 {teacher_name} 老师上课，无法开始新课堂"
        )

    teacher_id = int(user.get("sub", 0))
    teacher_name = user.get("name", "")

    schedule_id = data.schedule_id
    week_number = None
    classroom = None
    source_type = "manual"

    if schedule_id:
        schedule = session.get(CourseSchedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课表不存在")
        if schedule.class_name != data.class_name:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="班级与课表不匹配")
        if data.course_name and schedule.course_name != data.course_name:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="课程名称与课表不匹配")
        week_number = _get_current_week_number()
        classroom = schedule.classroom
        source_type = "scheduled"
        if not data.course_name:
            data.course_name = schedule.course_name

    course_session = start_course_session(
        session=session,
        class_name=data.class_name,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        course_name=data.course_name,
        schedule_id=schedule_id,
        week_number=week_number,
        classroom=classroom,
        source_type=source_type,
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_STARTED,
        ApiResponseConst.DATA: {
            "id": course_session.id,
            "active": True,
            "course_name": course_session.course_name,
            "class_name": course_session.class_name,
            "start_time": course_session.start_time,
            "status": course_session.status,
            "session_code": course_session.session_code,
            "schedule_id": course_session.schedule_id,
            "week_number": course_session.week_number,
            "source_type": course_session.source_type,
        }
    }


@router.post("/course-sessions/{session_id}/end", response_model=ApiSuccessResponse)
def finish_course_session(
    session_id: int,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """结束指定课程会话"""
    teacher_id = int(user.get("sub", 0))
    cs = session.get(CourseSession, session_id)
    if not cs or cs.teacher_id != teacher_id:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课堂不存在")
    if cs.status != "active":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="课堂未在活跃状态")

    cs.status = "ended"
    from app.core.timezone import get_now
    cs.end_time = get_now()
    cs.updated_at = get_now()
    session.add(cs)
    session.commit()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CLASS_ENDED
    }


@router.get("/course-sessions/class/{class_name}", response_model=ApiResponse[dict])
async def get_course_session_for_class(
    class_name: str,
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取指定班级的活跃课程会话（学生端使用）"""
    cs = get_active_course_session_by_class_name(session, class_name)
    if cs and cs.status == "active":
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                "id": cs.id,
                "session_code": cs.session_code,
                "active": True,
                "course_name": cs.course_name,
                "class_name": cs.class_name,
                "teacher_name": cs.teacher_name,
                "start_time": cs.start_time,
            }
        }

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {"active": False}
    }


def _get_current_week_number() -> int:
    """获取当前教学周次（与前端 getCurrentWeek 保持一致）"""
    from datetime import datetime
    # 默认以每年2月1日为学期开始，可根据配置扩展
    now = datetime.now()
    semester_start = datetime(now.year, 2, 1)
    if now < semester_start:
        semester_start = datetime(now.year - 1, 2, 1)
    delta = now - semester_start
    week = delta.days // 7 + 1
    return max(1, week)
```

- [ ] **Step 2: Update `backend/app/api/routes/__init__.py`**

Add:

```python
from app.api.routes.course_sessions import router as course_sessions_router
```

Add to `__all__`:

```python
"course_sessions_router",
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/routes/course_sessions.py backend/app/api/routes/__init__.py
git commit -m "feat(api): add CourseSession routes"
```

### Task 3.2: Create ScheduleAdjustment API route

**Files:**
- Create: `backend/app/api/routes/schedule_adjustments.py`
- Modify: `backend/app/api/routes/__init__.py`

- [ ] **Step 1: Write schedule_adjustments.py**

Create `backend/app/api/routes/schedule_adjustments.py`:

```python
"""
课表调整 API
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session
from app.core.db import get_session
from app.core.config import HttpStatus
from app.core.jwt import get_current_user
from app.models import CourseSchedule
from app.models.constants import ApiResponseConst, ApiResponse, ApiSuccessResponse
from app.crud.schedule_adjustment import (
    get_adjustments, create_adjustment, has_active_session, has_ended_session
)
from app.crud.course_session import start_course_session

router = APIRouter(tags=["schedule_adjustments"])


class CreateAdjustmentRequest(BaseModel):
    schedule_id: int
    week_number: int
    type: str
    reason: Optional[str] = None
    new_date: Optional[date] = None
    new_start_time: Optional[str] = None
    new_end_time: Optional[str] = None
    new_classroom: Optional[str] = None


class AdjustmentResponse(ApiResponse[list[dict]]):
    pass


@router.post("/schedule-adjustments", response_model=ApiSuccessResponse)
def create_schedule_adjustment(
    data: CreateAdjustmentRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """创建课表调整记录"""
    user_id = int(user.get("sub", 0))
    role = user.get("role", "")

    # 权限检查
    schedule = session.get(CourseSchedule, data.schedule_id)
    if not schedule:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课表不存在")
    if role == "teacher" and schedule.teacher_id != user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权调整此课程")

    # 停课规则
    if data.type == "cancel":
        if has_active_session(session, data.schedule_id, data.week_number):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="进行中的课程不能停课")

    # 调课规则
    if data.type == "modify":
        if has_ended_session(session, data.schedule_id, data.week_number):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已结束的课程不能调课")

    # 补课规则：创建一个新的 CourseSession
    generated_session_id = None
    if data.type == "makeup":
        if not data.new_date:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="补课必须指定日期")
        course_session = start_course_session(
            session=session,
            class_name=schedule.class_name,
            teacher_id=schedule.teacher_id or user_id,
            teacher_name=schedule.teacher_name,
            course_name=schedule.course_name,
            schedule_id=data.schedule_id,
            week_number=data.week_number,
            classroom=data.new_classroom or schedule.classroom,
            source_type="makeup",
        )
        generated_session_id = course_session.id

    create_adjustment(
        session=session,
        schedule_id=data.schedule_id,
        week_number=data.week_number,
        adjustment_type=data.type,
        created_by=user_id,
        reason=data.reason,
        new_date=data.new_date,
        new_start_time=data.new_start_time,
        new_end_time=data.new_end_time,
        new_classroom=data.new_classroom,
        generated_session_id=generated_session_id,
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "调整记录已创建"
    }


@router.get("/schedule-adjustments", response_model=AdjustmentResponse)
def list_schedule_adjustments(
    schedule_id: Optional[int] = Query(None),
    week_number: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """查询课表调整记录"""
    adjustments = get_adjustments(session, schedule_id=schedule_id, week_number=week_number)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [
            {
                "id": a.id,
                "schedule_id": a.schedule_id,
                "week_number": a.week_number,
                "type": a.type,
                "reason": a.reason,
                "new_date": str(a.new_date) if a.new_date else None,
                "new_start_time": a.new_start_time,
                "new_end_time": a.new_end_time,
                "new_classroom": a.new_classroom,
                "generated_session_id": a.generated_session_id,
                "created_by": a.created_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in adjustments
        ]
    }
```

- [ ] **Step 2: Update `backend/app/api/routes/__init__.py`**

Add:

```python
from app.api.routes.schedule_adjustments import router as schedule_adjustments_router
```

And to `__all__`:

```python
"schedule_adjustments_router",
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/routes/schedule_adjustments.py backend/app/api/routes/__init__.py
git commit -m "feat(api): add ScheduleAdjustment routes"
```

### Task 3.3: Update checkin API to use CourseSession

**Files:**
- Modify: `backend/app/api/routes/checkin.py`

- [ ] **Step 1: Replace class_session imports and logic**

Replace the top of `backend/app/api/routes/checkin.py` with:

```python
"""
签到相关 API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Body, Depends, Request, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from app.core.db import get_session
from app.core.config import HttpStatus
from app.crud import (
    get_today_checkins, create_checkin,
    get_students_by_class
)
from app.crud.course_session import (
    get_active_course_session_by_class_name,
    get_teacher_active_course_sessions,
    end_course_session,
)
from app.core.jwt import get_current_user
from app.models import CourseSession
from app.models.constants import (
    ApiResponseConst, MessageConst,
    ApiResponse, ApiSuccessResponse
)

router = APIRouter(tags=["checkin"])
```

Then update each endpoint:

**`GET /checkins/stats` endpoint change:**
Replace the function body to use `CourseSession`:

```python
@router.get("/checkins/stats", response_model=CheckinStatsResponse)
def get_checkin_stats(
    request: Request,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取签到统计（当前教师的活跃课堂）"""
    teacher_id = int(user.get("sub", 0))
    sessions = get_teacher_active_course_sessions(session, teacher_id)

    if not sessions:
        return {
            ApiResponseConst.SUCCESS: True,
            ApiResponseConst.DATA: {
                'active': False,
                'total': 0,
                'checked_in': 0,
                'not_checked_in': 0,
                'rate': 0
            }
        }

    # 取第一个活跃课堂（若只有一个）
    cs = sessions[0]
    students = get_students_by_class(session, cs.class_name)
    checkins = get_today_checkins(session, cs.class_name, cs.start_time)

    total = len(students)
    checked_in = len(checkins)
    not_checked_in = total - checked_in
    rate = round(checked_in / total * 100, 1) if total > 0 else 0

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            'active': True,
            'course_name': cs.course_name,
            'class_name': cs.class_name,
            'total': total,
            'checked_in': checked_in,
            'not_checked_in': not_checked_in,
            'rate': rate
        }
    }
```

**`POST /checkin` endpoint change:**
Replace class_session lookup:

```python
@router.post("/checkin", response_model=CheckinResponse)
def do_checkin(
    request: Request,
    data: CheckinRequest,
    db_session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """学生签到"""
    from app.crud import get_student
    from app.crud.checkin import has_checked_in_session, is_device_checked_in_session

    student = get_student(db_session, data.student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    cs = get_active_course_session_by_class_name(db_session, student.class_name)
    if not cs or cs.status != "active":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='当前未在上课')

    if has_checked_in_session(db_session, data.student_id, cs.id):
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='您已在本课堂签到')

    if data.device_id:
        if is_device_checked_in_session(db_session, data.device_id, cs.id):
            raise HTTPException(status_code=HttpStatus.CONFLICT, detail='该设备已签到')

    checkin = create_checkin(
        db_session,
        data.student_id,
        data.student_name or student.name,
        cs.class_name,
        cs.id,
        device_id=data.device_id,
        device_info=data.device_info
    )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CHECKIN_SUCCESS,
        ApiResponseConst.DATA: checkin.model_dump()
    }
```

**`GET /checkins/today` endpoint change:**
Replace class_session lookup:

```python
@router.get("/checkins/today", response_model=CheckinListResponse)
def get_today_checkin_list(
    request: Request,
    class_name: Optional[str] = Query(None, description="班级名称"),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """获取今日签到列表"""
    cs = get_active_course_session_by_class_name(session, class_name) if class_name else None

    if cs and cs.status == "active":
        checkins = get_today_checkins(session, class_name, cs.start_time)
    elif class_name:
        checkins = get_today_checkins(session, class_name)
    else:
        checkins = get_today_checkins(session)

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: [c.model_dump() for c in checkins]
    }
```

**Remove old `/class-session/*` endpoints** from `backend/app/api/routes/checkin.py` entirely.

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/routes/checkin.py
git commit -m "refactor(api): migrate checkin routes to use CourseSession"
```

### Task 3.4: Register new routes in main app

**Files:**
- Find main app registration (likely `backend/app/main.py` or similar router setup)

- [ ] **Step 1: Add new routers to FastAPI app**

Look for where routers are included and add:

```python
app.include_router(course_sessions_router, prefix="/api/v1")
app.include_router(schedule_adjustments_router, prefix="/api/v1")
```

(Make sure these are added alongside existing routers like `checkin_router`, `schedules_router`, etc.)

- [ ] **Step 2: Verify backend starts**

Run:
```bash
cd /home/yufeng/student-manager/backend && conda run -n student-manage python -c "from app.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(api): register course_sessions and schedule_adjustments routers"
```

---

## Phase 4: Frontend Types and API Clients

### Task 4.1: Update frontend types

**Files:**
- Modify: `frontend-v3/src/types/api.ts`

- [ ] **Step 1: Add new types**

Add to `frontend-v3/src/types/api.ts` after existing `ClassSession` types:

```typescript
// 课程会话类型（新表 course_sessions）
export interface CourseSession {
  id: number
  session_code: string
  course_name?: string
  class_name: string
  classroom?: string
  teacher_id: number
  teacher_name?: string
  start_time: string
  end_time?: string
  status: 'active' | 'ended' | 'cancelled'
  week_number?: number
  schedule_id?: number
  source_type: 'scheduled' | 'manual' | 'makeup'
}

export interface StartCourseSessionRequest {
  class_name: string
  course_name?: string
  schedule_id?: number
}

// 课表调整记录
export interface ScheduleAdjustment {
  id: number
  schedule_id: number
  week_number: number
  type: 'cancel' | 'modify' | 'makeup'
  reason?: string
  new_date?: string
  new_start_time?: string
  new_end_time?: string
  new_classroom?: string
  generated_session_id?: number
  created_by: number
  created_at: string
}

export interface CreateScheduleAdjustmentRequest {
  schedule_id: number
  week_number: number
  type: 'cancel' | 'modify' | 'makeup'
  reason?: string
  new_date?: string
  new_start_time?: string
  new_end_time?: string
  new_classroom?: string
}

// 今日课表增强类型
export interface TodayScheduleItem {
  id: number
  course_name: string
  class_name: string
  teacher_id?: number
  teacher_name?: string
  day_of_week: number
  start_time: string
  end_time: string
  classroom?: string
  week_start: number
  week_end: number
  week_type: string
  // 新增增强字段
  week_number: number
  week_type_match: boolean
  session_status: 'none' | 'active' | 'ended' | 'cancelled' | 'adjusted' | 'makeup' | 'skipped'
  active_session_id?: number
  adjustment?: {
    type: string
    reason?: string
    new_date?: string
    new_start_time?: string
    new_end_time?: string
    new_classroom?: string
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/types/api.ts
git commit -m "feat(types): add CourseSession, ScheduleAdjustment and TodaySchedule types"
```

### Task 4.2: Create new API client files

**Files:**
- Create: `frontend-v3/src/api/courseSession.ts`
- Create: `frontend-v3/src/api/scheduleAdjustment.ts`
- Modify: `frontend-v3/src/api/index.ts`

- [ ] **Step 1: Write courseSession.ts**

Create `frontend-v3/src/api/courseSession.ts`:

```typescript
import { get, post } from '@/lib/api'
import type { CourseSession, StartCourseSessionRequest } from '@/types'

export interface ActiveClassSession {
  course_name?: string
  class_name: string
  teacher_id: number
  teacher_name: string
  start_time: string
}

export interface EndClassRequest {
  class_name?: string
}

export const courseSessionApi = {
  getCurrent: (): Promise<CourseSession[]> =>
    get('/course-sessions'),

  start: (data: StartCourseSessionRequest): Promise<CourseSession> =>
    post('/course-sessions/start', data),

  end: (sessionId: number): Promise<void> =>
    post(`/course-sessions/${sessionId}/end`, {}),

  getActiveSessions: (): Promise<ActiveClassSession[]> =>
    get('/class-sessions/active'),

  getForClass: (className: string): Promise<{ active: boolean; id?: number; session_code?: string; course_name?: string; class_name?: string; teacher_name?: string; start_time?: string }> =>
    get(`/class-sessions/class/${encodeURIComponent(className)}`),
}
```

- [ ] **Step 2: Write scheduleAdjustment.ts**

Create `frontend-v3/src/api/scheduleAdjustment.ts`:

```typescript
import { get, post } from '@/lib/api'
import type { ScheduleAdjustment, CreateScheduleAdjustmentRequest } from '@/types'

export const scheduleAdjustmentApi = {
  create: (data: CreateScheduleAdjustmentRequest): Promise<void> =>
    post('/schedule-adjustments', data),

  list: (params?: { schedule_id?: number; week_number?: number }): Promise<ScheduleAdjustment[]> => {
    const query = params
      ? '?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])).toString()
      : ''
    return get(`/schedule-adjustments${query}`)
  },
}
```

- [ ] **Step 3: Update api/index.ts**

Replace:
```typescript
export { classSessionApi } from './classSession'
```
with:
```typescript
export { courseSessionApi } from './courseSession'
export { scheduleAdjustmentApi } from './scheduleAdjustment'
// 保留废弃导出以兼容，后续逐步清理
export { classSessionApi } from './classSession'
```

- [ ] **Step 4: Commit**

```bash
git add frontend-v3/src/api/courseSession.ts frontend-v3/src/api/scheduleAdjustment.ts frontend-v3/src/api/index.ts
git commit -m "feat(api-clients): add courseSession and scheduleAdjustment APIs"
```

---

## Phase 5: Frontend Composables and Pages

### Task 5.1: Create useCourseSessions composable

**Files:**
- Create: `frontend-v3/src/composables/useCourseSessions.ts`
- Modify: `frontend-v3/src/composables/index.ts`

- [ ] **Step 1: Write useCourseSessions.ts**

Create `frontend-v3/src/composables/useCourseSessions.ts`:

```typescript
import { useQuery, useMutation, useQueryClient, type Query } from '@tanstack/vue-query'
import { unref, type Ref, computed } from 'vue'
import { courseSessionApi, checkinApi } from '@/api'
import type { CheckinRecord, CourseSession } from '@/types'

const isClient = (): boolean => typeof window !== 'undefined' && !!window.localStorage

const safeLocalStorage = {
  getItem(key: string): string | null {
    if (!isClient()) return null
    try { return localStorage.getItem(key) } catch { return null }
  },
  setItem(key: string, value: string): boolean {
    if (!isClient()) return false
    try { localStorage.setItem(key, value); return true } catch { return false }
  },
  removeItem(key: string): boolean {
    if (!isClient()) return false
    try { localStorage.removeItem(key); return true } catch { return false }
  }
}

export function useCourseSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['courseSessions'],
    queryFn: async () => {
      const sessions = await courseSessionApi.getCurrent()
      if (sessions && sessions.length > 0) {
        safeLocalStorage.setItem('activeCourseSessions', JSON.stringify(sessions))
        return sessions
      }
      safeLocalStorage.removeItem('activeCourseSessions')
      return []
    },
    refetchInterval: (query: Query<CourseSession[], Error, CourseSession[], string[]>) => {
      const data = query.state.data
      return data && data.length > 0 ? 5000 : 30000
    },
    staleTime: 3000,
    refetchOnWindowFocus: true,
    retry: 0,
  })
  return { data, isPending, error, refetch }
}

export function useCourseSessionByClassName(className: string | Ref<string>) {
  const { data: sessions, isPending, error, refetch } = useCourseSessions()
  const data = computed(() => {
    const resolved = unref(className)
    if (!sessions.value || !resolved) return null
    return sessions.value.find(s => s.class_name === resolved) || null
  })
  return { data, isPending, error, refetch }
}

export interface StartCourseSessionParams {
  className: string
  courseName?: string
  scheduleId?: number
}

export function useCourseSessionStart() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (params: StartCourseSessionParams) => {
      return await courseSessionApi.start({
        class_name: params.className,
        course_name: params.courseName,
        schedule_id: params.scheduleId,
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courseSessions'] })
      queryClient.invalidateQueries({ queryKey: ['active-class-sessions'] })
      queryClient.invalidateQueries({ queryKey: ['today-schedules'] })
    },
  })
  return { mutateAsync, isPending, error }
}

export function useCourseSessionEnd() {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (sessionId: number) => {
      await courseSessionApi.end(sessionId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['courseSessions'] })
      queryClient.invalidateQueries({ queryKey: ['students'] })
      queryClient.invalidateQueries({ queryKey: ['today-checkins'] })
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['active-class-sessions'] })
    },
  })
  return { mutateAsync, isPending, error }
}

export function useActiveClassSessions() {
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ['active-class-sessions'],
    queryFn: async () => {
      return await checkinApi.getActiveSessions()
    },
    refetchInterval: 10000,
  })
  return { data, isPending, error, refetch }
}

export function useStudentCheckIn(className?: string | Ref<string>) {
  const queryClient = useQueryClient()
  const { mutateAsync, isPending, error } = useMutation({
    mutationFn: async (studentCode: string): Promise<CheckinRecord> => {
      return await checkinApi.checkin({
        student_id: studentCode,
        student_name: '',
      })
    },
    onSuccess: () => {
      const resolved = unref(className)
      queryClient.invalidateQueries({ queryKey: ['checkin-stats'] })
      queryClient.invalidateQueries({ queryKey: ['today-checkins', resolved || 'all'] })
    },
  })
  return { mutateAsync, isPending, error }
}
```

- [ ] **Step 2: Update composables/index.ts**

Export the new composable:

```typescript
export * from './useCourseSessions'
```

Keep `useClassSession` for backward compatibility until fully migrated.

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/composables/useCourseSessions.ts frontend-v3/src/composables/index.ts
git commit -m "feat(composables): add useCourseSessions with CourseSession integration"
```

### Task 5.2: Update Router for SessionsHistory

**Files:**
- Modify: `frontend-v3/src/router/index.ts`

- [ ] **Step 1: Add route**

Add to `/teacher` children in `frontend-v3/src/router/index.ts`:

```typescript
{
  path: 'sessions-history',
  name: 'TeacherSessionsHistory',
  component: () => import('@/views/teacher/SessionsHistory.vue'),
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/router/index.ts
git commit -m "feat(router): add TeacherSessionsHistory route"
```

### Task 5.3: Update Teacher Dashboard

**Files:**
- Modify: `frontend-v3/src/views/teacher/Dashboard.vue`
- Modify: `frontend-v3/src/composables/useSchedules.ts`

- [ ] **Step 1: Update useSchedules.ts to return TodayScheduleItem**

Modify `frontend-v3/src/composables/useSchedules.ts` (check actual return type) to return `TodayScheduleItem[]` from `useTodaySchedules`.

- [ ] **Step 2: Rewrite Dashboard.vue today-schedule cards**

Replace the `todaySchedules` list rendering with new status-aware cards. Key changes:

```vue
<script setup lang="ts">
// Add new imports
import { useCourseSessionStart, useCourseSessions, useTodayCheckins } from '@/composables'
import type { TodayScheduleItem } from '@/types'

const { mutateAsync: startSession } = useCourseSessionStart()
const { refetch: refetchSessions } = useCourseSessions()
const { error: showErrorToast, success: showSuccessToast } = useToast()

async function handleStartFromSchedule(schedule: TodayScheduleItem) {
  try {
    await startSession({
      className: schedule.class_name,
      courseName: schedule.course_name,
      scheduleId: schedule.id,
    })
    showSuccessToast('课堂已开始')
    refetchSessions()
  } catch (err: any) {
    showErrorToast(err?.message || '开始课堂失败')
  }
}

function getScheduleStatusLabel(schedule: TodayScheduleItem) {
  switch (schedule.session_status) {
    case 'active': return '签到中'
    case 'ended': return '已结束'
    case 'cancelled': return '已停课'
    case 'adjusted': return '已调课'
    case 'makeup': return '补课'
    case 'skipped': return '本周不上'
    default: return '未开始'
  }
}

function canStartClass(schedule: TodayScheduleItem) {
  if (schedule.session_status === 'active') return false
  if (schedule.session_status === 'ended') return false
  if (schedule.session_status === 'cancelled') return false
  if (schedule.session_status === 'skipped') return false
  // Only allow within 15 min window; simplified check
  return true
}
</script>
```

Update the template list item to conditionally show different buttons based on `session_status`.

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/views/teacher/Dashboard.vue frontend-v3/src/composables/useSchedules.ts
git commit -m "feat(teacher): enhance Dashboard today schedule with status-aware actions"
```

### Task 5.4: Update ClassSession page

**Files:**
- Modify: `frontend-v3/src/views/teacher/ClassSession.vue`

- [ ] **Step 1: Replace useClassSessions with useCourseSessions**

Change imports from `useClassSessions` to `useCourseSessions`, `useCourseSessionStart`, `useCourseSessionEnd`.

- [ ] **Step 2: Add quick-start schedule cards**

Add a computed `todaySchedulesWithoutSession` that filters `todaySchedules` for ones not yet started.
Render these as quick-start cards above the manual form.

- [ ] **Step 3: Update end session to use session_id**

Change `handleEndSession` and `confirmEndSession` to pass the `selectedSession.value.id` to `endCourseSession` instead of `class_name`.

- [ ] **Step 4: Display source_type badge**

In the active session info card, add a badge showing:
- `source_type === 'scheduled'` → "按课表 · 第X周"
- `source_type === 'manual'` → "手动开启"
- `source_type === 'makeup'` → "补课 · 第X周"

- [ ] **Step 5: Commit**

```bash
git add frontend-v3/src/views/teacher/ClassSession.vue
git commit -m "feat(teacher): ClassSession supports quick-start from schedule and source badges"
```

### Task 5.5: Create ScheduleAdjustmentDialog and integrate into Schedules.vue

**Files:**
- Create: `frontend-v3/src/components/teacher/ScheduleAdjustmentDialog.vue`
- Modify: `frontend-v3/src/views/teacher/Schedules.vue`

- [ ] **Step 1: Write ScheduleAdjustmentDialog.vue**

Create the dialog with three tabs/modes: 停课、调课、补课.
Use existing `Dialog`, `Button`, `Input` components from `@/components/ui`.
Include `class_name`, `course_name`, `week_number` display for context.

- [ ] **Step 2: Add adjustment button per schedule card in Schedules.vue**

Add a small settings/adjustment icon button on each schedule timeline card.
Click opens the dialog.

- [ ] **Step 3: Commit**

```bash
git add frontend-v3/src/components/teacher/ScheduleAdjustmentDialog.vue frontend-v3/src/views/teacher/Schedules.vue
git commit -m "feat(teacher): add schedule adjustment dialog to Schedules page"
```

### Task 5.6: Create SessionsHistory page

**Files:**
- Create: `frontend-v3/src/views/teacher/SessionsHistory.vue`

- [ ] **Step 1: Write basic page**

A table/list showing:
- 课程名、班级、教室
- 第X周、上课时间
- 签到率进度条
- 状态标签
- 「查看详情」按钮（可展开显示已签到/未签到学生名单）

Use `useCourseSessions` for active sessions, and add a new API `GET /course-sessions?status=ended` for historical ones.

- [ ] **Step 2: Commit**

```bash
git add frontend-v3/src/views/teacher/SessionsHistory.vue
git commit -m "feat(teacher): add SessionsHistory page"
```

---

## Phase 6: Data Migration

### Task 6.1: Write database migration script

**Files:**
- Create: `migrations/versions/2026_04_06_course_session_migration.py` (or use Alembic)

- [ ] **Step 1: Create migration script**

Write a script that:
1. Creates `course_sessions` and `schedule_adjustments`
2. Migrates `class_session` → `course_sessions`
3. Remaps `checkin_records.session_id`
4. Adds `week_type` to `course_schedules`

- [ ] **Step 2: Test migration in dev environment**

Run:
```bash
cd /home/yufeng/student-manager/backend && conda run -n student-manage python -m alembic upgrade head
# or python migrations/versions/2026_04_06_course_session_migration.py
```

Verify:
```bash
sqlite3 data/class_system.db ".tables"
```

Ensure `course_sessions` and `schedule_adjustments` exist.

- [ ] **Step 3: Commit**

```bash
git add migrations/versions/2026_04_06_course_session_migration.py
git commit -m "chore(db): add CourseSession migration script"
```

---

## Phase 7: Tests

### Task 7.1: Backend unit tests for CourseSession CRUD

**Files:**
- Create: `tests/unit/crud/test_course_session.py`

- [ ] **Step 1: Write tests**

Test `start_course_session`, `end_course_session`, `get_active_course_session_by_class_name`, `get_teacher_active_course_sessions`.

- [ ] **Step 2: Run and commit**

```bash
cd /home/yufeng/student-manager && conda run -n student-manage pytest tests/unit/crud/test_course_session.py -v
```

Expected: PASS

```bash
git add tests/unit/crud/test_course_session.py
git commit -m "test(crud): add CourseSession unit tests"
```

### Task 7.2: Backend integration tests for CourseSession API

**Files:**
- Create: `tests/integration/test_course_session_api.py`
- Modify: `tests/integration/test_checkin_api_enhanced.py`

- [ ] **Step 1: Write new integration tests**

Cover:
- `POST /course-sessions/start` with and without `schedule_id`
- `POST /course-sessions/{id}/end`
- Multi-session support via new API
- Student checkin via updated `/checkin`

- [ ] **Step 2: Update existing test_checkin_api_enhanced.py**

Replace `/class-session` paths with `/course-sessions` and adjust assertions.

- [ ] **Step 3: Run tests**

```bash
cd /home/yufeng/student-manager && conda run -n student-manage pytest tests/integration/test_course_session_api.py tests/integration/test_checkin_api_enhanced.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_course_session_api.py tests/integration/test_checkin_api_enhanced.py
git commit -m "test(api): add CourseSession integration tests and migrate checkin tests"
```

### Task 7.3: Frontend tests

**Files:**
- Create/update relevant `frontend-v3/test/` files

- [ ] **Step 1: Run existing frontend tests**

```bash
cd /home/yufeng/student-manager/frontend-v3 && pnpm test:run
```

Fix any TypeScript errors caused by type renames.

- [ ] **Step 2: Commit fixes**

```bash
git commit -m "test(frontend): fix types after CourseSession migration"
```

---

## Spec Coverage Checklist

| 需求 | 对应任务 |
|------|----------|
| 新建 CourseSession 模型 | Task 1.1, 1.2 |
| 新建 ScheduleAdjustment 模型 | Task 1.1 |
| CourseSchedule 增加 week_type | Task 1.3 |
| 软引导开课（支持 schedule_id） | Task 3.1, 5.3, 5.4 |
| 调课/停课/补课 API | Task 2.2, 3.2 |
| Dashboard 今日课表状态 | Task 3.4, 5.3 |
| ClassSession 快捷开课 | Task 5.4 |
| 历史课堂页面 | Task 5.6 |
| 数据迁移 | Task 6.1 |
| 测试覆盖 | Task 7.1-7.3 |

---

## Execution Choice

Plan complete and saved to `docs/superpowers/plans/2026-04-06-course-schedule-closed-loop.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints for review

**Which approach do you prefer?**
