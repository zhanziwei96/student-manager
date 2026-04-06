# ClassHub 课程表闭环设计文档

**文档版本**: v1.0  
**日期**: 2026-04-06  
**状态**: 已确认，待实施  

---

## 1. 设计目标

将现有"课表数据（CourseSchedule）"与"实际课堂（ClassSession）"完全打通，形成教学闭环：

```
课表模板 → 单次上课实例 → 学生签到 → 历史追溯 → 调课/停课/补课
```

---

## 2. 核心决策

| 决策项 | 方案 | 说明 |
|--------|------|------|
| 课表约束策略 | 软引导 | 有课表时自动推荐并携带 schedule_id 开课，无课表时允许手动开课并提示确认 |
| 数据模型 | 方案B：单表统一 | 废弃 `class_session` 表，新建 `course_sessions` 作为"单次上课实例"唯一主表；`checkin_records` 外键指向 `course_sessions.id` |
| 调课范围 | 完整支持 | 临时停课、调课（改时间/教室）、补课 |

---

## 3. 核心概念

| 概念 | 职责 | 对应表 |
|------|------|--------|
| CourseSchedule | 静态课表模板，描述"每周三10点有什么课" | `course_schedules` |
| CourseSession | 单次上课实例，描述"第5周周三的那一节计算机应用基础课" | `course_sessions` (新) |
| ScheduleAdjustment | 对单次上课实例的例外调整 | `schedule_adjustments` (新) |
| CheckinRecord | 学生签到记录，关联到具体的 CourseSession | `checkin_records` (改外键) |

---

## 4. 数据模型

### 4.1 CourseSession（单次上课实例）

```python
class CourseSession(SQLModel, table=True):
    __tablename__ = "course_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: Optional[int] = Field(
        default=None,
        foreign_key="course_schedules.id",
        description="关联的课表ID"
    )
    session_code: str = Field(..., description="课堂唯一代码", index=True)
    course_name: Optional[str] = Field(default=None, description="课程名称")
    class_name: str = Field(..., description="班级名称", index=True)
    classroom: Optional[str] = Field(default=None, description="教室")
    teacher_id: int = Field(..., description="教师ID", index=True)
    teacher_name: Optional[str] = Field(default=None, description="教师姓名")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    week_number: Optional[int] = Field(default=None, description="教学周次")
    status: str = Field(default="active", description="课堂状态: active|ended|cancelled", index=True)
    source_type: str = Field(default="manual", description="来源类型: scheduled|manual|makeup")
    updated_at: datetime = Field(default_factory=get_shanghai_now, description="更新时间")
```

**索引**:
- `(teacher_id, status)`：活跃课堂查询
- `(class_name, status)`：班级活跃课堂查询
- `(schedule_id, week_number)`：课表+周次历史查询

### 4.2 ScheduleAdjustment（课表调整记录）

```python
class ScheduleAdjustment(SQLModel, table=True):
    __tablename__ = "schedule_adjustments"

    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: int = Field(..., foreign_key="course_schedules.id", description="关联课表ID")
    week_number: int = Field(..., description="第几周")
    type: str = Field(..., description="调整类型: cancel|modify|makeup")
    new_date: Optional[date] = Field(default=None, description="新日期")
    new_start_time: Optional[str] = Field(default=None, description="新开始时间")
    new_end_time: Optional[str] = Field(default=None, description="新结束时间")
    new_classroom: Optional[str] = Field(default=None, description="新教室")
    generated_session_id: Optional[int] = Field(
        default=None,
        foreign_key="course_sessions.id",
        description="补课生成的课堂实例ID"
    )
    reason: Optional[str] = Field(default=None, description="调整原因")
    created_by: int = Field(..., description="操作人ID")
    created_at: datetime = Field(default_factory=get_shanghai_now)
```

### 4.3 关联模型调整

**CheckinRecord**: `session_id` 的外键指向改为 `course_sessions.id`。

**CourseSchedule**: 新增 `week_type` 字段，支持 `all/odd/even/custom`。

```python
class CourseSchedule(SQLModel, table=True):
    # ... 原有字段不变 ...
    week_type: str = Field(default="all", description="周类型: all|odd|even|custom")
```

**导入模板更新**: `schedules.py` 下载的 Excel 模板需要增加可选列 `周类型`（默认值 `all`），导入逻辑需兼容无此列的旧模板。

### 4.4 数据迁移

1. 创建 `course_sessions` 和 `schedule_adjustments` 表。
2. 将 `class_session` 数据迁移到 `course_sessions`：
   - `active=1` → `status='active'`
   - `active=0` → `status='ended'`
   - `source_type='manual'`
3. 通过 `start_time + class_name + teacher_id` 重新映射 `checkin_records.session_id`。
4. 可选：对历史 `CourseSession` 反查 `course_schedules` 回填 `schedule_id`。

---

## 5. API 设计

### 5.1 新增/修改的 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/course-sessions` | 教师课堂列表（活跃+历史） |
| `POST` | `/course-sessions/start` | 开始上课，可传 `schedule_id` |
| `POST` | `/course-sessions/{id}/end` | 结束上课 |
| `GET` | `/course-sessions/{id}/stats` | 单次课堂签到统计 |
| `POST` | `/schedule-adjustments` | 创建调课/停课/补课 |
| `GET` | `/schedule-adjustments` | 查询调整记录 |
| `GET` | `/schedules/today` | 今日课表（增强，带状态） |
| `POST` | `/checkin` | 学生签到（底层表切换） |
| `GET` | `/checkins/today` | 今日签到列表（底层表切换） |
| `GET` | `/checkins/stats` | 签到统计（底层表切换） |

### 5.2 开始上课

**请求**: `POST /course-sessions/start`

```json
{
  "class_name": "2025中药学1班",
  "course_name": "计算机应用基础",
  "schedule_id": 12
}
```

**业务规则**:
1. 班级冲突检测：该班级已有 `status=active` 的课堂则拒绝。
2. 传入 `schedule_id` 时：校验课表存在且 `class_name`/`course_name` 一致；自动计算当前教学周次 `week_number`（后端复用与前端 `getCurrentWeek` 一致的计算逻辑，默认以学期开始日期为基准）；`source_type="scheduled"`。
3. 未传入 `schedule_id` 时：提示"当前时段无排课，确认手动开启？"；`source_type="manual"`。
4. 补课场景：`schedule_id` 为 null 但指定 `course_name` 时视为临时补课。

### 5.3 今日课表增强

**请求**: `GET /schedules/today`

**新增返回字段**（每个课表项）:

```json
{
  "week_number": 7,
  "week_type_match": true,
  "session_status": "none",
  "active_session_id": null,
  "adjustment": null
}
```

**状态计算逻辑**:
1. 检查 `week_type` 是否匹配当前周（单双周过滤）。
2. 查询 `ScheduleAdjustment`，如有则返回对应状态。
3. 查询该周次是否已有 `CourseSession`，返回 `active`/`ended`。
4. 否则返回 `none`。

### 5.4 调课/停课/补课

**请求**: `POST /schedule-adjustments`

| 类型 | 必填字段 | 业务规则 |
|------|----------|----------|
| `cancel` | `schedule_id`, `week_number`, `reason` | 已结束的课程允许标记停课但提示警告；进行中的课程不允许停课 |
| `modify` | `schedule_id`, `week_number` + 新时间/教室 | 已结束的禁止调课；进行中的允许调课但`start_time`不变；调课后需冲突检测 |
| `makeup` | 日期时间、`course_name`、`class_name` | `schedule_id` 可选；创建 `CourseSession(source_type="makeup")`；需冲突检测 |

---

## 6. 前端交互

### 6.1 教师 Dashboard 今日课表

- **未上课（30分钟前）**: disabled，显示"待上课"
- **可上课（前后15分钟）**: 高亮，按钮"开始签到"，点击直接开课
- **签到进行中**: 脉冲绿点，显示签到人数，按钮"管理中"
- **已结束/已停课**: 变淡，不可点击

### 6.2 ClassSession 页面

- **当前无活跃课堂**: 顶部显示"今日排课快捷卡片"，一键开课；下方保留折叠的"手动开课"入口
- **当前有活跃课堂**: 正常管理签到，标题显示课堂来源信息（按课表 / 手动 / 补课）

### 6.3 新增页面/组件

- **调课弹窗组件**: Admin/Teacher 在 `Schedules.vue` 中对课程发起停课/调课/补课
- **历史课堂页面** (`/teacher/sessions-history`): 按周次/班级/课程筛选历史课堂，显示签到率，支持查看详情

### 6.4 路由调整

```javascript
{
  path: '/teacher/sessions-history',
  name: 'TeacherSessionsHistory',
  component: () => import('@/views/teacher/SessionsHistory.vue')
}
```

---

## 7. 测试策略

### 7.1 后端测试

- `test_start_class_with_schedule_id`：按课表开课，`week_number` 自动计算
- `test_start_class_manual`：手动开课成功
- `test_cancel_active_class_rejected`：进行中的课程不能停课
- `test_modify_classroom_conflict`：调课冲突检测拒绝
- `test_checkin_after_table_migration`：签到关联新表正常
- `test_today_schedule_status_combinations`：今日课表各种状态组合

### 7.2 前端测试

- Dashboard 课程状态卡片渲染及按钮行为
- ClassSession 快捷开课/手动开课切换
- 调课弹窗各模式的表单校验

### 7.3 E2E 测试

- 教师 Dashboard 点击"开始签到" → 学生签到 → 教师结束签到的完整闭环

---

## 8. 风险与回滚

| 风险 | 缓解措施 |
|------|----------|
| 迁移时系统在线 | 选择低峰期执行，脚本幂等设计 |
| `checkin_records` 映射失败 | 迁移前备份数据库，迁移后 count 校验 |
| 旧 API 残留引用 | 全局 `grep` 检查 `/class-session` 引用，一次性替换 |

---

## 9. 附录：废弃清单

以下代码在本次实施后将废弃：

- `backend/app/models/checkin.py` 中的 `ClassSession` 模型
- `backend/app/crud/checkin.py` 中基于 `ClassSession` 的 CRUD 函数（需重构为 `CourseSession`）
- API 路由 `/class-session/*`（替换为 `/course-sessions/*`）
- 前端 `useClassSessions` 等 composables 中对 `/class-session` 的调用
