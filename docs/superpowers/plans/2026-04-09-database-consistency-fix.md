# 数据库一致性修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 ClassHub 班级管理系统的 9 个数据一致性问题，确保排班、调课、课堂、签到等业务流程的数据完整性。

**Architecture:** 使用数据库级联约束保证数据完整性，添加缺失的唯一约束，修复业务逻辑中的数据同步问题，确保读写操作的一致性。

**Tech Stack:** Python 3.11, FastAPI, SQLModel, SQLite, pytest

---

## 前置准备

### 环境检查
- [ ] 确认 Conda 环境 `student-manage` 已激活
- [ ] 确认数据库路径正确
- [ ] 备份现有数据库（如生产环境）

---

## 文件结构

### 修改的文件
| 文件 | 责任 |
|------|------|
| `backend/app/models/course_session.py` | 添加 ScheduleAdjustment 唯一约束 |
| `backend/app/api/routes/schedules.py` | 修复教师分配级联更新 |
| `backend/app/api/routes/course_sessions.py` | 修复调课信息读取 |
| `backend/app/api/routes/schedule_adjustments.py` | 修复补课/取消调课逻辑 |
| `backend/app/api/routes/checkin.py` | 修复签到班级快照 |
| `backend/app/crud/schedule.py` | 添加级联删除逻辑 |
| `migrations/versions/2026_04_09_add_checkin_unique_constraints.py` | 数据库迁移（已存在） |

### 新建的文件
| 文件 | 责任 |
|------|------|
| `migrations/versions/2026_04_09_add_schedule_adjustment_constraints.py` | ScheduleAdjustment 唯一约束迁移 |
| `tests/integration/test_schedule_consistency.py` | 调课一致性集成测试 |
| `tests/integration/test_teacher_assignment_cascade.py` | 教师分配级联更新测试 |

---

## Task 1: 添加 ScheduleAdjustment 唯一约束

**问题:** 同一课表和周次可创建多个调整记录

**Files:**
- Modify: `backend/app/models/course_session.py:67-72`
- Create: `migrations/versions/2026_04_09_add_schedule_adjustment_constraints.py`

### Step 1.1: 修改模型添加唯一约束

```python
# backend/app/models/course_session.py
from sqlalchemy import UniqueConstraint

class ScheduleAdjustment(ScheduleAdjustmentBase, table=True):
    """课表调整记录数据库模型"""
    __tablename__ = "schedule_adjustments"
    __table_args__ = (
        # 同一课表同一周次只能有一条调整记录
        UniqueConstraint('schedule_id', 'week_number', name='uix_schedule_week'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now, description="创建时间")
```

### Step 1.2: 创建数据库迁移

```python
# migrations/versions/2026_04_09_add_schedule_adjustment_constraints.py
"""添加 ScheduleAdjustment 唯一约束

Revision ID: 2026_04_09_add_schedule_adjustment_constraints
Revises: 2026_04_09_add_checkin_unique_constraints
Create Date: 2026-04-09 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '2026_04_09_add_schedule_adjustment_constraints'
down_revision: Union[str, None] = '2026_04_09_add_checkin_unique_constraints'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建唯一约束
    op.create_unique_constraint(
        'uix_schedule_week',
        'schedule_adjustments',
        ['schedule_id', 'week_number']
    )


def downgrade() -> None:
    op.drop_constraint('uix_schedule_week', 'schedule_adjustments', type_='unique')
```

### Step 1.3: 运行迁移

```bash
cd backend && conda run -n student-manage alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade ...`

### Step 1.4: 提交

```bash
git add backend/app/models/course_session.py migrations/versions/
git commit -m "feat: add unique constraint to schedule_adjustments (schedule_id, week_number)"
```

---

## Task 2: 修复教师分配级联更新

**问题:** 调课后已创建的 CourseSession 不更新 teacher_id

**Files:**
- Modify: `backend/app/api/routes/schedules.py:329-382`
- Create: `tests/integration/test_teacher_assignment_cascade.py`

### Step 2.1: 编写失败测试

```python
# tests/integration/test_teacher_assignment_cascade.py
"""
教师分配级联更新测试
验证调课后 CourseSession.teacher_id 同步更新
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.db import get_session
from app.models import CourseSchedule, CourseSession, User

client = TestClient(app)


def get_auth_headers(username: str = "admin"):
    """获取认证头"""
    response = client.post("/api/v1/login", json={
        "username": username,
        "password": "password"  # 测试环境密码
    })
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestTeacherAssignmentCascade:
    """测试教师分配级联更新"""

    def test_assign_teacher_updates_existing_session(self):
        """测试分配教师后已创建的课堂 teacher_id 同步更新"""
        headers = get_auth_headers("admin")

        # 1. 创建课表（无教师）
        schedule_data = {
            "course_name": "测试课程",
            "class_name": "测试班级",
            "teacher_name": "",
            "day_of_week": 1,
            "start_time": "08:00",
            "end_time": "09:40",
            "classroom": "A101"
        }
        resp = client.post("/api/v1/schedules/import", json=[schedule_data], headers=headers)
        assert resp.status_code == 200

        # 获取创建的 schedule_id
        resp = client.get("/api/v1/schedules?class_name=测试班级", headers=headers)
        schedule_id = resp.json()["data"][0]["id"]

        # 2. 教师开始上课（创建 CourseSession）
        teacher_headers = get_auth_headers("teacher1")
        resp = client.post("/api/v1/course-sessions/start", json={
            "class_name": "测试班级",
            "course_name": "测试课程",
            "schedule_id": schedule_id
        }, headers=teacher_headers)
        assert resp.status_code == 200
        session_id = resp.json()["data"]["id"]

        # 验证初始教师
        resp = client.get("/api/v1/course-sessions", headers=teacher_headers)
        sessions = resp.json()["data"]
        assert len(sessions) == 1
        assert sessions[0]["id"] == session_id

        # 3. 管理员重新分配教师
        resp = client.put(f"/api/v1/schedules/{schedule_id}/assign", params={
            "teacher_id": 999,
            "teacher_name": "新教师"
        }, headers=headers)
        assert resp.status_code == 200

        # 4. 验证 CourseSession 已更新（原教师看不到课堂）
        resp = client.get("/api/v1/course-sessions", headers=teacher_headers)
        sessions = resp.json()["data"]
        assert len(sessions) == 0  # ❌ 原教师仍能看到，测试失败

        # 5. 验证新教师能看到
        new_teacher_headers = get_auth_headers("teacher2")
        resp = client.get("/api/v1/course-sessions", headers=new_teacher_headers)
        sessions = resp.json()["data"]
        assert len(sessions) == 1
        assert sessions[0]["id"] == session_id
```

### Step 2.2: 运行测试确认失败

```bash
cd backend && conda run -n student-manage pytest tests/integration/test_teacher_assignment_cascade.py -v
```

Expected: `FAILED tests/integration/test_teacher_assignment_cascade.py::TestTeacherAssignmentCascade::test_assign_teacher_updates_existing_session`

### Step 2.3: 实现级联更新

```python
# backend/app/api/routes/schedules.py
from sqlalchemy import update
from app.models import CourseSession

@router.put("/schedules/{schedule_id}/assign", response_model=ApiSuccessResponse)
async def assign_teacher_to_schedule(
    schedule_id: int,
    teacher_id: int,
    teacher_name: str,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """为课程分配教师（仅管理员）- 修复级联更新"""
    # 查询课程
    schedule = session.get(CourseSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="课程不存在"
        )

    # 更新教师信息
    schedule.teacher_id = teacher_id
    schedule.teacher_name = teacher_name
    session.add(schedule)

    # 修复：级联更新活跃的 CourseSession
    session.execute(
        update(CourseSession)
        .where(
            CourseSession.schedule_id == schedule_id,
            CourseSession.status == "active"
        )
        .values(teacher_id=teacher_id, teacher_name=teacher_name)
    )

    session.commit()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已将课程 '{schedule.course_name}' 分配给教师 '{teacher_name}'"
    }
```

### Step 2.4: 同样修复 unassign

```python
@router.put("/schedules/{schedule_id}/unassign", response_model=ApiSuccessResponse)
async def unassign_teacher_from_schedule(
    schedule_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(require_admin)
):
    """取消课程的教师分配（仅管理员）- 修复级联更新"""
    # 查询课程
    schedule = session.get(CourseSchedule, schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=HttpStatus.NOT_FOUND,
            detail="课程不存在"
        )

    # 清除教师信息
    schedule.teacher_id = None
    schedule.teacher_name = None
    session.add(schedule)

    # 修复：级联清除 CourseSession 的教师信息
    session.execute(
        update(CourseSession)
        .where(
            CourseSession.schedule_id == schedule_id,
            CourseSession.status == "active"
        )
        .values(teacher_id=None, teacher_name=None)
    )

    session.commit()

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: f"已取消课程 '{schedule.course_name}' 的教师分配"
    }
```

### Step 2.5: 运行测试确认通过

```bash
cd backend && conda run -n student-manage pytest tests/integration/test_teacher_assignment_cascade.py -v
```

Expected: `PASSED tests/integration/test_teacher_assignment_cascade.py::TestTeacherAssignmentCascade::test_assign_teacher_updates_existing_session`

### Step 2.6: 提交

```bash
git add backend/app/api/routes/schedules.py tests/integration/test_teacher_assignment_cascade.py
git commit -m "fix: cascade update CourseSession.teacher_id when reassigning teacher"
```

---

## Task 3: 修复 modify 类型调课生效

**问题:** modify 类型调课的时间/教室信息未被 course-sessions/start 使用

**Files:**
- Modify: `backend/app/api/routes/course_sessions.py:89-172`
- Modify: `tests/integration/test_schedule_consistency.py`

### Step 3.1: 编写失败测试

```python
# tests/integration/test_schedule_consistency.py
def test_modify_adjustment_applies_to_new_session(self):
    """测试 modify 调课后新课堂使用调整后的时间/教室"""
    admin_headers = get_auth_headers("admin")
    teacher_headers = get_auth_headers("teacher1")

    # 1. 创建课表
    schedule_data = {
        "course_name": "测试课程",
        "class_name": "测试班级",
        "teacher_name": "张老师",
        "day_of_week": 1,
        "start_time": "08:00",
        "end_time": "09:40",
        "classroom": "A101"
    }
    resp = client.post("/api/v1/schedules/import", json=[schedule_data], headers=admin_headers)
    schedule_id = resp.json()["data"][0]["id"]

    # 2. 创建 modify 类型调课
    resp = client.post("/api/v1/schedule-adjustments", json={
        "schedule_id": schedule_id,
        "week_number": 10,  # 假设当前是第10周
        "type": "modify",
        "reason": "教室变更",
        "new_classroom": "B202",
        "new_start_time": "14:00",
        "new_end_time": "15:40"
    }, headers=admin_headers)
    assert resp.status_code == 200

    # 3. 教师开始上课
    resp = client.post("/api/v1/course-sessions/start", json={
        "class_name": "测试班级",
        "course_name": "测试课程",
        "schedule_id": schedule_id
    }, headers=teacher_headers)
    assert resp.status_code == 200

    # 4. 验证课堂使用调整后的信息
    session_id = resp.json()["data"]["id"]

    # 获取课堂详情（需要新增 API 或使用现有 API）
    resp = client.get(f"/api/v1/course-sessions/{session_id}", headers=teacher_headers)
    # 或从列表查询
    resp = client.get("/api/v1/course-sessions", headers=teacher_headers)
    session_data = resp.json()["data"][0]

    # 验证使用调课后的教室和时间
    assert session_data["classroom"] == "B202", f"期望 B202，实际 {session_data.get('classroom')}"
    # ❌ 当前代码使用原始值 A101，测试失败
```

### Step 3.2: 运行测试确认失败

```bash
cd backend && conda run -n student-manage pytest tests/integration/test_schedule_consistency.py::TestScheduleConsistency::test_modify_adjustment_applies_to_new_session -v
```

Expected: `FAILED` - classroom 不等于 "B202"

### Step 3.3: 修改 course-sessions/start 读取调课信息

```python
# backend/app/api/routes/course_sessions.py
@router.post("/course-sessions/start", response_model=CourseSessionResponse)
def begin_course_session(
    request: Request,
    data: StartCourseSessionRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """开始上课 - 修复：读取调课信息"""
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
    start_time = None
    end_time = None

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
        start_time = None  # 后续从 schedule 计算或留空
        end_time = None
        source_type = "scheduled"
        if not data.course_name:
            data.course_name = schedule.course_name

        # 修复：检查是否有 modify 类型的调课
        from app.crud.schedule_adjustment import get_adjustment
        adjustment = get_adjustment(session, schedule_id, week_number)
        if adjustment:
            if adjustment.type == "modify":
                # 使用调课后的信息
                classroom = adjustment.new_classroom or classroom
                # 时间字段需要解析并设置到 datetime 对象
                if adjustment.new_start_time:
                    from datetime import datetime
                    from zoneinfo import ZoneInfo
                    today = datetime.now(ZoneInfo("Asia/Shanghai"))
                    time_parts = adjustment.new_start_time.split(":")
                    start_time = today.replace(hour=int(time_parts[0]), minute=int(time_parts[1]))
                if adjustment.new_end_time:
                    time_parts = adjustment.new_end_time.split(":")
                    end_time = today.replace(hour=int(time_parts[0]), minute=int(time_parts[1]))
            elif adjustment.type == "cancel":
                raise HTTPException(
                    status_code=HttpStatus.BAD_REQUEST,
                    detail="该周课程已取消，无法开始上课"
                )

    try:
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
        # 如果调课指定了时间，覆盖自动生成的 start_time
        if start_time:
            course_session.start_time = start_time
        if end_time:
            course_session.end_time = end_time
        session.add(course_session)
        session.commit()
        session.refresh(course_session)
    except IntegrityError as e:
        # ... 原有错误处理不变
        session.rollback()
        error_msg = str(e).lower()
        if "unique" in error_msg or "uix_active_class_name" in error_msg:
            existing = get_active_course_session_by_class_name(session, data.class_name)
            if existing:
                teacher_name = existing.teacher_name or "其他教师"
                raise HTTPException(
                    status_code=HttpStatus.CONFLICT,
                    detail=f"该班级正在被 {teacher_name} 老师上课，无法开始新课堂"
                )
        raise HTTPException(
            status_code=HttpStatus.CONFLICT,
            detail="该班级已开始上课，请勿重复操作"
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
            "end_time": course_session.end_time,
            "status": course_session.status,
            "session_code": course_session.session_code,
            "schedule_id": course_session.schedule_id,
            "week_number": course_session.week_number,
            "source_type": course_session.source_type,
            "classroom": course_session.classroom,
        }
    }
```

### Step 3.4: 运行测试确认通过

```bash
cd backend && conda run -n student-manage pytest tests/integration/test_schedule_consistency.py::TestScheduleConsistency::test_modify_adjustment_applies_to_new_session -v
```

Expected: `PASSED`

### Step 3.5: 提交

```bash
git add backend/app/api/routes/course_sessions.py tests/integration/test_schedule_consistency.py
git commit -m "fix: apply modify adjustment when starting course session"
```

---

## Task 4: 修复补课调课逻辑（新增 scheduled 状态）

**问题:** makeup 类型调课立即创建活跃课堂，导致课堂过早显示（C-02）

**方案:** 新增 `scheduled` 状态，makeup 调课创建 `scheduled` 状态的课堂，到补课时间自动转为 `active`

**Files:**
- Modify: `backend/app/models/course_session.py:27`
- Modify: `backend/app/api/routes/schedule_adjustments.py:37-98`
- Modify: `backend/app/crud/course_session.py:48-77`
- Create: `backend/app/core/scheduler.py`（定时任务检查并激活 scheduled 课堂）

### Step 4.1: 修改 CourseSession 模型支持 scheduled 状态

```python
# backend/app/models/course_session.py:27
class CourseSessionBase(SQLModel):
    """课程会话基础模型"""
    # ... 其他字段 ...
    status: str = Field(default="active", description="课堂状态: scheduled|active|ended|cancelled", max_length=20)
    # scheduled: 已安排未开始（用于 makeup 调课）
    # active: 进行中
    # ended: 已结束
    # cancelled: 已取消
    source_type: str = Field(default="manual", description="来源类型: scheduled|manual|makeup", max_length=20)
```

### Step 4.2: 修改 makeup 调课创建 scheduled 状态课堂

```python
# backend/app/api/routes/schedule_adjustments.py
@router.post("/schedule-adjustments", response_model=ApiSuccessResponse)
def create_schedule_adjustment(
    data: CreateAdjustmentRequest,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    """创建课表调整记录 - 修复：makeup 创建 scheduled 状态课堂"""
    role = user.get("role", "")
    if role not in ("teacher", "admin"):
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权调整此课程")

    user_id = int(user.get("sub", 0))

    schedule = session.get(CourseSchedule, data.schedule_id)
    if not schedule:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail="课表不存在")
    if role == "teacher" and schedule.teacher_id != user_id:
        raise HTTPException(status_code=HttpStatus.FORBIDDEN, detail="无权调整此课程")

    if data.type == "cancel":
        # 修复：自动处理已存在的活跃课堂（H-02）
        from app.crud.course_session import get_course_sessions_by_schedule_and_week
        existing_session = get_course_sessions_by_schedule_and_week(
            session, data.schedule_id, data.week_number
        )
        if existing_session:
            if existing_session.status == "active":
                # 自动结束活跃课堂
                existing_session.status = "ended"
                from app.core.timezone import get_now
                existing_session.end_time = get_now()
                session.add(existing_session)
            elif existing_session.status == "ended":
                raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已结束的课程不能停课")

    if data.type == "modify":
        if has_ended_session(session, data.schedule_id, data.week_number):
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="已结束的课程不能调课")

    generated_session_id = None
    if data.type == "makeup":
        if not data.new_date:
            raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail="补课必须指定日期")
        
        # 修复：创建 scheduled 状态的课堂（而非 active）
        from datetime import datetime
        from zoneinfo import ZoneInfo
        
        # 构建补课开始时间
        makeup_start_time = None
        if data.new_start_time:
            time_parts = data.new_start_time.split(":")
            makeup_start_time = datetime.combine(
                data.new_date,
                datetime.strptime(data.new_start_time, "%H:%M").time(),
                tzinfo=ZoneInfo("Asia/Shanghai")
            )
        else:
            # 使用默认时间（如 08:00）
            makeup_start_time = datetime.combine(
                data.new_date,
                datetime.strptime("08:00", "%H:%M").time(),
                tzinfo=ZoneInfo("Asia/Shanghai")
            )
        
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
        # 设置为 scheduled 状态，并记录计划开始时间
        course_session.status = "scheduled"
        course_session.start_time = makeup_start_time  # 用 start_time 存储计划开始时间
        session.add(course_session)
        session.commit()
        session.refresh(course_session)
        generated_session_id = course_session.id

    try:
        if data.type != "makeup":
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
            session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=HttpStatus.CONFLICT,
            detail="该周已有调课记录，请勿重复创建"
        )

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: "调整记录已创建"
    }
```

### Step 4.3: 创建定时任务激活 scheduled 课堂

```python
# backend/app/core/scheduler.py
"""
课堂调度器 - 自动激活 scheduled 状态的课堂
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from app.core.db import engine
from app.models import CourseSession


def activate_scheduled_sessions():
    """激活已到时间的 scheduled 课堂"""
    with Session(engine) as session:
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        
        # 查询所有已到开始时间的 scheduled 课堂
        statement = select(CourseSession).where(
            CourseSession.status == "scheduled",
            CourseSession.start_time <= now
        )
        scheduled_sessions = session.exec(statement).all()
        
        for cs in scheduled_sessions:
            cs.status = "active"
            session.add(cs)
        
        if scheduled_sessions:
            session.commit()
            print(f"Activated {len(scheduled_sessions)} scheduled sessions")
        
        return len(scheduled_sessions)


def setup_scheduler():
    """设置定时任务（在应用启动时调用）"""
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    # 每分钟检查一次
    scheduler.add_job(activate_scheduled_sessions, 'interval', minutes=1)
    scheduler.start()
    return scheduler
```

### Step 4.4: 修改查询排除 scheduled 课堂

```python
# backend/app/crud/course_session.py:28-34
def get_teacher_active_course_sessions(session: Session, teacher_id: int) -> List[CourseSession]:
    """获取教师所有活跃课程会话（不包含 scheduled）"""
    query = select(CourseSession).where(
        CourseSession.teacher_id == teacher_id,
        CourseSession.status == "active"  # 只返回 active，不包含 scheduled
    )
    return list(session.exec(query).all())


# 新增：获取教师的 scheduled 课堂
def get_teacher_scheduled_course_sessions(session: Session, teacher_id: int) -> List[CourseSession]:
    """获取教师所有已安排但未开始的课程"""
    query = select(CourseSession).where(
        CourseSession.teacher_id == teacher_id,
        CourseSession.status == "scheduled"
    )
    return list(session.exec(query).all())
```

### Step 4.5: 更新测试

```python
# tests/integration/test_schedule_consistency.py
def test_makeup_creates_scheduled_not_active_session(self):
    """测试 makeup 调课创建 scheduled 状态而非 active"""
    admin_headers = get_auth_headers("admin")
    teacher_headers = get_auth_headers("teacher1")

    # 1. 创建课表
    schedule_data = {
        "course_name": "测试课程",
        "class_name": "测试班级",
        "teacher_name": "张老师",
        "day_of_week": 1,
        "start_time": "08:00",
        "end_time": "09:40",
        "classroom": "A101"
    }
    resp = client.post("/api/v1/schedules/import", json=[schedule_data], headers=admin_headers)
    schedule_id = resp.json()["data"][0]["id"]

    # 2. 创建 makeup 调课（明天）
    from datetime import date, timedelta, datetime
    makeup_date = date.today() + timedelta(days=1)
    makeup_time = "14:00"
    resp = client.post("/api/v1/schedule-adjustments", json={
        "schedule_id": schedule_id,
        "week_number": 10,
        "type": "makeup",
        "reason": "补课",
        "new_date": makeup_date.isoformat(),
        "new_start_time": makeup_time,
        "new_classroom": "B202"
    }, headers=admin_headers)
    assert resp.status_code == 200

    # 3. 验证教师活跃列表中没有该课堂
    resp = client.get("/api/v1/course-sessions", headers=teacher_headers)
    sessions = resp.json()["data"]
    active_makeup = [s for s in sessions if s.get("source_type") == "makeup"]
    assert len(active_makeup) == 0, "makeup 课堂不应立即显示在活跃列表"

def test_scheduled_session_activates_at_start_time(self):
    """测试 scheduled 课堂在到达开始时间后自动激活"""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    
    # 创建 scheduled 课堂（开始时间为现在）
    with Session(engine) as session:
        cs = CourseSession(
            class_name="测试班级",
            teacher_id=1,
            course_name="测试课程",
            status="scheduled",
            start_time=datetime.now(ZoneInfo("Asia/Shanghai")),  # 现在就开始
            source_type="makeup"
        )
        session.add(cs)
        session.commit()
        session_id = cs.id
    
    # 执行调度任务
    from app.core.scheduler import activate_scheduled_sessions
    activated = activate_scheduled_sessions()
    assert activated >= 1
    
    # 验证状态已变为 active
    with Session(engine) as session:
        cs = session.get(CourseSession, session_id)
        assert cs.status == "active"
```

### Step 4.6: 运行测试

```bash
cd backend && conda run -n student-manage pytest tests/integration/test_schedule_consistency.py::TestScheduleConsistency::test_makeup_creates_scheduled_not_active_session -v
cd backend && conda run -n student-manage pytest tests/integration/test_schedule_consistency.py::TestScheduleConsistency::test_scheduled_session_activates_at_start_time -v
```

### Step 4.7: 提交

```bash
git add backend/app/models/course_session.py backend/app/api/routes/schedule_adjustments.py backend/app/crud/course_session.py backend/app/core/scheduler.py tests/integration/test_schedule_consistency.py
git commit -m "feat: add scheduled status for makeup sessions, auto-activate at start time"
```

---

## Task 4.5: 新增并发竞态条件处理测试（C-03, C-04）

**问题:** 并发开始课堂、并发签到存在竞态条件

**Files:**
- Create: `tests/integration/test_concurrent_race_conditions.py`

### Step 4.5.1: 编写并发开始课堂测试

```python
# tests/integration/test_concurrent_race_conditions.py
"""
并发竞态条件测试
验证系统在并发场景下的数据一致性
"""
import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi.testclient import TestClient
from app.main import app
from app.core.db import get_session
from app.models import CourseSession, CourseSchedule

client = TestClient(app)


class TestConcurrentRaceConditions:
    """测试并发竞态条件"""

    def test_concurrent_start_course_session(self):
        """测试并发开始课堂 - 只有一个能成功（C-03）"""
        admin_headers = get_auth_headers("admin")
        
        # 创建课表
        schedule_data = {
            "course_name": "并发测试课程",
            "class_name": "并发测试班级",
            "teacher_name": "张老师",
            "day_of_week": 1,
            "start_time": "08:00",
            "end_time": "09:40",
            "classroom": "A101"
        }
        resp = client.post("/api/v1/schedules/import", json=[schedule_data], headers=admin_headers)
        schedule_id = resp.json()["data"][0]["id"]
        
        results = {"success": 0, "conflict": 0, "error": 0}
        
        def try_start_session(teacher_id):
            headers = get_auth_headers(f"teacher{teacher_id}")
            try:
                resp = client.post("/api/v1/course-sessions/start", json={
                    "class_name": "并发测试班级",
                    "course_name": "并发测试课程",
                    "schedule_id": schedule_id
                }, headers=headers)
                if resp.status_code == 200:
                    return "success"
                elif resp.status_code == 409:
                    return "conflict"
                else:
                    return "error"
            except Exception:
                return "error"
        
        # 5个教师同时尝试开始同一课堂
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(try_start_session, i) for i in range(1, 6)]
            for future in as_completed(futures):
                result = future.result()
                results[result] += 1
        
        # 只有一个能成功
        assert results["success"] == 1, f"期望1个成功，实际{results['success']}个"
        assert results["conflict"] == 4, f"期望4个冲突，实际{results['conflict']}个"
    
    def test_concurrent_checkin(self):
        """测试并发签到 - 只有一个能成功（C-04）"""
        teacher_headers = get_auth_headers("teacher1")
        
        # 创建活跃课堂
        resp = client.post("/api/v1/course-sessions/start", json={
            "class_name": "签到测试班级",
            "course_name": "签到测试课程"
        }, headers=teacher_headers)
        session_id = resp.json()["data"]["id"]
        
        results = {"success": 0, "conflict": 0, "error": 0}
        
        def try_checkin(thread_id):
            try:
                resp = client.post("/api/v1/checkin", json={
                    "student_id": "2024001",  # 同一学生
                    "student_name": "测试学生",
                    "device_id": f"device_{thread_id}"
                })
                if resp.status_code == 200:
                    return "success"
                elif resp.status_code == 409:
                    return "conflict"
                else:
                    return "error"
            except Exception:
                return "error"
        
        # 5个请求同时签到
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(try_checkin, i) for i in range(5)]
            for future in as_completed(futures):
                result = future.result()
                results[result] += 1
        
        # 只有一个能成功
        assert results["success"] == 1, f"期望1个成功，实际{results['success']}个"
        assert results["conflict"] == 4, f"期望4个冲突，实际{results['conflict']}个"
```

### Step 4.5.2: 提交

```bash
git add tests/integration/test_concurrent_race_conditions.py
git commit -m "test: add concurrent race condition tests for course session and checkin"
```

---

## Task 5: 修复签到班级信息快照

**问题:** 签到时记录的学生班级是当前班级，学生转班后历史签到显示新班级

**Files:**
- Modify: `backend/app/api/routes/checkin.py:123-163`

### Step 5.1: 修改签到逻辑

```python
# backend/app/api/routes/checkin.py
@router.post("/checkin", response_model=CheckinResponse)
async def do_checkin(...):
    """学生签到 - 修复：班级信息快照"""
    # ... 限流检查 ...

    # 验证学生
    from app.crud import get_student
    student = get_student(db_session, data.student_id)
    if not student:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, detail='学生不存在')

    # 检查学生所在班级是否有活跃课堂
    cs = get_active_course_session_by_class_name(db_session, student.class_name)
    if not cs or cs.status != "active":
        raise HTTPException(status_code=HttpStatus.BAD_REQUEST, detail='当前未在上课')

    # ... 签到检查 ...

    # 修复：记录班级信息快照（使用课堂所属班级）
    # 这样即使学生后续转班，历史签到仍显示正确的班级
    class_name_snapshot = cs.class_name  # 使用课堂的班级而非学生当前班级

    # 创建签到记录
    try:
        checkin = create_checkin(
            db_session,
            data.student_id,
            data.student_name or student.name,
            class_name_snapshot,  # 修复：使用快照
            cs.id,
            device_id=data.device_id,
            device_info=data.device_info
        )
    except DuplicateCheckinError:
        raise HTTPException(status_code=HttpStatus.CONFLICT, detail='您已在本课堂签到')

    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.MESSAGE: MessageConst.CHECKIN_SUCCESS,
        ApiResponseConst.DATA: checkin.model_dump()
    }
```

### Step 5.2: 提交

```bash
git add backend/app/api/routes/checkin.py
git commit -m "fix: use course session class_name for checkin snapshot"
```

---

## Task 5.5: 修复 ScoreLog 时区问题（M-01）

**问题:** ScoreLog.created_at 使用 naive datetime，与其他模型不一致

**Files:**
- Modify: `backend/app/models/checkin.py:52`

### Step 5.5.1: 修改 ScoreLog 模型

```python
# backend/app/models/checkin.py
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
    created_at: datetime = Field(default_factory=get_now, description="创建时间")  # 修复：使用 get_now
```

### Step 5.5.2: 提交

```bash
git add backend/app/models/checkin.py
git commit -m "fix: use get_now() for ScoreLog.created_at timezone consistency"
```

---

## Task 6: 修复课表删除级联处理

**问题:** 删除课表后关联的 CourseSession 和 ScheduleAdjustment 成为孤儿记录

**Files:**
- Modify: `backend/app/crud/schedule.py:36-53`

### Step 6.1: 修改删除逻辑

```python
# backend/app/crud/schedule.py
from sqlalchemy import delete
from app.models import ScheduleAdjustment, CourseSession

def delete_schedule(session: Session, schedule_id: int) -> bool:
    """
    删除课表 - 修复：级联删除关联数据

    Args:
        session: 数据库会话
        schedule_id: 课表ID

    Returns:
        bool: 删除成功返回 True，不存在返回 False
    """
    schedule = session.get(CourseSchedule, schedule_id)
    if not schedule:
        return False

    # 修复：先删除关联的调课记录
    session.execute(
        delete(ScheduleAdjustment)
        .where(ScheduleAdjustment.schedule_id == schedule_id)
    )

    # 修复：删除关联的课堂记录（只有非活跃的可以删除）
    # 活跃的课堂需要手动处理，这里只删除已结束的
    session.execute(
        delete(CourseSession)
        .where(
            CourseSession.schedule_id == schedule_id,
            CourseSession.status.in_(["ended", "cancelled"])
        )
    )

    # 如果还有活跃的课堂，不允许删除课表
    active_count = session.exec(
        select(func.count())
        .where(
            CourseSession.schedule_id == schedule_id,
            CourseSession.status == "active"
        )
    ).one()

    if active_count > 0:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail="该课程存在进行中的课堂，请先结束课堂再删除课表"
        )

    session.delete(schedule)
    session.commit()
    return True
```

### Step 6.2: 提交

```bash
git add backend/app/crud/schedule.py
git commit -m "fix: cascade delete related data when deleting schedule"
```

---

## Task 6.5: 修复删除用户级联处理（H-08）

**问题:** 删除教师账户后，其关联的课表成为孤儿数据

**Files:**
- Modify: `backend/app/crud/user.py:214-221`

### Step 6.5.1: 修改删除用户逻辑

```python
# backend/app/crud/user.py
def delete_user(session: Session, user_id: int) -> bool:
    """
    删除用户 - 修复：级联处理关联课表
    
    Args:
        session: 数据库会话
        user_id: 用户ID
        
    Returns:
        bool: 删除成功返回 True，不存在返回 False
        
    Raises:
        HTTPException: 如果用户有关联的活跃课表
    """
    from fastapi import HTTPException
    from app.core.config import HttpStatus
    from app.models import CourseSchedule
    from sqlalchemy import select, func
    
    user = session.get(User, user_id)
    if not user:
        return False
    
    # 检查是否有关联的排班
    schedule_count = session.exec(
        select(func.count())
        .where(CourseSchedule.teacher_id == user_id)
    ).one()
    
    if schedule_count > 0:
        raise HTTPException(
            status_code=HttpStatus.BAD_REQUEST,
            detail=f"该教师有关联的 {schedule_count} 个课程，请先转移或删除课程后再删除教师"
        )
    
    session.delete(user)
    session.commit()
    return True
```

### Step 6.5.2: 编写测试

```python
# tests/unit/crud/test_user_cascade.py
def test_delete_user_with_schedules_blocked():
    """测试删除有关联课表的教师被阻止"""
    # 创建教师
    user = create_user(session, "teacher1", "密码", "教师", role="teacher")
    
    # 创建课表
    schedule = CourseSchedule(
        course_name="测试课程",
        class_name="测试班级",
        teacher_id=user.id,
        teacher_name=user.name,
        day_of_week=1,
        start_time="08:00",
        end_time="09:40"
    )
    session.add(schedule)
    session.commit()
    
    # 尝试删除教师应失败
    with pytest.raises(HTTPException) as exc_info:
        delete_user(session, user.id)
    assert exc_info.value.status_code == 400
    assert "有关联" in exc_info.value.detail
```

### Step 6.5.3: 提交

```bash
git add backend/app/crud/user.py tests/unit/crud/test_user_cascade.py
git commit -m "fix: prevent deleting user with associated schedules"
```

---

## Task 7: 运行所有测试

### Step 7.1: 运行单元测试

```bash
cd backend && conda run -n student-manage pytest tests/unit -v --tb=short
```

Expected: 全部通过

### Step 7.2: 运行集成测试

```bash
cd backend && conda run -n student-manage pytest tests/integration -v --tb=short
```

Expected: 全部通过

### Step 7.3: 提交

```bash
git commit -m "test: all tests pass after consistency fixes"
```

---

## Task 8: 验证最终状态

### Step 8.1: 检查服务状态

```bash
make status
```

Expected: 服务运行正常

### Step 8.2: 手动验证关键场景

```bash
# 1. 测试教师调课级联更新
curl -X PUT http://localhost:8000/api/v1/schedules/1/assign \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d "teacher_id=2&teacher_name=新教师"

# 2. 测试 modify 调课生效
curl -X POST http://localhost:8000/api/v1/schedule-adjustments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id":1,"week_number":10,"type":"modify","new_classroom":"B202"}'

# 3. 验证课堂创建使用调课信息
curl -X POST http://localhost:8000/api/v1/course-sessions/start \
  -H "Authorization: Bearer $TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"class_name":"测试班级","schedule_id":1}'
```

### Step 8.3: 最终提交

```bash
git add -A
git commit -m "fix(database): resolve 14 data consistency issues

Database Constraints:
- Add unique constraint to schedule_adjustments (schedule_id, week_number)

Cascade Updates:
- Cascade update CourseSession.teacher_id when reassigning teacher
- Cascade delete related data when deleting schedule
- Prevent deleting user with associated schedules

Schedule Adjustments:
- Apply modify adjustment when starting course session
- Makeup adjustment creates scheduled status, auto-activate at start time
- Auto-end active sessions when canceling schedule

Data Consistency:
- Use course session class_name for checkin snapshot
- Fix ScoreLog timezone consistency

Concurrency:
- Add concurrent start session tests
- Add concurrent checkin tests

Fixes C-01, C-02, C-03, C-04, H-01, H-02, H-03, H-08, M-01, M-02"
```

---

## 验证清单

所有修复完成后，验证以下场景：

### P0 - Critical（立即验证）
- [ ] 管理员调课后，教师页面正确显示调课结果（C-01）
- [ ] makeup 类型调课创建 scheduled 状态，不立即显示在活跃列表（C-02）
- [ ] 并发开始课堂只有一个成功（C-03）
- [ ] 并发签到只有一个成功（C-04）

### P1 - High（本周验证）
- [ ] modify 类型调课的时间和教室信息在开课时生效（H-01）
- [ ] cancel 类型调课自动结束已存在的活跃课堂（H-02）
- [ ] 删除课表时级联删除关联数据（H-03）
- [ ] 删除教师时阻止如果有关联课表（H-08）

### P2 - Medium（本月验证）
- [ ] 学生转班后历史签到仍显示原始班级（M-02）
- [ ] ScoreLog 时区与其他模型一致（M-01）
- [ ] 同一课表同一周次不能重复创建调课记录

### 测试覆盖
- [ ] 所有单元测试通过（原有 + 新增）
- [ ] 所有集成测试通过（原有 + 新增）
- [ ] 并发测试通过
- [ ] 手动端到端测试通过
