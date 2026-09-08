# ClassHub 学期/届数数据库重构方案

> 版本：v1.2 | 日期：2026-09-08 | 规模：2000 学生 / 10 教师 / 4GB 内存
>
> **v1.2 修订记录**（大学场景定位）：
> ① 新增课程线三表：`courses`（课程目录）/ `course_offerings`（教学班）/ `enrollments`（选课）
> ② 决策：`class_scope` 用字符串（合班教学）、成绩挂 `enrollments`、不做学分/GPA
> ③ 确认移除 `teacher_class_semesters`（教师授课事实唯一真源 = offerings.teacher_id，见 2.2 课程线）
> ④ 成绩模型三组件：个人成绩（`enrollments.score`，授课教师改）＋ 小组成绩（`groups.score` 科目维度累计）＋ 期末成绩（`enrollments.final_score`，试卷个人分/任务小组同分）；**取消综合分**（`student_semester_scores` 不建，`Student.score` 废弃）
> ⑤ 小组改造：保留科目维度（subject_id → course_id），小组持续一学期做多个任务；**删除任务/互评流程**（group_tasks 系列表废弃）
> ⑥ 排行榜 4 榜：班内/跨班 × 个人/小组，仅限教师所教科目的成绩
>
> **v1.1 修订记录**（对照实际代码评审后）：
> ① 补学生-班级-学期三元表 `student_class_semesters`（与教师侧对称，填补"学生各学期班级归属"缺口）
> ② 明确学生状态机（`status`）与届的语义（`cohort_year` 为身份属性，不随转班更新）
> ③ 补管理员学期场景（跨学期报表、审计加 semester 维度）
> ④ 修正物化视图 SQL（SELECT 缺 `semester_id` 列 bug）
> ⑤ 性能章节 P1/P2 整体降级为附录 A（2000 学生规模下无收益）
> ⑥ 1.3 分布表补漏 `answers` / `audit_logs` / `device_binds`

---

## 一、现状诊断

### 1.1 已有的学期基础设施

- `semester` 字符串字段（格式 `"2026-2027-1"`）已加到 9 张业务表
- `TermSettings` 配置在 `.env` 中（`label`、`start_date`、`total_weeks`）
- `term.py` 提供 `get_current_term()` / `get_current_week_number()` 工具函数
- `subjects` + `student_subject_scores` 表已按 semester 隔离

### 1.2 结构性缺口

| 缺口 | 现状 | 后果 |
|------|------|------|
| **学生没有"届"** | `Student` 表只有 `class_name` 字符串 | 无法区分不同届的同名班级；毕业生无法按届归档 |
| **教师-班级映射不感知学期** | `User.assigned_classes` 是跨学期的 JSON 字符串 | 教师换班后历史映射丢失；无法按学期查询 |
| **班级只是个字符串** | 没有 `classes` 表，`class_name` 散落在 9+ 张表 | 无引用完整性；班级重命名要改 N 张表 |
| **学期只是字符串+配置** | semester 标识散落各表 + 元数据在 `.env` | 切换学期需改配置重启；历史学期元数据不保留 |
| **学生分数是全局累计** | `Student.score` 字段无学期维度 | 学期切换时需手动清零；历史分数无法追溯 |
| **ClassGroupSettings 没有学期** | 用 `class_name` 做主键，无 semester | 不同学期的班级设置共享，无法独立管理 |
| **课程只是个字符串** | `course_schedule.course_name` 散落课表/调课/课堂，无 courses 实体 | 无课程编码/目录；无法按课程聚合统计；课程改名要改 N 张表 |

### 1.3 semester 字段分布

| 表 | 有 semester | 有 class_name |
|----|------------|---------------|
| `course_schedules` | ✅ | ✅ |
| `course_sessions` | ✅ | ✅ |
| `checkin_records` | ✅ | ✅ |
| `score_logs` | ✅ | ❌ |
| `groups` | ✅ | ✅ |
| `group_tasks` | ✅ | ✅ |
| `group_evaluation_scores` | ✅ | ❌ |
| `questions` | ✅ | ✅ |
| `schedule_adjustments` | ✅ | ❌ |
| `subjects` | ✅ | ❌ |
| `student_subject_scores` | ✅ | ❌ |
| `student_subject_score_logs` | ✅ | ❌ |
| `group_score_logs` | ✅ | ❌ |
| `students` | ❌ | ✅ |
| `users` | ❌ | ✅（JSON） |
| `class_group_settings` | ❌ | ✅（主键） |
| `answers` | ❌ | ❌ |
| `audit_logs` | ❌ | ❌（重构后建议加 semester，管理员按学期审计） |
| `device_binds` | ❌ | ❌ |

---

## 二、目标架构：终极优雅方案

### 2.1 设计原则

1. **一个事实只存一次** — 班级名只在 `classes` 表，学期信息只在 `semesters` 表
2. **每个真实概念都是一等公民** — 届、班级、学期全部实体表化
3. **时间和身份正交分离** — 身份线（Cohort→Class→Student）+ 时间线（Semester）在业务层自然交叉

```
身份线（稳定）                 时间线（随学期切换）
  Cohort ── Class ── Student    Semester ── 业务数据
  （入学届）  （班级） （学生）  （学期）    （签到/分数/课表...）
```

### 2.2 完整表结构

#### 核心实体表

```python
# ─── cohorts 表 ───
class Cohort(SQLModel, table=True):
    """届 — 一届学生，入学年份相同"""
    __tablename__ = "cohorts"

    year: str = Field(primary_key=True, max_length=10)         # "2026"
    label: str = Field(default="", max_length=50)               # "2026届"
    entry_semester_id: int = Field(foreign_key="semesters.id")  # 入学学期
    status: str = Field(default="active", max_length=20)        # active | graduated


# ─── semesters 表 ───
class Semester(SQLModel, table=True):
    """学期 — 实体化，替代 .env 配置"""
    __tablename__ = "semesters"

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str = Field(unique=True, max_length=20)              # "2026-2027-1"
    start_date: date                                             # 开学第一天
    total_weeks: int                                             # 总周数
    is_current: bool = Field(default=False, index=True)          # 当前学期标记
    status: str = Field(default="active", max_length=20)         # active | archived


# ─── classes 表 ───
class Class(SQLModel, table=True):
    """班级 — 届下的一个班"""
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint('name', 'cohort_year', name='uix_class_name_cohort'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)                            # "1班"
    cohort_year: str = Field(foreign_key="cohorts.year", index=True)
    # GENERATED 列：自动拼接显示名
    display_name: str  # PG 自动生成 "2026届1班"


# ─── students 表（改造） ───
class Student(StudentBase, table=True):
    """学生 — 归属于班级，班级隐含届"""
    __tablename__ = "students"

    student_id: str = Field(primary_key=True)
    name: str
    class_id: int = Field(foreign_key="classes.id", index=True)       # ← 当前班级（冗余缓存，真源见 student_class_semesters）
    cohort_year: str = Field(max_length=10, index=True)               # ← 身份属性（入学年），不随转班更新
    class_name: str = Field(default="未分班", max_length=100)         # ← 冗余（免 JOIN 显示）
    status: str = Field(default="active", max_length=20)              # ← active|suspended|withdrawn|graduated
    is_account_enabled: bool = Field(default=True)
    # score 字段（综合分）废弃 — 个人成绩 = 各科目成绩（enrollments.score）
    ...
```

**学生状态机与届的语义**（关键设计决策）：
- `status`（学籍状态）与 `is_account_enabled`（账户开关）正交：前者控制学籍归属，后者只控制登录
- `cohort_year` 是身份属性 = 入学年，转班/换班**不更新**；留级是显式管理操作（换届 + 更新 cohort_year）
- `students.class_id` 只是"当前班级"的冗余缓存，真源是 `student_class_semesters` 当前学期行

#### 课程线（大学场景核心）

> 大学语境下"课堂"的第一公民是课程：课程目录 → 教学班 → 选课名单。
> 现有 `subjects`（每学期一条）+ `student_subject_scores`（学生×科目×教师×学期+分数）是雏形，重构升级为以下三张表。

```python
# ─── courses 表（课程目录，跨学期稳定） ───
class Course(SQLModel, table=True):
    """课程目录 — 一门课程一条记录（由 subjects 按 name 去重升级）"""
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint('code', name='uix_course_code'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=20)                          # 课程编码（如 MATH1001，第一身份）
    name: str = Field(max_length=100)                         # 课程名称（不唯一：同名不同层次常见）
    department: str = Field(default="", max_length=50)        # 开课院系（字符串起步，需要时再实体化）
    status: str = Field(default="active", max_length=20)      # active | archived
    created_at: datetime = Field(default_factory=get_now)


# ─── course_offerings 表（教学班/开课） ───
class CourseOffering(SQLModel, table=True):
    """教学班 — 某学期某教师上某课程的一个班（课程可有多个平行教学班）"""
    __tablename__ = "course_offerings"
    __table_args__ = (
        UniqueConstraint('course_id', 'semester_id', 'teacher_id', 'class_scope',
                         name='uix_offering'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="courses.id", index=True)
    semester_id: int = Field(foreign_key="semesters.id", index=True)
    teacher_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)  # 可空：先排课后定教师
    teacher_name: str = Field(default="", max_length=50)       # 冗余快照（免 JOIN 显示）
    class_scope: str = Field(max_length=100)                   # 面向范围 "计科1-2班"（展示用，过滤用 offering_id）
    capacity: Optional[int] = Field(default=None)              # 容量（可选）
    status: str = Field(default="active", max_length=20)       # active | ended
    created_at: datetime = Field(default_factory=get_now)


# ─── enrollments 表（选课关系） ───
class Enrollment(SQLModel, table=True):
    """选课 — 学生×教学班×学期，成绩直接挂选课记录（吸收 student_subject_scores）"""
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint('student_id', 'offering_id', name='uix_enrollment'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="students.student_id", index=True)
    offering_id: int = Field(foreign_key="course_offerings.id", index=True)
    semester_id: int = Field(foreign_key="semesters.id", index=True)   # 冗余第二 FK（按学期过滤免 JOIN）
    status: str = Field(default="enrolled", max_length=20)             # enrolled | dropped（退课标记，保留历史）
    score: float = Field(default=0.0, index=True)                      # 个人成绩（该科目平时分，授课教师修改）
    final_score: Optional[float] = Field(default=None, index=True)     # 期末成绩（试卷=个人分；任务=小组同分；独立于个人成绩/小组成绩）
    version: int = Field(default=1)                                    # 乐观锁（打分并发）
    created_at: datetime = Field(default_factory=get_now)
    updated_at: datetime = Field(default_factory=get_now)
```

**课程线关键设计决策**：
- `class_scope` 用字符串而非 `class_id` FK：大学合班上课是常态（计科1、2班合上），单 FK 表达不了；名单由 enrollments 承载
- 上课时间/教室留在课表：`course_schedule` 改造后挂 `offering_id`，一个教学班多个时间槽，教室随时间槽走（调课方便）
- 期中换教师 = 拆分新 offering：enrollment 迁到新 offering（旧标 `dropped`），比现有 subjects 唯一约束硬塞教师维度更干净
- **成绩体系三组件**（无综合分、无学分/GPA、无多维度）：个人成绩 `enrollments.score`（授课教师修改）＋ 小组成绩 `groups.score`（科目维度累计分）＋ 期末成绩 `enrollments.final_score`（试卷→个人分；任务→小组成员同分，独立于前两者）
- **教师权限从 offerings 派生（已确认）**：不建 `teacher_class_semesters` 表，教师授课事实的唯一真源是 `offering.teacher_id`，教师权限查询 = JOIN offerings（见 9.7）

#### 小组改造（保留科目维度，删除任务/互评流程）

- **小组定义**：班级×学期×科目维度的持续小组，一学期一起做多个任务；学生可按科目加入不同小组
- **结构改造**：`groups.subject_id` → `course_id` FK；`class_name` → `class_id` FK；`score` 为小组累计分（保留乐观锁），教师直接加减
- **删除**：`group_tasks` / `group_task_dimensions` / `evaluation_assignments` / `group_evaluation_scores` 表及任务/互评流程停用（Phase 4 删除，旧数据只读保留）
- **期末任务小组同分**：教师登记期末成绩时选教学班 + 小组 → 该小组组员在 `enrollments.final_score` 写同样的分；试卷形式则逐个学生写个人分

#### 桥接表

> ⚠️ 原方案的 `teacher_class_semesters` 已确认**移除**：教师授课事实的唯一真源是
> `course_offerings.teacher_id`（见上方课程线决策），教师权限查询 = JOIN offerings 派生，
> `User.assigned_classes` JSON 过渡期保留、Phase 4 删除。

```python
# ─── student_class_semesters 表 ───
class StudentClassSemester(SQLModel, table=True):
    """学生-班级-学期 三元关系 — 记录学生每个学期的班级归属（与教师侧对称）"""
    __tablename__ = "student_class_semesters"
    __table_args__ = (
        UniqueConstraint('student_id', 'semester_id',
                         name='uix_student_class_semester'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: str = Field(foreign_key="students.student_id", index=True)
    class_id: int = Field(foreign_key="classes.id", index=True)
    semester_id: int = Field(foreign_key="semesters.id", index=True)
    created_at: datetime = Field(default_factory=get_now)
```

> 综合分（`student_semester_scores`）已确认**不建**：个人成绩 = 各科目成绩（`enrollments.score`），
> 现 `Student.score` 综合分废弃（过渡期只读，Phase 4 删除）。

#### 业务表改造（全部 class_name → class_id, semester → semester_id）

```python
# 以 checkin_records 为例（其他业务表同理）
class CheckinRecord(SQLModel, table=True):
    __tablename__ = "checkin_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    semester_id: int = Field(foreign_key="semesters.id", index=True)    # ← 替代 semester str
    session_id: Optional[int] = Field(foreign_key="course_sessions.id", index=True)
    student_id: str = Field(foreign_key="students.student_id", index=True)
    class_id: int = Field(foreign_key="classes.id", index=True)         # ← 替代 class_name str
    class_name: str = Field(max_length=100)                              # ← 冗余（历史快照）
    student_name: Optional[str] = Field(default=None, max_length=50)    # ← 冗余（历史快照）
    checkin_type: str
    checkin_time: datetime
    ...
```

### 2.3 实体关系图

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│  cohorts   │1──N│  classes   │1──N│  students  │
│  "2026届"  │    │  "1班"     │    │  张三      │
│  status    │    │  cohort_year│    │  class_id  │
└───────────┘    └───────────┘    └───────────┘
                      │
                      │
                      ▼
  ┌────────────────────┐
  │ student_class_     │
  │ semesters          │
  │ (学生-班级-学期)    │
  └────────┬───────────┘
           │
           ▼
    ┌───────────┐
    │ semesters │
    │ "2026-    │
    │  2027-1"  │
    │ start_date│
    │ is_current│
    └───────────┘
           │
  ┌────────┼───────────┐
  ▼        ▼           ▼
course_schedules  checkin_records  groups
course_sessions   score_logs      enrollments
...               ...            (course_offerings 亦挂 semesters)
    (全部用 semester_id + class_id FK + 冗余 class_name)
```

### 2.4 冗余字段策略（受控反范式化）

| 冗余字段 | 所在表 | 来源 | 用途 | 更新规则 |
|----------|--------|------|------|----------|
| `class_name` | 所有业务表 | `classes.name` | 前端列表展示免 JOIN | 写入时拷贝，不改历史 |
| `class_id` | `students` | `student_class_semesters` 当前学期行 | 当前班级免 JOIN | 转班时与归属表同步更新 |
| `cohort_year` | `students` | 入学年份（身份属性） | 按届过滤免 JOIN | 永不随转班更新（留级走显式流程） |
| `student_name` | `checkin_records` 等 | `students.name` | 列表展示免 JOIN | 写入时拷贝，不改历史 |

**核心规则**：
- 过滤/JOIN 永远用 FK（`class_id`、`semester_id`），不用冗余字段
- 冗余字段仅供 SELECT 显示，不改历史数据
- 冗余字段的不一致是可接受的（它代表写入时的快照）
- 学生班级归属的真源是 `student_class_semesters`；`students.class_id` / `class_name` 只是当前值的冗余缓存

---

## 三、查询对比

| 查询 | 现在（字符串 + JSON） | 重构后（FK + 实体表） |
|------|----------------------|----------------------|
| 2026 届有哪些学生 | ❌ 无法查 | `SELECT s.* FROM students s WHERE s.cohort_year='2026'` |
| 张老师这学期教哪些班/课 | JSON 解析 `assigned_classes` | `SELECT * FROM course_offerings WHERE teacher_id=X AND semester_id=当前`（所教班级由此派生） |
| 1 班这学期签到 | `WHERE class_name='1班' AND semester='...'` | `WHERE class_id=X AND semester_id=Y` — 索引精确命中 |
| 班级改名 | 改 9 张表 | 改 `classes` 表 1 行 |
| 切换学期 | 改 .env + 重启 | `UPDATE semesters SET is_current=...` — 一条 SQL |
| 2025 届毕业 | ❌ 只能逐个 disable 学生 | `UPDATE cohorts SET status='graduated' WHERE year='2025'` |
| 学生各科成绩历史 | 综合分只有当前值，科目分散落 | `enrollments` 按学期天然保留每科 score + final_score 历史 |
| 上学期 1 班学生名单 | ❌ 只能靠业务表快照字符串查询 | `SELECT s.* FROM student_class_semesters scs JOIN students s ON s.student_id=scs.student_id WHERE scs.class_id=X AND scs.semester_id=Y` |
| 学生转班历史 | ❌ 无记录 | `SELECT * FROM student_class_semesters WHERE student_id=X ORDER BY semester_id` |
| 教学班学生名单 | ❌ 无教学班实体，靠课表字符串推导 | `SELECT * FROM enrollments WHERE offering_id=X AND status='enrolled'` |
| 学生退课历史 | ❌ 无记录 | `SELECT * FROM enrollments WHERE student_id=X AND status='dropped'` |
| 排行榜（4 榜：班内/跨班 × 个人/小组，仅所教科目） | 按综合分全局排 | `enrollments.score` / `groups.score` 按 `offering_id` / `course_id` / `class_id` FK 过滤 |

---

## 四、ACID 性能优化

### 4.1 索引策略（P0 — 必须做）

```sql
-- ═══ 所有 FK 列必须建索引（PG 不自动建！） ═══
CREATE INDEX idx_students_class_id ON students(class_id);
CREATE INDEX idx_students_cohort_year ON students(cohort_year);
CREATE INDEX idx_checkin_class_id ON checkin_records(class_id);
CREATE INDEX idx_checkin_semester_id ON checkin_records(semester_id);
CREATE INDEX idx_schedule_class_id ON course_schedules(class_id);
CREATE INDEX idx_schedule_semester_id ON course_schedules(semester_id);
CREATE INDEX idx_sessions_class_id ON course_sessions(class_id);
CREATE INDEX idx_sessions_semester_id ON course_sessions(semester_id);
CREATE INDEX idx_groups_class_id ON groups(class_id);
CREATE INDEX idx_groups_semester_id ON groups(semester_id);
-- group_tasks / group_evaluation_scores 已废弃（任务/互评流程删除），不建索引
CREATE INDEX idx_questions_semester_id ON questions(semester_id);
CREATE INDEX idx_adjustments_semester_id ON schedule_adjustments(semester_id);
CREATE INDEX idx_scorelogs_semester_id ON score_logs(semester_id);
CREATE INDEX idx_scs_student_id ON student_class_semesters(student_id);
CREATE INDEX idx_offerings_course_id ON course_offerings(course_id);
CREATE INDEX idx_offerings_semester_id ON course_offerings(semester_id);
CREATE INDEX idx_enrollments_offering_id ON enrollments(offering_id);
CREATE INDEX idx_scs_class_id ON student_class_semesters(class_id);
CREATE INDEX idx_scs_semester_id ON student_class_semesters(semester_id);
CREATE INDEX idx_groups_course_id ON groups(course_id);
CREATE INDEX idx_classes_cohort_year ON classes(cohort_year);

-- ═══ 复合索引：覆盖高频查询 ═══
-- 签到记录：按班级+学期查询（最高频）
CREATE INDEX idx_checkin_class_semester
    ON checkin_records(class_id, semester_id, checkin_time DESC);

-- 课表：按班级+学期+星期
CREATE INDEX idx_schedule_class_semester_dow
    ON course_schedules(class_id, semester_id, day_of_week);

-- 课堂会话：按班级+学期+状态
CREATE INDEX idx_sessions_class_semester_status
    ON course_sessions(class_id, semester_id, status);

-- 小组：按班级+学期+科目（小组排名最高频）
CREATE INDEX idx_groups_class_semester_course
    ON groups(class_id, semester_id, course_id);

-- 教学班：按教师+学期（教师端"我的教学班"最高频）
CREATE INDEX idx_offerings_teacher_semester
    ON course_offerings(teacher_id, semester_id);

-- 选课：按学期+学生（学生端"我的选课"最高频）
CREATE INDEX idx_enrollments_semester_student
    ON enrollments(semester_id, student_id);

-- 学生班级归属：按班级+学期查学生名单（最高频之一）
CREATE INDEX idx_scs_class_semester
    ON student_class_semesters(class_id, semester_id);

-- ═══ 部分索引 ═══
-- 当前学期只有 1 行，索引极小
CREATE INDEX idx_semesters_is_current
    ON semesters(is_current) WHERE is_current = True;
```

### 4.2 应用层缓存（P0）

```python
# app/core/term.py — 改为从数据库读取 + 应用层缓存
_current_semester_cache: Optional[Semester] = None
_current_semester_ts: float = 0
_CACHE_TTL = 60  # 60 秒

def get_current_semester(session: Session) -> Semester:
    """获取当前学期 — 带应用层缓存"""
    global _current_semester_cache, _current_semester_ts
    import time
    now = time.time()
    if _current_semester_cache and (now - _current_semester_ts) < _CACHE_TTL:
        return _current_semester_cache
    sem = session.exec(
        select(Semester).where(Semester.is_current == True)
    ).first()
    if sem:
        _current_semester_cache = sem
        _current_semester_ts = now
    return sem

def get_current_semester_id(session: Session) -> int:
    sem = get_current_semester(session)
    return sem.id if sem else 1

def get_current_term() -> str:
    """保持向后兼容"""
    if _current_semester_cache:
        return _current_semester_cache.label
    return "unknown"


# app/core/class_cache.py — 班级映射缓存
_class_cache: dict[int, Class] = {}
_class_name_to_id_cache: dict[str, int] = {}

def get_class_by_id(session: Session, class_id: int) -> Class:
    if class_id in _class_cache:
        return _class_cache[class_id]
    cls = session.get(Class, class_id)
    if cls:
        _class_cache[class_id] = cls
        _class_name_to_id_cache[cls.name] = cls.id
    return cls

def get_class_id_by_name(session: Session, class_name: str) -> Optional[int]:
    if class_name in _class_name_to_id_cache:
        return _class_name_to_id_cache[class_name]
    cls = session.exec(
        select(Class).where(Class.name == class_name)
    ).first()
    if cls:
        _class_cache[cls.id] = cls
        _class_name_to_id_cache[cls.name] = cls.id
        return cls.id
    return None

def invalidate_class_cache():
    _class_cache.clear()
    _class_name_to_id_cache.clear()
```

### 4.3 防 N+1 查询（P0）

```python
from sqlalchemy.orm import joinedload, selectinload

# ❌ N+1：2000 个学生 = 2001 次查询
students = session.exec(select(Student)).all()
for s in students:
    print(s.class_.name)

# ✅ joinedload：1 次 JOIN
students = session.exec(
    select(Student).options(joinedload(Student.class_))
).all()

# ✅ selectinload：2 次查询（适合一对多）
students = session.exec(
    select(Student).options(selectinload(Student.class_))
).all()
```

### 4.4 物化视图排行榜（P1 — 已移至附录 A.1）

> 原方案此处规划物化视图。经规模评估：2000 行实时 `ORDER BY` 已有
> `idx_students_score` 索引，<1ms，物化视图 + REFRESH CONCURRENTLY 的复杂度不划算。
> **当前不实施**。原版本 SQL 有 bug：SELECT 列表缺 `semester_id` 列，
> 而 UNIQUE INDEX 依赖该列，建索引会直接报错。修正后的完整 SQL 见附录 A.1。

### 4.5 UPSERT 幂等操作（P2 — 已移至附录 A.2）

> 10 教师并发下重复提交冲突率 <1%，现有"先查后写 + 唯一约束兜底"即可。
> 需要时再按附录 A.2 改造。

### 4.6 学期切换分批处理

```python
def semester_rollover(session: Session, new_semester_id: int):
    """学期切换 — advisory lock + 分批"""
    # 互斥锁：防止多个管理员同时切换
    acquired = session.execute(
        text("SELECT pg_try_advisory_xact_lock(20260908)")
    ).scalar()
    if not acquired:
        raise HTTPException(409, "学期切换正在进行中")

    old_semester_id = get_current_semester_id_cached()

    # 步骤1：切换当前学期标记（瞬间完成）
    session.execute(
        update(Semester).values(is_current=False).where(Semester.id == old_semester_id)
    )
    session.execute(
        update(Semester).values(is_current=True).where(Semester.id == new_semester_id)
    )
    session.commit()

    # 步骤2：为新学期创建学生班级归属（默认沿用上一学期班级，管理员可再调整）
    # 注：原"创建学生分数记录"步骤已取消 — 综合分废弃，成绩随 enrollments 按学期自然隔离
    # 注意：from sqlalchemy import literal
    session.execute(
        insert(StudentClassSemester).from_select(
            ["student_id", "class_id", "semester_id"],
            select(
                StudentClassSemester.student_id,
                StudentClassSemester.class_id,
                literal(new_semester_id),
            ).where(
                StudentClassSemester.semester_id == old_semester_id,
                StudentClassSemester.student_id.in_(
                    select(Student.student_id).where(Student.status == "active")
                ),
            )
        )
    )
    session.commit()

    # 步骤3：复制开课计划（上一学期 active 教学班 → 新学期，教师默认留任，管理员可再调整）
    session.execute(
        insert(CourseOffering).from_select(
            ["course_id", "semester_id", "teacher_id", "teacher_name", "class_scope"],
            select(
                CourseOffering.course_id,
                literal(new_semester_id),
                CourseOffering.teacher_id,
                CourseOffering.teacher_name,
                CourseOffering.class_scope,
            ).where(
                CourseOffering.semester_id == old_semester_id,
                CourseOffering.status == "active",
            )
        )
    )
    session.commit()

    # 步骤4：复制选课名单（新旧教学班按 course_id 映射；dropped 不复制）
    # 注意：from sqlalchemy.orm import aliased
    new_offering = aliased(CourseOffering)
    session.execute(
        insert(Enrollment).from_select(
            ["student_id", "offering_id", "semester_id"],
            select(
                Enrollment.student_id,
                new_offering.id,
                literal(new_semester_id),
            )
            .select_from(Enrollment)
            .join(CourseOffering, Enrollment.offering_id == CourseOffering.id)
            .join(new_offering, new_offering.course_id == CourseOffering.course_id)
            .where(
                Enrollment.semester_id == old_semester_id,
                Enrollment.status == "enrolled",
                new_offering.semester_id == new_semester_id,
            )
        )
    )
    session.commit()

    # 步骤5：刷新物化视图（未启用物化视图时跳过，见附录 A.1）
    session.execute(text(
        "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_semester_score_ranking"
    ))
    session.commit()

    # 步骤4：清除缓存
    invalidate_semester_cache()
```

### 4.7 FK 级联策略

| 关系 | 级联策略 | 理由 |
|------|----------|------|
| Class → Cohort | **RESTRICT** | 届下有班级时禁止删届 |
| Student → Class | **RESTRICT** | 班下有学生时禁止删班 |
| CheckinRecord → CourseSession | **CASCADE** | 课堂删了，签到没意义 |
| GroupMember → Group | **CASCADE** | 小组删了，成员自然解散 |
| CourseOffering → Course | **RESTRICT** | 课程有开课时禁止删（停开用归档） |
| Enrollment → Offering | **CASCADE** | 教学班删了，选课没意义 |
| Enrollment → Student | **CASCADE** | 学生删了，选课没意义 |
| StudentClassSemester → Student | **CASCADE** | 学生删了，归属记录没意义 |
| StudentClassSemester → Class | **CASCADE** | 班级删了，归属记录没意义 |
| StudentClassSemester → Semester | **RESTRICT** | 学期有归属记录时禁止删 |
| ScoreLog → Student | **SET NULL** | 学生删了，日志保留但 student_id 置空 |
| Group → Course | **RESTRICT** | 课程有小组时禁止删（停开用归档） |
| GroupMember → Group | 已列于上 | - |

### 4.8 Deferred FK 约束（P2 — 已移至附录 A.3）

> 学期切换一年 1-2 次，常规迁移顺序（先建新行再改标记）即可满足 FK 检查，
> 无需 DEFERRABLE 约束。需要时再按附录 A.3 改造。

---

## 五、4GB 内存专项优化（已移至附录 A.4）

> 原方案将 PostgreSQL 参数、连接池、Gunicorn、监控列为 Phase 3 的一部分。
> 经评估，这些属于**部署运维主题**，与数据模型重构无耦合：
> - PG 参数（shared_buffers=512MB 等）建议部署时直接参考附录 A.4 配置，不依赖重构阶段
> - 连接池收紧、pg_stat_statements 监控对 4GB 机器有实际价值，可随时独立实施
>
> 完整内容见附录 A.4。

---

## 六、分步落地计划

### Phase 1：基础实体表 + 索引（1-2 天）

| 步骤 | 操作 | 风险 |
|------|------|------|
| 1 | Alembic 迁移：创建 `semesters` 表，从 `.env` 初始化当前学期记录 | 低 |
| 2 | Alembic 迁移：创建 `cohorts` 表，初始化当前届 | 低 |
| 3 | Alembic 迁移：创建 `classes` 表，从 `students.class_name` DISTINCT 推导 | 低 |
| 4 | Alembic 迁移：`students` 加 `class_id`、`cohort_year`、`status` 字段，回填数据（cohort_year 回填入学年） | 中 |
| 5 | 教师授课关系不建桥接表：`course_offerings.teacher_id` 为唯一真源，`User.assigned_classes` JSON 过渡期保留（Phase 4 删除） | - |
| 6 | ~~创建 student_semester_scores~~ 已取消：综合分废弃，个人成绩 = enrollments.score，期末成绩 = enrollments.final_score | - |
| 7 | Alembic 迁移：创建 `student_class_semesters` 表，从当前 `students.class_name` 初始化本学期归属 | 低 |
| 8 | 所有业务表加 `class_id`、`semester_id` 列，回填数据 | 中 |
| 9 | 建索引（FK 列 + 复合索引 + 部分索引） | 低 |
| 10 | `ClassGroupSettings` 加 `semester_id` 主键 | 低 |
| 11 | Alembic 迁移：`audit_logs` 加 `semester_id` 字段（管理员按学期审计） | 低 |
| 12 | Alembic 迁移：创建 `courses` 表，从 `subjects` 按 name 去重推导（补 code） | 低 |
| 13 | Alembic 迁移：创建 `course_offerings` 表，从课表 `course_name` + `teacher_id` 推导 | 中 |
| 14 | Alembic 迁移：创建 `enrollments` 表，从 `student_subject_scores` 迁移（score/version 继承，另加 final_score 字段） | 中 |
| 15 | Alembic 迁移：小组改造 `groups.subject_id` → `course_id` FK；任务/互评相关表标记废弃 | 低 |

### Phase 2：CRUD 层适配（2-3 天）

| 步骤 | 操作 |
|------|------|
| 1 | `term.py` 改为从数据库读取 + 应用层缓存 |
| 2 | `class_cache.py` 班级映射缓存 |
| 3 | 所有 CRUD 从 `class_name` 字符串过滤 → `class_id` FK 过滤 |
| 4 | 所有 CRUD 从 `semester` 字符串过滤 → `semester_id` FK 过滤 |
| 5 | 教师权限校验：从 `course_offerings` 派生（JOIN offerings），过渡期兼容 `assigned_classes` |
| 6 | ~~综合分 CRUD~~ 已取消：个人成绩 = enrollments.score（授课教师修改）；`Student.score` 过渡期只读，Phase 4 废弃 |
| 7 | 学生转班/学期归属读写 → `student_class_semesters` CRUD（同步维护 `students.class_id` / `class_name` 缓存，`cohort_year` 不更新） |
| 8 | 课表/调课/课堂 CRUD：`course_name` 字符串 → `offering_id` FK |
| 9 | `student_subject_scores` 读写 → `enrollments` CRUD（个人成绩 score + 期末成绩 final_score + 退课） |
| 10 | 小组 CRUD：`subject_id` → `course_id`；小组分教师直接加减；任务/互评接口停用（旧数据只读） |
| 11 | 保留旧字段做双写过渡期 |

### Phase 3：性能优化（1-2 天）

> ⚠️ **经规模评估（2000 学生 / 10 教师），本阶段整体移至附录 A，P1/P2 项当前无收益**：
> 实时排行榜已有索引 <1ms、并发冲突率≈0、学期切换一年 1-2 次。
> 唯一保留项：eager loading 防 N+1（随 Phase 2 CRUD 适配同步完成）。
> 下表保留仅为将来数据量增长时的执行参考，实施时机见附录 A 启用条件。

| 步骤 | 操作 |
|------|------|
| 1 | PG 参数调优（shared_buffers / work_mem / random_page_cost） |
| 2 | 连接池参数调整 |
| 3 | 物化视图排行榜 |
| 4 | UPSERT 幂等改造（签到、打分） |
| 5 | eager loading 防 N+1 |
| 6 | Advisory Lock 学期切换互斥 |
| 7 | pg_stat_statements 监控启用 |

### Phase 4：清理与前端适配（2-3 天）

| 步骤 | 操作 |
|------|------|
| 1 | 前端班级选择器改为按届+学期过滤 |
| 2 | 前端学期管理界面（创建/切换学期） |
| 3 | 前端届管理界面（毕业归档、留级/休学/退学状态管理） |
| 4 | 审计日志支持按学期过滤（`audit_logs.semester_id`） |
| 5 | 确认双写过渡期稳定后，删除旧字段（`Student.score`、`User.assigned_classes`、业务表 `class_name` / `semester` 字符串列）及废弃表（`subjects`、`student_subject_scores`、`student_subject_score_logs`、`group_tasks`、`group_task_dimensions`、`evaluation_assignments`、`group_evaluation_scores`） |
| 6 | 删除 `.env` 中 `TERM_CFG__*` 配置 |

---

## 七、优化优先级总览

| 优先级 | 优化项 | 层级 |
|--------|--------|------|
| **P0** | FK 列索引 + 复合索引 | 数据库 |
| **P0** | 应用层缓存（学期 + class 映射） | 应用 |
| **P0** | 防 N+1：eager loading | 应用 |
| **P0** | PG 参数调优（shared_buffers=512MB 等） | 数据库 |
| **P1** | 物化视图排行榜（4GB work_mem=8MB） | 数据库 |
| **P1** | 连接池收紧 10+5 | 应用 |
| **P1** | Gunicorn 2 worker + gevent | 部署 |
| **P1** | 业务表冗余 class_name | 数据库 |
| **P1** | 签到 FK 校验替代应用层 SELECT | 应用 |
| **P1** | 学期切换分批处理 | 应用 |
| **P2** | UPSERT 幂等操作 | 应用 |
| **P2** | Advisory Lock 互斥 | 应用 |
| **P2** | pg_stat_statements 监控 | 数据库 |
| **P2** | FK DEFERRABLE | 数据库 |
| **P3** | 分区表（数据量 >100 万行时） | 数据库 |

**实施策略**：P0 立即实施；P1/P2 已移至附录 A——当前规模（2000 学生 / 10 教师）无收益，仅在附录 A 启用条件触发时评估；P3 见附录 A.5。

### 不需要的优化

| 项目 | 原因 |
|------|------|
| 读写分离 / 主从 | 单 PG 实例完全够 |
| Redis 缓存层 | PG 物化视图 + 应用缓存已够 |
| PgBouncer | 15 连接 PG 原生处理 |
| 悲观锁 SELECT FOR UPDATE | 10 老师并发冲突率 <1% |
| SERIALIZABLE 隔离 | READ COMMITTED 够用 |
| 数据库分区 | 3 年 ~60 万行，PG 无压力 |

---

## 八、风险与兜底

| 风险 | 缓解措施 |
|------|----------|
| 迁移过程中数据不一致 | 双写过渡期：新旧字段同时写入，读新字段，确认稳定后再删旧 |
| 学期切换误操作 | Advisory Lock 互斥 + 操作前确认 + 事务可回滚 |
| 4GB 内存 OOM | `statement_timeout=10s` + `pool_size=10` + 监控 |
| FK 级联误删 | 关键关系用 RESTRICT，CASCADE 只用于强从属（课堂→签到） |
| 缓存与数据库不一致 | 缓存 TTL=60s + 关键操作后手动 invalidate |

---

## 九、代码风格规范（重构时必须遵守）

> 以下规范基于对现有后端/前端代码库的全面审查，确保重构代码与已有代码风格一致。

### 9.1 后端模型层

#### SQLModel Base+Table 继承链

```python
# ✅ 正确：现有模式
class StudentBase(SQLModel):
    student_id: str = Field(primary_key=True)
    name: str = Field(max_length=50)
    class_name: str = Field(default="未分班", max_length=100)
    is_account_enabled: bool = Field(default=True)

class Student(StudentBase, table=True):
    __tablename__ = "students"
    # 数据库专属字段在这里
    password_hash: Optional[str] = Field(default=None)

class StudentCreate(SQLModel):
    # 创建请求模型（独立定义，不继承 Base）
    student_id: str
    name: str
    class_name: str = "未分班"

class StudentUpdate(SQLModel):
    # 更新请求模型（全部 Optional）
    name: Optional[str] = None
    class_name: Optional[str] = None

class StudentResponse(StudentBase):
    # 响应模型（继承 Base，只含安全字段）
    pass
```

**新实体表必须遵循此模式：**

```python
# cohorts
class CohortBase(SQLModel):
    year: str = Field(primary_key=True, max_length=10)
    label: str = Field(default="", max_length=50)
    status: str = Field(default="active", max_length=20)

class Cohort(CohortBase, table=True):
    __tablename__ = "cohorts"
    entry_semester_id: int = Field(foreign_key="semesters.id")

class CohortResponse(CohortBase):
    entry_semester_id: int

# semesters
class SemesterBase(SQLModel):
    label: str = Field(max_length=20)
    start_date: date
    total_weeks: int
    is_current: bool = Field(default=False)
    status: str = Field(default="active", max_length=20)

class Semester(SemesterBase, table=True):
    __tablename__ = "semesters"
    id: Optional[int] = Field(default=None, primary_key=True)

class SemesterResponse(SemesterBase):
    id: int

# classes
class ClassBase(SQLModel):
    name: str = Field(max_length=100)
    cohort_year: str = Field(max_length=10)

class Class(ClassBase, table=True):
    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint('name', 'cohort_year', name='uix_class_name_cohort'),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    # display_name 由 PG GENERATED 列自动生成，不在模型中

class ClassResponse(ClassBase):
    id: int
    display_name: str  # 查询时从 PG 读取

# student_class_semesters（桥接表）
class StudentClassSemesterBase(SQLModel):
    student_id: str
    class_id: int
    semester_id: int

class StudentClassSemester(StudentClassSemesterBase, table=True):
    __tablename__ = "student_class_semesters"
    __table_args__ = (
        UniqueConstraint('student_id', 'semester_id', name='uix_student_class_semester'),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now)

# courses（课程目录）
class CourseBase(SQLModel):
    code: str = Field(max_length=20)
    name: str = Field(max_length=100)
    department: str = Field(default="", max_length=50)
    status: str = Field(default="active", max_length=20)

class Course(CourseBase, table=True):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint('code', name='uix_course_code'),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now)

class CourseResponse(CourseBase):
    id: int

# course_offerings（教学班）
class CourseOfferingBase(SQLModel):
    course_id: int
    semester_id: int
    teacher_id: Optional[int] = None
    teacher_name: str = ""
    class_scope: str
    capacity: Optional[int] = None
    status: str = "active"

class CourseOffering(CourseOfferingBase, table=True):
    __tablename__ = "course_offerings"
    __table_args__ = (
        UniqueConstraint('course_id', 'semester_id', 'teacher_id', 'class_scope',
                         name='uix_offering'),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=get_now)

class CourseOfferingResponse(CourseOfferingBase):
    id: int

# enrollments（选课 — 吸收 student_subject_scores，成绩 + 乐观锁）
class EnrollmentBase(SQLModel):
    student_id: str
    offering_id: int
    semester_id: int
    status: str = "enrolled"
    score: float = 0.0
    final_score: Optional[float] = None

class Enrollment(EnrollmentBase, table=True):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint('student_id', 'offering_id', name='uix_enrollment'),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=get_now)
    updated_at: datetime = Field(default_factory=get_now)

class EnrollmentResponse(EnrollmentBase):
    id: int
    version: int
```

#### 禁止使用 SQLModel Relationship

```python
# ❌ 禁止：现有代码库从不使用 Relationship
class Student(StudentBase, table=True):
    class_: Class = Relationship()  # 不用

# ✅ 正确：全部通过 FK + 手动 JOIN/select
# CRUD 层用 session.exec(select(Student, Class).join(Class, ...))
```

#### get_current_term() 作为 default_factory

```python
# ✅ 正确：现有模式
class Group(GroupBase, table=True):
    semester: str = Field(default_factory=get_current_term)

# ✅ 重构后保持兼容
class CheckinRecord(CheckinRecordBase, table=True):
    semester_id: int = Field(default_factory=get_current_semester_id_cached)
```

#### 乐观锁模式

```python
# ✅ 正确：现有模式 — raw SQL + version 字段
def update_student_score(session: Session, student_id: str, delta: float) -> Student:
    result = session.execute(
        text("""
            UPDATE students
            SET score = score + :delta, version = version + 1
            WHERE student_id = :sid AND version = :ver
            RETURNING *
        """),
        {"delta": delta, "sid": student_id, "ver": current_version}
    )
    if not result.fetchone():
        raise HTTPException(409, "数据已被修改，请刷新重试")
    session.commit()

# ✅ 重构后 enrollments（个人成绩/期末成绩）与 groups（小组分）同样用此模式
def update_enrollment_score(session, enrollment_id, delta, version):
    result = session.execute(
        text("""
            UPDATE enrollments
            SET score = score + :delta, version = version + 1
            WHERE id = :eid AND version = :ver
            RETURNING *
        """),
        {"delta": delta, "eid": enrollment_id, "ver": version}
    )
    if not result.fetchone():
        raise HTTPException(409, "数据已被修改，请刷新重试")
    session.commit()
```

#### 事件总线 after_commit 模式

```python
# ✅ 正确：现有模式 — 重构后事件载荷改为 enrollment（个人成绩/期末成绩）
def update_enrollment_score(session, enrollment_id, delta):
    enrollment = ...
    session.commit()
    # 事务提交后才发事件
    event_bus.emit_after_commit(
        ScoreUpdated(enrollment_id=enrollment_id, new_score=enrollment.score)
    )
```

### 9.2 后端 API 路由层

#### ApiResponse[T] + ApiResponseConst 响应格式

```python
# ✅ 正确：现有模式 — 所有 API 统一返回格式
from app.models.constants import ApiResponse, ApiResponseConst

# 列表接口
class StudentListResponse(ApiResponse[list[StudentWithCheckin]]):
    pass

@router.get("/students", response_model=StudentListResponse)
def list_students(...):
    students = ...
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: students,
        ApiResponseConst.MESSAGE: "获取成功",
    }

# 分页接口 — 额外返回 total
class StudentPaginatedResponse(ApiResponse[list[StudentWithCheckin]]):
    total: int = 0

@router.get("/students/paginated", response_model=StudentPaginatedResponse)
def list_students_paginated(...):
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: students,
        "total": total_count,
        ApiResponseConst.MESSAGE: "获取成功",
    }
```

**新增实体 API 必须遵循：**

```python
# 学期管理 API
class SemesterListResponse(ApiResponse[list[SemesterResponse]]):
    pass

class SemesterCreateRequest(SQLModel):
    label: str
    start_date: date
    total_weeks: int

@router.post("/semesters", response_model=ApiResponse[SemesterResponse])
def create_semester(req: SemesterCreateRequest, ...):
    sem = ...
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: sem,
        ApiResponseConst.MESSAGE: "学期创建成功",
    }
```

#### 内联请求模型

```python
# ✅ 正确：请求模型直接定义在路由文件中（不单独建文件）
# backend/app/api/routes/students.py
class CreateStudentRequest(BaseModel):
    student_id: str
    name: str
    class_name: str = "未分班"

class UpdateScoreRequest(BaseModel):
    delta: float
    reason: Optional[str] = None
```

#### 白名单字典构造（防泄漏）

```python
# ✅ 正确：只包含安全字段，绝不直接 dict(model)
@router.get("/students/{student_id}")
def get_student(student_id: str, ...):
    student = crud.get_student(session, student_id)
    return {
        ApiResponseConst.SUCCESS: True,
        ApiResponseConst.DATA: {
            "student_id": student.student_id,
            "name": student.name,
            "class_name": student.class_name,
            "score": student.score,
            "is_account_enabled": student.is_account_enabled,
            # 注意：绝不包含 password_hash
        },
    }
```

### 9.3 后端 CRUD 层

#### 纯数据层原则

```python
# ✅ 正确：CRUD 只做数据操作，权限检查在 API 层
# ❌ 禁止：CRUD 层抛 HTTPException
def get_student(session: Session, student_id: str) -> Optional[Student]:
    return session.get(Student, student_id)

# ✅ 权限检查在路由层
@router.get("/students/{student_id}")
def get_student(student_id: str, user=Depends(require_teacher)):
    verify_teacher_class_access(user, class_name)
    student = crud.get_student(session, student_id)
    ...
```

#### get_current_term() 过滤

```python
# ✅ 正确：现有模式 — 所有学期相关查询用 get_current_term()
def get_groups_by_class(session, class_name: str):
    return session.exec(
        select(Group).where(
            Group.class_name == class_name,
            Group.semester == get_current_term()
        )
    ).all()

# ✅ 重构后 — 用 semester_id 替代
def get_groups_by_class(session, class_id: int, semester_id: int):
    return session.exec(
        select(Group).where(
            Group.class_id == class_id,
            Group.semester_id == semester_id
        )
    ).all()
```

### 9.4 前端 API 层

#### ofetch + request<T> / requestRaw<T>

```typescript
// ✅ 正确：现有模式
import { request, requestRaw } from '@/lib/api'

// 普通请求 — 自动提取 ApiResponse.data
const students = await request<Student[]>('/api/students')

// 分页请求 — 保留 total
const { data, total } = await requestRaw<Student[]>('/api/students/paginated')

// ❌ 禁止：不使用 axios
// import axios from 'axios'  // 不用
```

**新增实体 API 必须遵循：**

```typescript
// frontend-v3/src/api/semesters.ts
import { request } from '@/lib/api'
import type { Semester } from '@/types/api'

export const semesterApi = {
  getAll: () => request<Semester[]>('/api/semesters'),
  getCurrent: () => request<Semester>('/api/semesters/current'),
  create: (data: CreateSemesterRequest) => request<Semester>('/api/semesters', { method: 'POST', body: data }),
  switchCurrent: (id: number) => request<Semester>(`/api/semesters/${id}/activate`, { method: 'PUT' }),
}
```

#### TypeScript 类型定义

```typescript
// ✅ 正确：现有模式 — class_name 是 string，不是 class_id
// frontend-v3/src/types/api.ts
export interface Student {
  student_id: string
  name: string
  class_name: string        // string，不是 number
  score: number
  is_account_enabled: boolean
}

// ✅ 重构后 — 双写过渡期同时保留 class_name 和 class_id
export interface Student {
  student_id: string
  name: string
  class_id: number          // 新增
  class_name: string        // 保留（冗余字段）
  cohort_year: string       // 新增
  score: number
  is_account_enabled: boolean
}
```

#### class_name 在 API 契约中的过渡策略

```
阶段1（双写期）：前端继续传 class_name，后端同时写入 class_id + class_name
阶段2（稳定期）：前端可选传 class_id 或 class_name，后端优先用 class_id
阶段3（清理期）：前端全面改用 class_id，删除旧 class_name 参数
```

### 9.5 前端 TanStack Query 规范

#### queryKey 命名约定

```typescript
// ✅ 正确：现有模式
const QUERY_KEYS = {
  students: ['students'],
  paginatedStudents: (params) => ['students', 'paginated', params],
  classStudents: (className) => ['class-students', className],
  courseSessions: ['courseSessions'],
  activeClassSessions: ['active-class-sessions'],
  term: ['term', 'current'],
  teacherGroups: (className) => ['teacher-groups', className],
  studentGroups: (className) => ['student-groups', className],
  groupLeaderboard: (className, subjectId?) => ['group-leaderboard', className, subjectId],
}

// ✅ 新增实体的 queryKey
const QUERY_KEYS_NEW = {
  semesters: ['semesters'],
  currentSemester: ['semester', 'current'],
  cohorts: ['cohorts'],
  classByCohort: (cohortYear) => ['classes', cohortYear],
  enrollmentScores: (offeringId) => ['enrollment-scores', offeringId],
  finalScores: (offeringId) => ['final-scores', offeringId],
  groupScores: (courseId, classId) => ['group-scores', courseId, classId],
  studentClassSemesters: (semesterId) => ['student-class-semesters', semesterId],
}
```

#### 乐观更新模式

```typescript
// ✅ 正确：现有模式 — onMutate/onError/onSettled 三步曲
const useUpdateStudentScore = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (params) => studentApi.updateScore(params),
    onMutate: async (params) => {
      // 1. 取消进行中的查询（防止覆盖乐观更新）
      await queryClient.cancelQueries({ queryKey: ['students'] })
      // 2. 保存快照
      const previous = queryClient.getQueryData(['students'])
      // 3. 乐观更新缓存
      queryClient.setQueryData(['students'], (old) =>
        old?.map(s => s.student_id === params.student_id
          ? { ...s, score: s.score + params.delta }
          : s
        )
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      // 回滚
      if (context?.previous) {
        queryClient.setQueryData(['students'], context.previous)
      }
    },
    onSettled: () => {
      // 最终刷新
      queryClient.invalidateQueries({ queryKey: ['students'] })
    },
  })
}

// ✅ 重构后 — enrollments（个人成绩/期末成绩）同样适用此模式
// queryKey 改为 ['enrollment-scores', offeringId]
```

#### invalidateQueries 联动

```typescript
// ✅ 正确：现有模式 — 一个写操作触发多个缓存刷新
onSettled: () => {
  queryClient.invalidateQueries({ queryKey: ['students'] })
  queryClient.invalidateQueries({ queryKey: ['semester-scores', semesterId] })
  queryClient.invalidateQueries({ queryKey: ['group-leaderboard'] })
}
```

### 9.6 Alembic 迁移规范

#### 命名与数据回填

```python
# ✅ 正确：现有模式
# 文件名格式：YYYYMMDDHHMMSS_descriptive_name.py
# 例：20260904161715_add_semester_fields.py

# ✅ 数据回填必须写在 upgrade() 中
def upgrade():
    # 1. 加列
    op.add_column('checkin_records', sa.Column('semester_id', sa.Integer(), nullable=True))

    # 2. 回填数据
    op.execute("""
        UPDATE checkin_records
        SET semester_id = (SELECT id FROM semesters WHERE is_current = TRUE LIMIT 1)
        WHERE semester_id IS NULL
    """)

    # 3. 改为 NOT NULL + 建 FK
    op.alter_column('checkin_records', 'semester_id', nullable=False)
    op.create_foreign_key('fk_checkin_semester_id', 'checkin_records', 'semesters', ['semester_id'], ['id'])

    # 4. 建索引
    op.create_index('idx_checkin_semester_id', 'checkin_records', ['semester_id'])
```

### 9.7 权限层适配

```python
# ✅ 正确：现有模式 — verify_teacher_class_access 检查 assigned_classes
async def verify_teacher_class_access(user: dict, class_name: str):
    if user.get("is_admin"):
        return
    assigned = user.get("class_name", [])
    if class_name not in assigned:
        raise HTTPException(403, "无权操作此班级")

# ✅ 重构后 — 教师授课关系从 course_offerings 派生（不建 teacher_class_semesters 表）
async def verify_teacher_offering_access(
    session: Session,
    user_id: int,
    offering_id: int,
    semester_id: int
):
    if user.get("is_admin"):
        return
    offering = session.exec(
        select(CourseOffering).where(
            CourseOffering.teacher_id == user_id,
            CourseOffering.id == offering_id,
            CourseOffering.semester_id == semester_id,
        )
    ).first()
    if not offering:
        raise HTTPException(403, "无权操作此教学班")

# ✅ 双写过渡期 — 两种方式并存
async def verify_teacher_class_access_compat(
    session: Session,
    user: dict,
    class_name: str,
    class_id: Optional[int] = None,
    semester_id: Optional[int] = None,
):
    if user.get("is_admin"):
        return
    if class_id and semester_id:
        # 新路径
        ...
    else:
        # 旧路径（兼容）
        assigned = user.get("class_name", [])
        if class_name not in assigned:
            raise HTTPException(403, "无权操作此班级")

#### 管理员场景（无班级范围约束，但需要学期维度）

- 管理员 `is_admin` 全局放行，不校验班级归属
- 新增管理场景：审计按学期过滤（Phase 4 步骤 4）
- 管理端接口一律显式传入 `semester_id`（默认当前学期），不做隐式学期上下文
```

---

## 十、双写过渡期时间线

```
        Phase 1              Phase 2              Phase 3              Phase 4
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │ 新表创建      │ →  │ CRUD 双写     │ →  │ 前端适配      │ →  │ 清理旧字段    │
   │ 旧字段保留    │    │ 读新写旧+新   │    │ 渐进切换      │    │ 删旧列/旧代码 │
   │ 数据回填      │    │ 验证一致性    │    │ 新UI上线      │    │ 删 .env 配置  │
   └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
         ↓                    ↓                    ↓                    ↓
   DB: 新旧并存          API: 兼容两种格式     FE: class_id 可选    DB: 只留新结构
   后端: 无行为变更       前端: 无感知变更      queryKey 扩展        API: 删旧参数
```

### 各阶段检查清单

| 阶段 | 完成标准 | 回滚方案 |
|------|----------|----------|
| Phase 1 | 所有新表+索引已创建；旧字段仍可用；数据回填验证通过 | DROP 新表即可 |
| Phase 2 | 双写一致性验证通过（新旧字段值一致率 100%）；所有 CRUD 已适配 | 关闭双写，读旧字段 |
| Phase 3 | 前端全面使用 class_id/semester_id；新 UI（学期/届管理）可用 | 前端切回 class_name |
| Phase 4 | 旧字段已删除；.env TermSettings 已移除；代码无冗余 | Alembic downgrade |

---

## 附录 A：扩展优化（按需启用）

> ⚠️ 本附录收纳原方案第三、四、五节中的 P1/P2/P3 项。
> 按当前规模评估（2000 学生 / 10 教师 / 4GB 内存）：
> - 实时排行榜 `ORDER BY` 2000 行已有索引，<1ms
> - 10 教师并发冲突率 ≈ 0
> - 学期切换一年 1-2 次
>
> **这些优化当前不需要实施**。仅在满足任一启用条件时再评估：
> - 学生数 > 10,000 或业务表行数 > 100 万
> - 并发教师/管理员 > 50
> - 单查询平均耗时 > 100ms（用 A.4 的 pg_stat_statements 佐证）

### A.1 物化视图排行榜（原 4.4，P1）

```sql
-- 预计算排行榜（4 榜中的个人成绩榜，按教学班分区），避免实时 JOIN + ORDER BY
-- ⚠️ SELECT 列表必须包含分区/索引依赖的全部列
CREATE MATERIALIZED VIEW mv_offering_score_ranking AS
SELECT
    e.offering_id,
    e.semester_id,
    e.student_id,
    s.name,
    s.class_name,
    e.score,
    e.final_score,
    RANK() OVER (PARTITION BY e.offering_id ORDER BY e.score DESC) AS rank_score,
    RANK() OVER (PARTITION BY e.offering_id ORDER BY e.final_score DESC) AS rank_final
FROM enrollments e
JOIN students s ON s.student_id = e.student_id;

CREATE UNIQUE INDEX idx_mv_ranking_pk
    ON mv_offering_score_ranking(offering_id, student_id);
CREATE INDEX idx_mv_ranking_score
    ON mv_offering_score_ranking(offering_id, rank_score);

-- 打分后刷新（CONCURRENTLY 不锁读）
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_offering_score_ranking;
```

### A.2 UPSERT 幂等操作（原 4.5，P2）

```python
from sqlalchemy.dialects.postgresql import insert

# 签到：重复提交不报错，更新时间
stmt = insert(CheckinRecord).values(**record_data)
stmt = stmt.on_conflict_do_update(
    index_elements=['session_id', 'student_id'],
    set_={
        'checkin_time': stmt.excluded.checkin_time,
        'checkin_type': stmt.excluded.checkin_type,
    }
)
session.execute(stmt)
session.commit()
```

### A.3 Deferred FK 约束（原 4.8，P2）

```sql
-- 学期切换大事务安全：FK 检查延迟到 COMMIT 时
ALTER TABLE checkin_records
    DROP CONSTRAINT checkin_records_semester_id_fkey,
    ADD CONSTRAINT checkin_records_semester_id_fkey
        FOREIGN KEY (semester_id) REFERENCES semesters(id)
        DEFERRABLE INITIALLY IMMEDIATE;

-- 批量操作时临时延迟
-- SET CONSTRAINTS ALL DEFERRED;
```

### A.4 4GB 内存专项（原第五节，部署运维主题）

**与数据模型重构无耦合，可随时独立实施。** PG 参数建议部署时直接配置。

#### PostgreSQL 参数

```ini
# postgresql.conf — 4GB 机器专用

# 内存
shared_buffers = 512MB
effective_cache_size = 1536MB
work_mem = 8MB
maintenance_work_mem = 128MB
wal_buffers = 16MB

# 并发
max_connections = 80
max_worker_processes = 2

# WAL
checkpoint_completion_target = 0.9
min_wal_size = 256MB
max_wal_size = 1GB

# 查询规划（SSD/NVMe 必改）
random_page_cost = 1.1
effective_io_concurrency = 200

# 自动清理
autovacuum = on
autovacuum_max_workers = 2
autovacuum_naptime = 1min

# 监控
log_min_duration_statement = 100    # >100ms 的查询记录
log_lock_waits = on
deadlock_timeout = 1000
```

#### 连接池

```python
# db.py — 4GB 机器专用
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,               # 10 常驻
    max_overflow=5,             # 最多 15 连接
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=settings.app.debug,
    connect_args={
        "application_name": "classhub",
        "options": "-c statement_timeout=10000",  # 10s 超时
    }
)
```

#### Gunicorn

```bash
gunicorn app.main:app \
    --workers 2 \               # 2 进程（4GB 机器不要开多）
    --worker-class gevent \     # 协程高并发
    --worker-connections 200 \
    --timeout 30
```

#### 监控（pg_stat_statements）

```sql
-- 启用 pg_stat_statements
shared_preload_libraries = 'pg_stat_statements'
CREATE EXTENSION pg_stat_statements;

-- 找最慢的查询
SELECT calls, round(mean_exec_time::numeric, 2) AS avg_ms,
       round(max_exec_time::numeric, 2) AS max_ms, query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

### A.5 分区表（P3）

仅当业务表行数 > 100 万时考虑（3 年 ~60 万行，PG 无压力）。
按 `semester_id` LIST 分区：每个学期一个分区，归档/删除学期即 DROP PARTITION。
